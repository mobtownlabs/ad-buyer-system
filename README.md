# Ad Buyer System

CrewAI-based advertising buyer agent using IAB OpenDirect 2.1 standards and the IAB Tech Lab's agentic-direct server.

## Features

- **Dual Protocol Support**: MCP (direct tool calls) and A2A (natural language) protocols
- **Hierarchical Agent Architecture**: Portfolio Manager coordinates Channel Specialists
- **Claude Models**: Opus 4 for strategic decisions, Sonnet 4.5 for execution
- **IAB OpenDirect Integration**: Full API support for booking deals and PMPs
- **Multiple Interfaces**: CLI, REST API, and conversational chat

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Ad Buyer System                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Portfolio Manager (Claude Opus)              │   │
│  │         Budget allocation, strategy, coordination         │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         │                                        │
│         ┌───────────────┼───────────────┬───────────────┐       │
│         ▼               ▼               ▼               ▼       │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐  │
│  │ Branding  │   │  Mobile   │   │    CTV    │   │Performance│  │
│  │  Agent    │   │App Agent  │   │   Agent   │   │   Agent   │  │
│  │ (Sonnet)  │   │ (Sonnet)  │   │ (Sonnet)  │   │ (Sonnet)  │  │
│  └─────┬─────┘   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘  │
│        │               │               │               │        │
│        └───────────────┴───────┬───────┴───────────────┘        │
│                                │                                 │
│         ┌──────────────────────┼──────────────────────┐         │
│         ▼                      ▼                      ▼         │
│  ┌───────────┐          ┌───────────┐          ┌───────────┐   │
│  │ Research  │          │ Execution │          │ Reporting │   │
│  │   Agent   │          │   Agent   │          │   Agent   │   │
│  └───────────┘          └───────────┘          └───────────┘   │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                      Unified Client                              │
│              ┌─────────────┬─────────────┐                      │
│              │     MCP     │     A2A     │                      │
│              │ (33 tools)  │  (natural   │                      │
│              │   direct    │  language)  │                      │
│              └──────┬──────┴──────┬──────┘                      │
└─────────────────────┼─────────────┼─────────────────────────────┘
                      │             │
                      ▼             ▼
        ┌─────────────────────────────────────┐
        │   IAB Tech Lab agentic-direct       │
        │         (OpenDirect 2.1)            │
        │  https://agentic-direct-server-     │
        │    hwgrypmndq-uk.a.run.app          │
        └─────────────────────────────────────┘
```

## Prerequisites

- **Python 3.11+**
- **Anthropic API key** - Required for CrewAI agents ([get one here](https://console.anthropic.com/))
- **Internet access** - The system connects to IAB Tech Lab's hosted agentic-direct server by default

> **Note**: You do **not** need to install the [IAB Tech Lab agentic-direct](https://github.com/InteractiveAdvertisingBureau/agentic-direct) server locally. This system connects to their hosted instance at `https://agentic-direct-server-hwgrypmndq-uk.a.run.app` which provides the OpenDirect 2.1 API via MCP and A2A protocols.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/mobtownlabs/ad-buyer-system.git
cd ad-buyer-system

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY
```

### Basic Usage

```bash
# CLI Commands
ad-buyer --help                    # Show available commands
ad-buyer init                      # Create campaign brief template
ad-buyer book campaign_brief.json  # Run booking workflow
ad-buyer search --channel ctv      # Search inventory
ad-buyer chat                      # Interactive chat mode

# Run API server
python -m ad_buyer.interfaces.api.main
# Server runs at http://localhost:8000
```

## Client Usage Examples

> **Runnable examples**: See the `examples/` folder for complete, runnable scripts:
> - `basic_mcp_usage.py` - MCP protocol basics
> - `natural_language_a2a.py` - A2A natural language queries
> - `protocol_switching.py` - Switching protocols on-the-fly
> - `individual_clients.py` - Using IABMCPClient and A2AClient directly

### Using the Unified Client (Recommended)

```python
import asyncio
from ad_buyer.clients import UnifiedClient, Protocol

async def main():
    # MCP mode - direct tool calls (faster, deterministic)
    async with UnifiedClient(protocol=Protocol.MCP) as client:
        # List available products
        result = await client.list_products()
        print(f"Products: {result.data}")

        # Create an account
        result = await client.create_account(name="My Advertiser")
        account_id = result.data["id"]

        # Create an order
        result = await client.create_order(
            account_id=account_id,
            name="Q1 Campaign",
            budget=50000
        )
        order_id = result.data["id"]

        # Create a line item
        result = await client.create_line(
            order_id=order_id,
            product_id="prod-123",
            name="Homepage Banner",
            quantity=1000000
        )

asyncio.run(main())
```

### Using Natural Language (A2A Protocol)

```python
import asyncio
from ad_buyer.clients import UnifiedClient, Protocol

async def main():
    async with UnifiedClient(protocol=Protocol.A2A) as client:
        # Natural language queries
        result = await client.send_natural_language(
            "Find CTV inventory with household targeting under $30 CPM"
        )
        print(f"Response: {result.data}")

asyncio.run(main())
```

### Switching Protocols On-The-Fly

```python
import asyncio
from ad_buyer.clients import UnifiedClient, Protocol

async def main():
    async with UnifiedClient(protocol=Protocol.MCP) as client:
        # Connect to both protocols
        await client.connect_both()

        # Use MCP for fast, deterministic operations
        products = await client.list_products(protocol=Protocol.MCP)

        # Use A2A for natural language queries
        recommendations = await client.send_natural_language(
            "What products would work best for a brand awareness campaign?"
        )

        # Mix in a workflow
        account = await client.create_account(
            name="Test Account",
            protocol=Protocol.MCP  # Fast, direct
        )

asyncio.run(main())
```

### Using Individual Clients

```python
# MCP Client - Direct tool access
from ad_buyer.clients import IABMCPClient

async with IABMCPClient() as client:
    result = await client.call_tool("list_products", {})
    print(client.tools)  # See all 33 available tools

# A2A Client - Natural language
from ad_buyer.clients import A2AClient

async with A2AClient() as client:
    response = await client.send_message("List available products")
    print(response.text, response.data)
```

## Available MCP Tools

The IAB server provides 33 OpenDirect tools:

| Category | Tools |
|----------|-------|
| **Accounts** | `create_account`, `update_account`, `get_account`, `list_accounts` |
| **Orders** | `create_order`, `update_order`, `get_order`, `list_orders` |
| **Lines** | `create_line`, `update_line`, `get_line`, `list_lines` |
| **Products** | `get_product`, `list_products`, `search_products` |
| **Creatives** | `create_creative`, `update_creative`, `get_creative`, `list_creatives` |
| **Assignments** | `create_assignment`, `delete_assignment`, `get_assignment`, `list_assignments` |
| **Organizations** | `create_organization`, `update_organization`, `get_organization`, `list_organizations` |
| **Change Requests** | `create_changerequest`, `get_changerequest`, `list_changerequests` |
| **Messages** | `create_message`, `get_message`, `list_messages` |

## Project Structure

```
ad_buyer_system/
├── examples/            # Runnable example scripts
│   ├── basic_mcp_usage.py
│   ├── natural_language_a2a.py
│   ├── protocol_switching.py
│   ├── individual_clients.py
│   └── campaign_brief.json
├── src/ad_buyer/
│   ├── agents/           # CrewAI agents (Portfolio Manager, Channel Specialists)
│   │   ├── level1/       # Portfolio Manager
│   │   ├── level2/       # Channel Specialists (Branding, Mobile, CTV, Performance)
│   │   └── level3/       # Operational Agents (Research, Execution, Reporting)
│   ├── clients/          # API clients
│   │   ├── unified_client.py   # Unified MCP + A2A client (recommended)
│   │   ├── mcp_client.py       # Direct MCP tool access
│   │   ├── a2a_client.py       # Natural language A2A
│   │   └── opendirect_client.py # REST client for local mock
│   ├── crews/            # CrewAI crews
│   ├── flows/            # CrewAI flows (deal booking workflow)
│   ├── interfaces/       # User interfaces
│   │   ├── api/          # FastAPI REST server
│   │   └── cli/          # Typer CLI
│   ├── models/           # Pydantic models (OpenDirect, flow state)
│   └── tools/            # CrewAI tools (research, execution, reporting)
├── tests/
│   └── unit/             # Unit tests (43 tests)
├── scripts/              # Test and utility scripts
└── campaign_brief.json   # Example campaign brief
```

## Configuration

Create a `.env` file with:

```bash
# Required
ANTHROPIC_API_KEY=your-api-key-here

# Optional - LLM Settings
DEFAULT_LLM_MODEL=anthropic/claude-sonnet-4-5-20250929
MANAGER_LLM_MODEL=anthropic/claude-opus-4-20250514
LLM_TEMPERATURE=0.3

# Optional - Local mock server (for development)
OPENDIRECT_BASE_URL=http://localhost:3000
```

## Running Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src/ad_buyer

# Test the unified client against IAB server
python scripts/test_unified_client.py

# Test MCP client
python scripts/test_mcp_e2e.py

# Test A2A client
python scripts/test_a2a_e2e.py
```

## IAB Tech Lab Integration

This project integrates with the [IAB Tech Lab agentic-direct](https://github.com/InteractiveAdvertisingBureau/agentic-direct) reference implementation:

- **Server**: `https://agentic-direct-server-hwgrypmndq-uk.a.run.app`
- **Protocol**: OpenDirect 2.1 via MCP (Model Context Protocol) and A2A (Agent-to-Agent)
- **Tools**: 33 MCP tools for full OpenDirect workflow

## Requirements

- Python 3.11+
- Anthropic API key (for CrewAI agents)
- Internet access (for IAB hosted server) or local mock server

## License

MIT
