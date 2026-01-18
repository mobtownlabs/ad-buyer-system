"""Unified client for IAB agentic-direct server supporting both MCP and A2A protocols."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union

from .a2a_client import A2AClient, A2AResponse
from .mcp_client import IABMCPClient, MCPToolResult


class Protocol(Enum):
    """Protocol to use for communication with IAB server."""

    MCP = "mcp"  # Direct tool calls via MCP SDK
    A2A = "a2a"  # Natural language via A2A (AI interprets requests)


@dataclass
class UnifiedResult:
    """Unified result from either MCP or A2A client."""

    success: bool = True
    data: Any = None
    error: str = ""
    protocol: Protocol = Protocol.MCP
    raw: Any = None

    @classmethod
    def from_mcp(cls, result: MCPToolResult) -> "UnifiedResult":
        """Create from MCP result."""
        return cls(
            success=result.success,
            data=result.data,
            error=result.error,
            protocol=Protocol.MCP,
            raw=result.raw,
        )

    @classmethod
    def from_a2a(cls, response: A2AResponse) -> "UnifiedResult":
        """Create from A2A response."""
        # A2A returns data in response.data list
        data = response.data[0] if len(response.data) == 1 else response.data
        if not data and response.text:
            data = response.text
        return cls(
            success=response.success,
            data=data,
            error=response.error,
            protocol=Protocol.A2A,
            raw=response.raw,
        )


class UnifiedClient:
    """Unified client that supports both MCP and A2A protocols.

    Use MCP for direct tool control (faster, deterministic).
    Use A2A for natural language requests (more flexible, AI-interpreted).

    Example:
        # MCP mode (default) - direct tool calls
        async with UnifiedClient(protocol=Protocol.MCP) as client:
            result = await client.list_products()

        # A2A mode - natural language
        async with UnifiedClient(protocol=Protocol.A2A) as client:
            result = await client.list_products()

        # Switch protocols on the fly
        async with UnifiedClient(protocol=Protocol.MCP) as client:
            # Use MCP for listing
            products = await client.list_products()

            # Switch to A2A for a complex natural language request
            result = await client.send_natural_language(
                "Find me CTV inventory with household targeting under $30 CPM"
            )
    """

    def __init__(
        self,
        base_url: str = "https://agentic-direct-server-hwgrypmndq-uk.a.run.app",
        protocol: Protocol = Protocol.MCP,
        a2a_agent_type: str = "buyer",
    ):
        """Initialize the unified client.

        Args:
            base_url: Base URL for the IAB server
            protocol: Default protocol to use (MCP or A2A)
            a2a_agent_type: Agent type for A2A ('buyer' or 'seller')
        """
        self.base_url = base_url
        self.default_protocol = protocol
        self.a2a_agent_type = a2a_agent_type

        self._mcp_client: Optional[IABMCPClient] = None
        self._a2a_client: Optional[A2AClient] = None

    async def connect(self, protocol: Protocol = None) -> None:
        """Connect to the server with specified protocol.

        Args:
            protocol: Protocol to connect with (uses default if not specified)
        """
        protocol = protocol or self.default_protocol

        if protocol == Protocol.MCP:
            if not self._mcp_client:
                self._mcp_client = IABMCPClient(base_url=self.base_url)
                await self._mcp_client.connect()
        else:
            if not self._a2a_client:
                self._a2a_client = A2AClient(
                    base_url=self.base_url,
                    agent_type=self.a2a_agent_type,
                )
                # A2A doesn't need explicit connect

    async def connect_both(self) -> None:
        """Connect to both MCP and A2A protocols."""
        await self.connect(Protocol.MCP)
        await self.connect(Protocol.A2A)

    async def close(self) -> None:
        """Close all connections."""
        if self._mcp_client:
            await self._mcp_client.close()
            self._mcp_client = None
        if self._a2a_client:
            await self._a2a_client.close()
            self._a2a_client = None

    async def __aenter__(self) -> "UnifiedClient":
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    @property
    def mcp(self) -> Optional[IABMCPClient]:
        """Get the MCP client (if connected)."""
        return self._mcp_client

    @property
    def a2a(self) -> Optional[A2AClient]:
        """Get the A2A client (if connected)."""
        return self._a2a_client

    @property
    def tools(self) -> dict[str, dict]:
        """Get available MCP tools (requires MCP connection)."""
        if self._mcp_client:
            return self._mcp_client.tools
        return {}

    async def _ensure_protocol(self, protocol: Protocol) -> None:
        """Ensure the specified protocol is connected."""
        if protocol == Protocol.MCP and not self._mcp_client:
            await self.connect(Protocol.MCP)
        elif protocol == Protocol.A2A and not self._a2a_client:
            await self.connect(Protocol.A2A)

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] = None,
        protocol: Protocol = None,
    ) -> UnifiedResult:
        """Call a tool using the specified protocol.

        Args:
            name: Tool name
            arguments: Tool arguments
            protocol: Protocol to use (default if not specified)

        Returns:
            UnifiedResult with the response
        """
        protocol = protocol or self.default_protocol
        await self._ensure_protocol(protocol)

        if protocol == Protocol.MCP:
            result = await self._mcp_client.call_tool(name, arguments)
            return UnifiedResult.from_mcp(result)
        else:
            # For A2A, construct a natural language request from tool name and args
            message = self._tool_to_natural_language(name, arguments or {})
            response = await self._a2a_client.send_message(message)
            return UnifiedResult.from_a2a(response)

    def _tool_to_natural_language(self, tool_name: str, args: dict) -> str:
        """Convert a tool call to natural language for A2A."""
        # Map common tools to natural language
        tool_mappings = {
            "list_products": "List all available advertising products",
            "list_accounts": "List all accounts",
            "list_orders": "List all orders",
            "list_lines": "List all line items",
            "list_creatives": "List all creatives",
        }

        if tool_name in tool_mappings and not args:
            return tool_mappings[tool_name]

        # For other tools, construct a message
        if tool_name == "create_account":
            return f"Create an account named '{args.get('name')}' of type {args.get('type', 'advertiser')}"
        elif tool_name == "create_order":
            return (
                f"Create an order named '{args.get('name')}' "
                f"for account {args.get('accountId')} "
                f"with budget ${args.get('budget', 0):,.2f}"
            )
        elif tool_name == "create_line":
            return (
                f"Create a line item named '{args.get('name')}' "
                f"for order {args.get('orderId')} "
                f"using product {args.get('productId')} "
                f"with {args.get('quantity', 0):,} impressions"
            )
        elif tool_name == "get_product":
            return f"Get product with ID {args.get('id')}"
        elif tool_name == "get_account":
            return f"Get account with ID {args.get('id')}"
        elif tool_name == "get_order":
            return f"Get order with ID {args.get('id')}"

        # Generic fallback
        args_str = ", ".join(f"{k}={v}" for k, v in args.items())
        return f"Execute {tool_name} with {args_str}" if args_str else f"Execute {tool_name}"

    async def send_natural_language(self, message: str) -> UnifiedResult:
        """Send a natural language request via A2A.

        This always uses A2A regardless of default protocol.

        Args:
            message: Natural language request

        Returns:
            UnifiedResult with the response
        """
        await self._ensure_protocol(Protocol.A2A)
        response = await self._a2a_client.send_message(message)
        return UnifiedResult.from_a2a(response)

    # Convenience methods that use the default protocol

    async def list_products(self, protocol: Protocol = None) -> UnifiedResult:
        """List available advertising products."""
        return await self.call_tool("list_products", protocol=protocol)

    async def get_product(self, product_id: str, protocol: Protocol = None) -> UnifiedResult:
        """Get a specific product by ID."""
        return await self.call_tool("get_product", {"id": product_id}, protocol=protocol)

    async def search_products(
        self,
        query: str = None,
        filters: dict = None,
        protocol: Protocol = None,
    ) -> UnifiedResult:
        """Search for products."""
        args = {}
        if query:
            args["query"] = query
        if filters:
            args["filters"] = filters
        return await self.call_tool("search_products", args, protocol=protocol)

    async def list_accounts(self, protocol: Protocol = None) -> UnifiedResult:
        """List all accounts."""
        return await self.call_tool("list_accounts", protocol=protocol)

    async def create_account(
        self,
        name: str,
        account_type: str = "advertiser",
        status: str = "active",
        protocol: Protocol = None,
    ) -> UnifiedResult:
        """Create a new account."""
        return await self.call_tool(
            "create_account",
            {"name": name, "type": account_type, "status": status},
            protocol=protocol,
        )

    async def get_account(self, account_id: str, protocol: Protocol = None) -> UnifiedResult:
        """Get an account by ID."""
        return await self.call_tool("get_account", {"id": account_id}, protocol=protocol)

    async def list_orders(self, account_id: str = None, protocol: Protocol = None) -> UnifiedResult:
        """List orders."""
        args = {"accountId": account_id} if account_id else {}
        return await self.call_tool("list_orders", args, protocol=protocol)

    async def create_order(
        self,
        account_id: str,
        name: str,
        budget: float,
        start_date: str = None,
        end_date: str = None,
        protocol: Protocol = None,
    ) -> UnifiedResult:
        """Create a new order."""
        args = {"accountId": account_id, "name": name, "budget": budget}
        if start_date:
            args["startDate"] = start_date
        if end_date:
            args["endDate"] = end_date
        return await self.call_tool("create_order", args, protocol=protocol)

    async def get_order(self, order_id: str, protocol: Protocol = None) -> UnifiedResult:
        """Get an order by ID."""
        return await self.call_tool("get_order", {"id": order_id}, protocol=protocol)

    async def list_lines(self, order_id: str = None, protocol: Protocol = None) -> UnifiedResult:
        """List line items."""
        args = {"orderId": order_id} if order_id else {}
        return await self.call_tool("list_lines", args, protocol=protocol)

    async def create_line(
        self,
        order_id: str,
        product_id: str,
        name: str,
        quantity: int,
        start_date: str = None,
        end_date: str = None,
        protocol: Protocol = None,
    ) -> UnifiedResult:
        """Create a new line item."""
        args = {
            "orderId": order_id,
            "productId": product_id,
            "name": name,
            "quantity": quantity,
        }
        if start_date:
            args["startDate"] = start_date
        if end_date:
            args["endDate"] = end_date
        return await self.call_tool("create_line", args, protocol=protocol)

    async def get_line(self, line_id: str, protocol: Protocol = None) -> UnifiedResult:
        """Get a line item by ID."""
        return await self.call_tool("get_line", {"id": line_id}, protocol=protocol)

    async def list_creatives(self, protocol: Protocol = None) -> UnifiedResult:
        """List all creatives."""
        return await self.call_tool("list_creatives", protocol=protocol)

    async def create_creative(
        self,
        name: str,
        creative_type: str,
        url: str = None,
        content: str = None,
        protocol: Protocol = None,
    ) -> UnifiedResult:
        """Create a new creative."""
        args = {"name": name, "type": creative_type}
        if url:
            args["url"] = url
        if content:
            args["content"] = content
        return await self.call_tool("create_creative", args, protocol=protocol)

    async def create_assignment(
        self,
        line_id: str,
        creative_id: str,
        protocol: Protocol = None,
    ) -> UnifiedResult:
        """Assign a creative to a line item."""
        return await self.call_tool(
            "create_assignment",
            {"lineId": line_id, "creativeId": creative_id},
            protocol=protocol,
        )
