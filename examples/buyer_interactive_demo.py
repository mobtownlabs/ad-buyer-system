#!/usr/bin/env python3
"""Buyer Agent Interactive Demo - Connects to Local Seller

This buyer agent connects to a locally running seller agent MCP server.
Run the seller first (seller_mcp_server.py), then run this buyer.

Usage:
    Terminal 1: cd ad_seller_system/examples && python seller_mcp_server.py
    Terminal 2: cd ad_buyer_system/examples && python buyer_interactive_demo.py

The buyer will:
1. Parse the Rivian R2 media brief PDF
2. Connect to the local seller agent
3. Discover available inventory
4. Get tiered pricing based on buyer identity
5. Create Deal IDs for DSP activation
6. Book OpenDirect order lines
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Rich console for beautiful output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for enhanced output: pip install rich")

# HTTP client
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("Error: Please install httpx: pip install httpx")
    sys.exit(1)

# PDF parsing
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None

# =============================================================================
# Configuration
# =============================================================================

SELLER_URL = "http://localhost:8001"  # Local seller agent

@dataclass
class BuyerIdentity:
    """Buyer identity for tiered pricing access."""
    seat_id: str = "amazon-dsp-001"
    seat_name: str = "Amazon DSP"
    agency_id: str = "agency-abc-001"
    agency_name: str = "Agency ABC"
    agency_holding_company: str = "Agency ABC Group"
    advertiser_id: str = "rivian-automotive-001"
    advertiser_name: str = "Rivian Automotive"
    advertiser_industry: str = "Automotive"

    def get_access_tier(self) -> str:
        """Get the access tier based on identity."""
        if self.advertiser_id:
            return "advertiser"
        elif self.agency_id:
            return "agency"
        elif self.seat_id:
            return "seat"
        return "public"

    def get_discount_percentage(self) -> int:
        """Get expected discount percentage."""
        discounts = {"public": 0, "seat": 5, "agency": 10, "advertiser": 15}
        return discounts.get(self.get_access_tier(), 0)


@dataclass
class CampaignBrief:
    """Parsed campaign brief from PDF."""
    campaign_name: str = "Rivian R2 Launch Campaign"
    client: str = "Rivian Automotive"
    agency: str = "Agency ABC"
    total_budget: float = 4_700_000
    start_date: str = "2026-03-01"
    end_date: str = "2026-06-30"
    ctv_budget: float = 3_500_000
    ctv_reach_target: int = 5_000_000
    ctv_frequency_target: int = 3
    performance_budget: float = 800_000
    mobile_budget: float = 400_000


# =============================================================================
# Seller Client
# =============================================================================

class LocalSellerClient:
    """Client for communicating with local seller MCP server."""

    def __init__(self, base_url: str = SELLER_URL):
        self.base_url = base_url.rstrip("/")
        # Disable proxy for local connections
        import os
        # Clear proxy env vars for local connections
        for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
            os.environ.pop(var, None)
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def call_tool(self, name: str, arguments: dict = None) -> dict:
        """Call an MCP tool on the seller."""
        try:
            response = await self.client.post(
                f"{self.base_url}/mcp/call",
                json={"name": name, "arguments": arguments or {}}
            )
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            return {"success": False, "error": "Cannot connect to seller agent. Is it running?"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_products(self, channel: str = None) -> dict:
        """List available products."""
        args = {"channel": channel} if channel else {}
        return await self.call_tool("list_products", args)

    async def get_pricing(
        self,
        product_id: str,
        buyer_tier: str = "public",
        volume: int = 0,
        deal_type: str = "preferred_deal"
    ) -> dict:
        """Get tiered pricing for a product."""
        return await self.call_tool("get_pricing", {
            "product_id": product_id,
            "buyer_tier": buyer_tier,
            "volume": volume,
            "deal_type": deal_type
        })

    async def check_availability(
        self,
        product_id: str,
        impressions: int,
        start_date: str,
        end_date: str
    ) -> dict:
        """Check inventory availability."""
        return await self.call_tool("check_availability", {
            "product_id": product_id,
            "impressions": impressions,
            "start_date": start_date,
            "end_date": end_date
        })

    async def create_deal(
        self,
        product_id: str,
        deal_type: str,
        price: float,
        impressions: int,
        start_date: str = None,
        end_date: str = None,
        buyer_id: str = None,
        advertiser_name: str = None,
        dsp_platform: str = "amazon_dsp"
    ) -> dict:
        """Create a Deal ID."""
        return await self.call_tool("create_deal", {
            "product_id": product_id,
            "deal_type": deal_type,
            "price": price,
            "impressions": impressions,
            "start_date": start_date or "2026-03-01",
            "end_date": end_date or "2026-06-30",
            "buyer_id": buyer_id,
            "advertiser_name": advertiser_name,
            "dsp_platform": dsp_platform
        })

    async def book_order(
        self,
        deal_id: str,
        order_name: str,
        buyer_id: str = None,
        billing_contact: str = None
    ) -> dict:
        """Book an OpenDirect order."""
        return await self.call_tool("book_order", {
            "deal_id": deal_id,
            "order_name": order_name,
            "buyer_id": buyer_id,
            "billing_contact": billing_contact
        })


# =============================================================================
# Display Helpers
# =============================================================================

def print_header(text: str):
    """Print a styled header."""
    if RICH_AVAILABLE:
        console.print(Panel(text, style="bold green"))
    else:
        print("\n" + "=" * 60)
        print(text)
        print("=" * 60)


def print_step(step: int, text: str):
    """Print a step indicator."""
    if RICH_AVAILABLE:
        console.print(f"\n[bold cyan]Step {step}:[/bold cyan] {text}")
    else:
        print(f"\n>>> Step {step}: {text}")


def print_success(text: str):
    """Print success message."""
    if RICH_AVAILABLE:
        console.print(f"[green]✓ {text}[/green]")
    else:
        print(f"[OK] {text}")


def print_error(text: str):
    """Print error message."""
    if RICH_AVAILABLE:
        console.print(f"[red]✗ {text}[/red]")
    else:
        print(f"[ERROR] {text}")


def print_info(text: str):
    """Print info message."""
    if RICH_AVAILABLE:
        console.print(f"[dim]{text}[/dim]")
    else:
        print(f"  {text}")


def print_json(data: dict, title: str = ""):
    """Print formatted JSON."""
    if RICH_AVAILABLE:
        if title:
            console.print(f"[dim]{title}[/dim]")
        console.print_json(json.dumps(data, indent=2, default=str))
    else:
        if title:
            print(title)
        print(json.dumps(data, indent=2, default=str))


# =============================================================================
# Presenter Controls
# =============================================================================

def wait_for_presenter(step_description: str = ""):
    """Wait for presenter to press Enter before continuing."""
    if RICH_AVAILABLE:
        if step_description:
            console.print(f"\n[dim italic]Next: {step_description}[/dim italic]")
        console.print("[bold yellow]>>> Press ENTER to continue...[/bold yellow]", end="")
    else:
        if step_description:
            print(f"\n  Next: {step_description}")
        print(">>> Press ENTER to continue...", end="")

    input()
    print()  # Add newline after Enter


# =============================================================================
# Demo Workflow
# =============================================================================

async def run_automated_demo():
    """Run the full automated demo workflow."""
    print_header("RIVIAN R2 CAMPAIGN - BUYER AGENT DEMO")
    print_info("Connecting to local seller agent...")
    print_info(f"Seller URL: {SELLER_URL}")
    print("")

    # Campaign brief
    brief = CampaignBrief()
    identity = BuyerIdentity()

    if RICH_AVAILABLE:
        console.print(Panel(
            f"Campaign: {brief.campaign_name}\n"
            f"Client: {brief.client}\n"
            f"Agency: {brief.agency}\n"
            f"Budget: ${brief.total_budget:,.2f}\n"
            f"Flight: {brief.start_date} to {brief.end_date}",
            title="[bold]Campaign Brief[/bold]",
            style="cyan"
        ))

    print_info(f"Buyer Identity: {identity.agency_name} + {identity.advertiser_name}")
    print_info(f"Access Tier: {identity.get_access_tier()}")
    print_info(f"Expected Discount: {identity.get_discount_percentage()}%")

    wait_for_presenter("Connect to seller agent")

    async with LocalSellerClient() as client:
        # Step 1: Check connection
        print_step(1, "Connecting to seller agent")

        result = await client.list_products()
        if not result.get("success", True):
            print_error(f"Failed to connect: {result.get('error')}")
            print_info("Make sure the seller agent is running:")
            print_info("  cd ad_seller_system/examples && python seller_mcp_server.py")
            return

        print_success("Connected to seller agent")

        wait_for_presenter("Discover available CTV inventory")

        # Step 2: Discover CTV inventory
        print_step(2, "Discovering CTV inventory")

        result = await client.list_products(channel="ctv")
        products = result.get("result", {}).get("products", [])

        if RICH_AVAILABLE and products:
            table = Table(title="Available CTV Inventory")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Avail (M)", style="yellow")
            table.add_column("Base CPM", style="magenta")

            for p in products:
                table.add_row(
                    p["id"],
                    p["name"][:35],
                    f"{p['available_impressions'] / 1_000_000:.0f}M",
                    f"${p['base_price']:.2f}"
                )
            console.print(table)

        print_success(f"Found {len(products)} CTV products")

        wait_for_presenter("Request tiered pricing (reveal buyer identity for discounts)")

        # Step 3: Get tiered pricing
        print_step(3, "Requesting tiered pricing (revealing buyer identity)")

        pricing_results = []
        for product in products:
            result = await client.get_pricing(
                product_id=product["id"],
                buyer_tier=identity.get_access_tier(),
                volume=brief.ctv_reach_target * brief.ctv_frequency_target,
                deal_type="preferred_deal"
            )

            if result.get("success"):
                pricing_data = result.get("result", {})
                pricing_results.append(pricing_data)

        if RICH_AVAILABLE and pricing_results:
            table = Table(title="Tiered Pricing (Advertiser Tier)")
            table.add_column("Product", style="cyan")
            table.add_column("Base CPM", style="yellow")
            table.add_column("Tier", style="green")
            table.add_column("Discount", style="magenta")
            table.add_column("Final CPM", style="bold green")

            for p in pricing_results:
                pricing = p.get("pricing", {})
                table.add_row(
                    p.get("product_name", "Unknown")[:30],
                    f"${pricing.get('base_price', 0):.2f}",
                    pricing.get("tier", "public"),
                    f"{pricing.get('total_discount', 0):.0f}%",
                    f"${pricing.get('final_price', 0):.2f}"
                )
            console.print(table)

        print_success("Received tiered pricing with advertiser discounts")

        wait_for_presenter("Create Deal IDs for DSP activation")

        # Step 4: Create Deal IDs
        print_step(4, "Creating Deal IDs for DSP activation")

        deals_created = []
        target_impressions = brief.ctv_reach_target * brief.ctv_frequency_target

        for pricing in pricing_results[:2]:  # Create deals for top 2 products
            result = await client.create_deal(
                product_id=pricing.get("product_id"),
                deal_type="preferred_deal",
                price=pricing.get("pricing", {}).get("final_price", 20.0),
                impressions=target_impressions // 2,
                start_date=brief.start_date,
                end_date=brief.end_date,
                buyer_id=identity.seat_id,
                advertiser_name=identity.advertiser_name,
                dsp_platform="amazon_dsp"
            )

            if result.get("success"):
                deal = result.get("result", {})
                deals_created.append(deal)
                print_success(f"Created Deal: {deal.get('deal_id')} at ${deal.get('price'):.2f} CPM")

        if RICH_AVAILABLE and deals_created:
            for deal in deals_created:
                activation = deal.get("activation", {})
                console.print(Panel(
                    f"Deal ID: [bold cyan]{deal.get('deal_id')}[/bold cyan]\n"
                    f"Product: {deal.get('product_name')}\n"
                    f"Price: ${deal.get('price'):.2f} CPM\n"
                    f"Impressions: {deal.get('impressions'):,}\n"
                    f"\n[bold]DSP Activation ({activation.get('platform', 'Amazon DSP')}):[/bold]\n" +
                    "\n".join(activation.get("steps", [])),
                    title="[bold green]Deal Created[/bold green]",
                    style="green"
                ))

        wait_for_presenter("Book OpenDirect order lines")

        # Step 5: Book OpenDirect orders
        print_step(5, "Booking OpenDirect order lines")

        orders_booked = []
        for i, deal in enumerate(deals_created):
            result = await client.book_order(
                deal_id=deal.get("deal_id"),
                order_name=f"Rivian R2 CTV Campaign - Line {i+1}",
                buyer_id=identity.seat_id,
                billing_contact="billing@agencyabc.com"
            )

            if result.get("success"):
                order = result.get("result", {})
                orders_booked.append(order)
                print_success(f"Booked Order: {order.get('order_id')} for {deal.get('deal_id')}")

        wait_for_presenter("View campaign summary")

        # Summary
        print_header("CAMPAIGN BOOKING SUMMARY")

        if RICH_AVAILABLE:
            total_impressions = sum(d.get("impressions", 0) for d in deals_created)
            total_cost = sum(
                d.get("price", 0) * d.get("impressions", 0) / 1000
                for d in deals_created
            )

            console.print(Panel(
                f"Campaign: {brief.campaign_name}\n"
                f"Advertiser: {identity.advertiser_name}\n"
                f"Agency: {identity.agency_name}\n"
                f"\n[bold]Deals Created:[/bold] {len(deals_created)}\n"
                f"[bold]Orders Booked:[/bold] {len(orders_booked)}\n"
                f"\n[bold]Total Impressions:[/bold] {total_impressions:,}\n"
                f"[bold]Estimated Cost:[/bold] ${total_cost:,.2f}\n"
                f"\n[bold]Deal IDs for DSP:[/bold]\n" +
                "\n".join(f"  • {d.get('deal_id')}" for d in deals_created),
                title="[bold green]Booking Complete[/bold green]",
                style="green"
            ))

        print_success("Demo complete! Both agents communicated successfully.")


async def run_interactive_mode():
    """Run in interactive mode - user can type commands."""
    print_header("BUYER AGENT - INTERACTIVE MODE")
    print_info("Connecting to local seller agent...")

    identity = BuyerIdentity()

    if RICH_AVAILABLE:
        console.print(Panel(
            "Commands:\n"
            "  [cyan]list[/cyan] [channel]     - List products (ctv, display, mobile)\n"
            "  [cyan]price[/cyan] <product_id> - Get pricing for a product\n"
            "  [cyan]avail[/cyan] <product_id> <impressions> - Check availability\n"
            "  [cyan]deal[/cyan] <product_id> <price> <impressions> - Create a deal\n"
            "  [cyan]book[/cyan] <deal_id>     - Book an order\n"
            "  [cyan]auto[/cyan]               - Run automated demo\n"
            "  [cyan]quit[/cyan]               - Exit",
            title="[bold]Interactive Commands[/bold]",
            style="cyan"
        ))

    async with LocalSellerClient() as client:
        # Test connection
        result = await client.list_products()
        if not result.get("success", True):
            print_error(f"Cannot connect to seller: {result.get('error')}")
            return

        print_success("Connected to seller agent")
        print("")

        while True:
            try:
                if RICH_AVAILABLE:
                    cmd = Prompt.ask("[bold cyan]buyer>[/bold cyan]")
                else:
                    cmd = input("buyer> ")

                if not cmd:
                    continue

                parts = cmd.strip().split()
                action = parts[0].lower()

                if action == "quit" or action == "exit":
                    print_info("Goodbye!")
                    break

                elif action == "auto":
                    await run_automated_demo()

                elif action == "list":
                    channel = parts[1] if len(parts) > 1 else None
                    result = await client.list_products(channel)
                    if result.get("success"):
                        products = result.get("result", {}).get("products", [])
                        if RICH_AVAILABLE:
                            table = Table(title="Products")
                            table.add_column("ID", style="cyan")
                            table.add_column("Name", style="green")
                            table.add_column("Channel", style="yellow")
                            table.add_column("Base CPM", style="magenta")

                            for p in products:
                                table.add_row(
                                    p["id"],
                                    p["name"][:40],
                                    p["channel"],
                                    f"${p['base_price']:.2f}"
                                )
                            console.print(table)
                        else:
                            for p in products:
                                print(f"  {p['id']}: {p['name']} (${p['base_price']})")

                elif action == "price":
                    if len(parts) < 2:
                        print_error("Usage: price <product_id>")
                        continue
                    product_id = parts[1]
                    result = await client.get_pricing(
                        product_id=product_id,
                        buyer_tier=identity.get_access_tier(),
                        volume=15_000_000,
                        deal_type="preferred_deal"
                    )
                    if result.get("success"):
                        print_json(result.get("result", {}))
                    else:
                        print_error(result.get("error", "Failed"))

                elif action == "avail":
                    if len(parts) < 3:
                        print_error("Usage: avail <product_id> <impressions>")
                        continue
                    result = await client.check_availability(
                        product_id=parts[1],
                        impressions=int(parts[2]),
                        start_date="2026-03-01",
                        end_date="2026-06-30"
                    )
                    if result.get("success"):
                        print_json(result.get("result", {}))
                    else:
                        print_error(result.get("error", "Failed"))

                elif action == "deal":
                    if len(parts) < 4:
                        print_error("Usage: deal <product_id> <price> <impressions>")
                        continue
                    result = await client.create_deal(
                        product_id=parts[1],
                        deal_type="preferred_deal",
                        price=float(parts[2]),
                        impressions=int(parts[3]),
                        buyer_id=identity.seat_id,
                        advertiser_name=identity.advertiser_name
                    )
                    if result.get("success"):
                        deal = result.get("result", {})
                        print_success(f"Created Deal: {deal.get('deal_id')}")
                        print_json(deal)
                    else:
                        print_error(result.get("error", "Failed"))

                elif action == "book":
                    if len(parts) < 2:
                        print_error("Usage: book <deal_id>")
                        continue
                    result = await client.book_order(
                        deal_id=parts[1],
                        order_name="Interactive Order",
                        buyer_id=identity.seat_id
                    )
                    if result.get("success"):
                        order = result.get("result", {})
                        print_success(f"Booked Order: {order.get('order_id')}")
                        print_json(order)
                    else:
                        print_error(result.get("error", "Failed"))

                else:
                    print_error(f"Unknown command: {action}")
                    print_info("Type 'quit' to exit")

            except KeyboardInterrupt:
                print_info("\nGoodbye!")
                break
            except Exception as e:
                print_error(f"Error: {e}")


async def main(seller_url: str = None, mode: str = "auto"):
    """Main entry point."""
    global SELLER_URL
    if seller_url:
        SELLER_URL = seller_url

    if mode == "interactive":
        await run_interactive_mode()
    else:
        await run_automated_demo()


def cli():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Buyer Agent Interactive Demo")
    parser.add_argument(
        "--mode",
        choices=["auto", "interactive"],
        default="auto",
        help="Demo mode: auto (full workflow) or interactive (manual commands)"
    )
    parser.add_argument(
        "--seller-url",
        default=SELLER_URL,
        help="Seller agent URL (default: http://localhost:8001)"
    )

    args = parser.parse_args()
    asyncio.run(main(seller_url=args.seller_url, mode=args.mode))


if __name__ == "__main__":
    cli()
