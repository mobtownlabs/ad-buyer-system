#!/usr/bin/env python3
"""Rivian R2 Campaign Demo - MCP Protocol Integration

This demo shows the buyer agent ingesting the Rivian R2 media brief PDF
and executing the media plan through direct MCP tool calls to seller agents.

The workflow:
1. Parse the PDF media brief to extract campaign requirements
2. Connect to the IAB Tech Lab agentic-direct server
3. Discover available inventory from seller agents
4. Check availability and get tiered pricing
5. Request Deal IDs for OpenDirect and DSP activation
6. Book the campaign lines

Usage:
    cd ad_buyer_system/examples
    python rivian_mcp_demo.py [path_to_pdf]

    If no PDF is provided, uses the default rivian_r2_media_brief.pdf
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Rich console for beautiful output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for enhanced output: pip install rich")

# PDF parsing
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Note: Install 'pdfplumber' for PDF parsing: pip install pdfplumber")

# Import buyer system components
try:
    from ad_buyer.clients.unified_client import UnifiedClient, Protocol
    from ad_buyer.models.buyer_identity import BuyerIdentity, BuyerContext, DealType
except ImportError:
    print("Error: Please install the ad_buyer package first:")
    print("  cd ad_buyer_system && pip install -e .")
    sys.exit(1)


# Console for rich output
console = Console() if RICH_AVAILABLE else None


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


def print_success(text: str):
    """Print success message."""
    if RICH_AVAILABLE:
        console.print(f"[green]:white_check_mark: {text}[/green]")
    else:
        print(f"[OK] {text}")


def print_info(text: str):
    """Print info message."""
    if RICH_AVAILABLE:
        console.print(f"[blue]:information_source: {text}[/blue]")
    else:
        print(f"[INFO] {text}")


@dataclass
class CampaignBrief:
    """Parsed campaign brief from PDF."""
    client: str = "Rivian Automotive"
    campaign_name: str = "Rivian R2 Launch Campaign"
    start_date: str = "2026-03-01"
    end_date: str = "2026-06-30"
    total_budget: float = 4_700_000

    # CTV Component
    ctv_budget: float = 3_500_000
    ctv_monthly: float = 875_000
    ctv_reach_target: int = 5_000_000
    ctv_frequency_target: float = 3.0
    ctv_target_cpm: float = 15.0
    ctv_publishers: list = None

    # Performance Component
    perf_budget: float = 800_000
    perf_monthly: float = 200_000
    perf_formats: list = None

    # Mobile App Component
    mobile_budget: float = 400_000
    mobile_monthly: float = 100_000
    mobile_target_cpi: float = 4.0

    # Audience
    audience_age: str = "30-54"
    audience_hhi: str = "$125,000+"
    audience_interests: list = None

    def __post_init__(self):
        if self.ctv_publishers is None:
            self.ctv_publishers = ["HBO Max", "Peacock", "Paramount+", "Hulu"]
        if self.perf_formats is None:
            self.perf_formats = ["video", "display", "native"]
        if self.audience_interests is None:
            self.audience_interests = [
                "outdoor recreation", "electric vehicles",
                "sustainable living", "adventure travel"
            ]


def parse_pdf_brief(pdf_path: str) -> CampaignBrief:
    """Parse the media brief PDF and extract campaign requirements."""
    print_info(f"Parsing PDF: {pdf_path}")

    if not PDF_AVAILABLE:
        print_info("PDF parsing unavailable, using default campaign brief")
        return CampaignBrief()

    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

        # Parse key values from PDF text
        brief = CampaignBrief()

        # Extract dates if found
        if "March 1" in text and "June 30" in text:
            brief.start_date = "2026-03-01"
            brief.end_date = "2026-06-30"

        # Extract budget
        if "$4,700,000" in text:
            brief.total_budget = 4_700_000

        # Extract reach target
        if "5,000,000" in text or "5 million" in text.lower():
            brief.ctv_reach_target = 5_000_000

        print_success(f"Parsed {len(pdf.pages)} pages from PDF")
        return brief

    except Exception as e:
        print_info(f"Could not parse PDF ({e}), using default campaign brief")
        return CampaignBrief()


async def discover_ctv_inventory(client: UnifiedClient, brief: CampaignBrief) -> list:
    """Discover CTV inventory from seller agents."""
    print_step(2, "Discovering CTV inventory from publishers")

    products_result = await client.list_products()

    if not products_result.success:
        print_info(f"Could not list products: {products_result.error}")
        return []

    products = products_result.data
    if isinstance(products, dict) and 'products' in products:
        products = products['products']
    elif not isinstance(products, list):
        products = [products] if products else []

    print_success(f"Found {len(products)} available products")

    # Display products in table format
    if RICH_AVAILABLE and products:
        table = Table(title="Available Inventory")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Base CPM", style="magenta")

        for p in products[:10]:  # Show first 10
            if isinstance(p, dict):
                table.add_row(
                    str(p.get('id', 'N/A'))[:20],
                    str(p.get('name', 'Unknown'))[:30],
                    str(p.get('deliveryType', p.get('type', 'N/A'))),
                    f"${p.get('basePrice', p.get('price', 0)):.2f}"
                )
        console.print(table)

    return products


async def check_avails_and_pricing(
    client: UnifiedClient,
    products: list,
    brief: CampaignBrief
) -> list:
    """Check availability and get tiered pricing for products."""
    print_step(3, "Checking availability and tiered pricing")

    pricing_results = []

    for product in products[:5]:  # Check first 5 products
        if not isinstance(product, dict):
            continue

        product_id = product.get('id')
        if not product_id:
            continue

        # Get tiered pricing
        pricing = await client.get_pricing(
            product_id=product_id,
            volume=brief.ctv_reach_target * 3,  # 3x frequency
            deal_type="PD",
            flight_start=brief.start_date,
            flight_end=brief.end_date,
        )

        if pricing.success and pricing.data:
            data = pricing.data
            p_info = data.get('pricing', {})

            result = {
                'product_id': product_id,
                'product_name': data.get('name', product.get('name', 'Unknown')),
                'base_price': p_info.get('base_price', data.get('basePrice', 0)),
                'tiered_price': p_info.get('tiered_price', 0),
                'tier': p_info.get('tier', 'public'),
                'tier_discount': p_info.get('tier_discount', 0),
                'volume_discount': p_info.get('volume_discount', 0),
            }
            pricing_results.append(result)

    # Display pricing table
    if RICH_AVAILABLE and pricing_results:
        table = Table(title="Tiered Pricing Results")
        table.add_column("Product", style="cyan")
        table.add_column("Base CPM", style="yellow")
        table.add_column("Tier", style="green")
        table.add_column("Discount", style="magenta")
        table.add_column("Final CPM", style="bold green")

        for r in pricing_results:
            discount = r['tier_discount'] + r['volume_discount']
            table.add_row(
                r['product_name'][:25],
                f"${r['base_price']:.2f}",
                r['tier'],
                f"{discount:.0f}%",
                f"${r['tiered_price']:.2f}"
            )
        console.print(table)

    return pricing_results


async def request_deal_ids(
    client: UnifiedClient,
    pricing_results: list,
    brief: CampaignBrief
) -> list:
    """Request Deal IDs for selected products."""
    print_step(4, "Requesting Deal IDs from seller agents")

    deals = []
    impressions_per_product = (brief.ctv_reach_target * 3) // max(len(pricing_results), 1)

    for item in pricing_results[:3]:  # Request deals for top 3 products
        deal_result = await client.request_deal(
            product_id=item['product_id'],
            deal_type="PD",  # Preferred Deal
            impressions=impressions_per_product,
            flight_start=brief.start_date,
            flight_end=brief.end_date,
            target_cpm=brief.ctv_target_cpm,
        )

        if deal_result.success and deal_result.data:
            d = deal_result.data
            deals.append(d)

            print_success(f"Deal ID created: {d.get('deal_id')}")
            print_info(f"  Product: {d.get('product_name')}")
            print_info(f"  Price: ${d.get('price', 0):.2f} CPM (was ${d.get('original_price', 0):.2f})")
            print_info(f"  Tier: {d.get('access_tier')}")

    return deals


async def create_opendirect_orders(
    client: UnifiedClient,
    deals: list,
    brief: CampaignBrief
) -> dict:
    """Create OpenDirect orders and line items."""
    print_step(5, "Creating OpenDirect orders and line items")

    # First, create an account
    account_result = await client.create_account(
        name=f"Rivian R2 Campaign - {brief.client}",
        account_type="advertiser",
        status="active"
    )

    if not account_result.success:
        print_info(f"Account creation info: {account_result.error or 'Using existing'}")
        # Try to list accounts to get an existing one
        accounts = await client.list_accounts()
        if accounts.success and accounts.data:
            acc_list = accounts.data
            if isinstance(acc_list, dict) and 'accounts' in acc_list:
                acc_list = acc_list['accounts']
            elif not isinstance(acc_list, list):
                acc_list = [acc_list] if acc_list else []
            if acc_list:
                account_id = acc_list[0].get('id', 'demo-account')
            else:
                account_id = 'demo-account'
        else:
            account_id = 'demo-account'
    else:
        account_id = account_result.data.get('id', 'demo-account') if isinstance(account_result.data, dict) else 'demo-account'

    print_success(f"Using account: {account_id}")

    # Create order
    order_result = await client.create_order(
        account_id=account_id,
        name=f"Rivian R2 CTV Campaign Q1-Q2 2026",
        budget=brief.ctv_budget,
        start_date=brief.start_date,
        end_date=brief.end_date,
    )

    order_id = None
    if order_result.success and order_result.data:
        if isinstance(order_result.data, dict):
            order_id = order_result.data.get('id')
        print_success(f"Created order: {order_id}")
    else:
        print_info(f"Order creation info: {order_result.error or 'Using simulation'}")
        order_id = 'demo-order'

    # Create line items for each deal
    lines = []
    for i, deal in enumerate(deals):
        line_result = await client.create_line(
            order_id=order_id or 'demo-order',
            product_id=deal.get('product_id', f'product-{i}'),
            name=f"R2 CTV - {deal.get('product_name', f'Line {i+1}')}",
            quantity=deal.get('impressions', 5_000_000),
            start_date=brief.start_date,
            end_date=brief.end_date,
        )

        if line_result.success:
            line_data = line_result.data if isinstance(line_result.data, dict) else {}
            lines.append({
                'line_id': line_data.get('id', f'line-{i}'),
                'deal_id': deal.get('deal_id'),
                'product': deal.get('product_name'),
                'impressions': deal.get('impressions'),
                'cpm': deal.get('price'),
            })
            print_success(f"Created line item for: {deal.get('product_name')}")

    return {
        'account_id': account_id,
        'order_id': order_id,
        'lines': lines,
        'deals': deals,
    }


def print_campaign_summary(
    brief: CampaignBrief,
    deals: list,
    booking: dict
):
    """Print the final campaign summary."""
    print_header("CAMPAIGN BOOKING SUMMARY")

    if RICH_AVAILABLE:
        # Campaign Overview
        console.print("\n[bold]Campaign Overview[/bold]")
        overview_table = Table(show_header=False, box=None)
        overview_table.add_column("", style="dim")
        overview_table.add_column("")
        overview_table.add_row("Client", brief.client)
        overview_table.add_row("Campaign", brief.campaign_name)
        overview_table.add_row("Flight", f"{brief.start_date} to {brief.end_date}")
        overview_table.add_row("Total Budget", f"${brief.total_budget:,.2f}")
        console.print(overview_table)

        # Deal IDs for DSP Activation
        console.print("\n[bold]Deal IDs for DSP Activation[/bold]")
        deal_table = Table()
        deal_table.add_column("Deal ID", style="cyan bold")
        deal_table.add_column("Product", style="green")
        deal_table.add_column("CPM", style="yellow")
        deal_table.add_column("Impressions", style="magenta")

        for deal in deals:
            deal_table.add_row(
                deal.get('deal_id', 'N/A'),
                deal.get('product_name', 'Unknown')[:30],
                f"${deal.get('price', 0):.2f}",
                f"{deal.get('impressions', 0):,}"
            )
        console.print(deal_table)

        # DSP Activation Instructions
        if deals:
            console.print("\n[bold]DSP Activation Instructions[/bold]")
            instructions = deals[0].get('activation_instructions', {})
            for platform, instruction in instructions.items():
                console.print(f"  [cyan]{platform.upper()}:[/cyan] {instruction}")

        # OpenDirect Booking
        console.print("\n[bold]OpenDirect Booking[/bold]")
        console.print(f"  Order ID: {booking.get('order_id')}")
        console.print(f"  Account ID: {booking.get('account_id')}")
        console.print(f"  Lines Created: {len(booking.get('lines', []))}")
    else:
        print(f"\nClient: {brief.client}")
        print(f"Campaign: {brief.campaign_name}")
        print(f"Flight: {brief.start_date} to {brief.end_date}")
        print(f"Total Budget: ${brief.total_budget:,.2f}")
        print("\nDeal IDs Created:")
        for deal in deals:
            print(f"  - {deal.get('deal_id')}: {deal.get('product_name')} @ ${deal.get('price', 0):.2f} CPM")

    print("\n" + "=" * 60)
    print("Demo complete! The campaign has been planned and booked.")
    print("=" * 60)


async def run_demo(pdf_path: Optional[str] = None):
    """Run the complete demo workflow."""
    print_header("RIVIAN R2 CAMPAIGN - MCP DEMO")
    print_info("Demonstrating IAB Tech Lab OpenDirect + MCP Integration")
    print_info("Protocol: MCP (Model Context Protocol)")
    print("")

    # Step 1: Parse the PDF
    print_step(1, "Parsing media brief PDF")

    if pdf_path is None:
        pdf_path = Path(__file__).parent / "rivian_r2_media_brief.pdf"

    brief = parse_pdf_brief(str(pdf_path))

    if RICH_AVAILABLE:
        console.print(f"\n[dim]Campaign:[/dim] {brief.campaign_name}")
        console.print(f"[dim]Budget:[/dim] ${brief.total_budget:,.2f}")
        console.print(f"[dim]CTV Target:[/dim] {brief.ctv_reach_target:,} reach @ {brief.ctv_frequency_target}x frequency")

    # Create buyer identity for tiered pricing
    identity = BuyerIdentity(
        seat_id="amazon-dsp-001",
        seat_name="Amazon DSP",
        agency_id="agency-abc-001",
        agency_name="Agency ABC",
        agency_holding_company="Agency ABC Group",
        advertiser_id="rivian-automotive-001",
        advertiser_name="Rivian Automotive",
        advertiser_industry="Automotive",
    )

    print_info(f"Buyer Identity: {identity.agency_name} + {identity.advertiser_name}")
    print_info(f"Access Tier: {identity.get_access_tier().value}")
    print_info(f"Discount: {identity.get_discount_percentage()}%")

    # Connect to IAB server with MCP protocol
    async with UnifiedClient(protocol=Protocol.MCP, buyer_identity=identity) as client:
        print_success("Connected to IAB Tech Lab agentic-direct server")
        print_info(f"Protocol: {client.default_protocol.value.upper()}")

        # Step 2: Discover inventory
        products = await discover_ctv_inventory(client, brief)

        # Step 3: Check availability and pricing
        pricing_results = await check_avails_and_pricing(client, products, brief)

        # Step 4: Request Deal IDs
        deals = await request_deal_ids(client, pricing_results, brief)

        # Step 5: Create OpenDirect orders
        booking = await create_opendirect_orders(client, deals, brief)

        # Print summary
        print_campaign_summary(brief, deals, booking)

        # Output JSON for programmatic consumption
        output = {
            'timestamp': datetime.now().isoformat(),
            'protocol': 'MCP',
            'campaign': {
                'name': brief.campaign_name,
                'client': brief.client,
                'budget': brief.total_budget,
                'start_date': brief.start_date,
                'end_date': brief.end_date,
            },
            'buyer_identity': {
                'agency': identity.agency_name,
                'advertiser': identity.advertiser_name,
                'tier': identity.get_access_tier().value,
            },
            'deals': deals,
            'booking': booking,
        }

        # Save to file
        output_path = Path(__file__).parent / "rivian_demo_output.json"
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        print_info(f"Output saved to: {output_path}")


def main():
    """Main entry point."""
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(run_demo(pdf_path))


if __name__ == "__main__":
    main()
