#!/usr/bin/env python3
"""Rivian R2 Campaign Demo - A2A (Agent-to-Agent) Protocol

This demo shows the buyer agent using natural language A2A protocol
to interact with seller agents for the Rivian R2 media campaign.

Unlike the MCP demo which uses direct tool calls, A2A uses natural language
that is interpreted by AI on the server side - demonstrating how two
AI agents can negotiate and transact using conversational protocols.

Usage:
    cd ad_buyer_system/examples
    python rivian_a2a_demo.py

Demo Prompts:
    The script will guide you through example prompts to use in a live demo.
    You can run it in interactive mode or let it execute automatically.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Rich console for beautiful output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Import buyer system components
try:
    from ad_buyer.clients.unified_client import UnifiedClient, Protocol
    from ad_buyer.clients.a2a_client import A2AClient
    from ad_buyer.models.buyer_identity import BuyerIdentity
except ImportError:
    print("Error: Please install the ad_buyer package first:")
    print("  cd ad_buyer_system && pip install -e .")
    sys.exit(1)


console = Console() if RICH_AVAILABLE else None


def print_header(text: str):
    """Print a styled header."""
    if RICH_AVAILABLE:
        console.print(Panel(text, style="bold blue"))
    else:
        print("\n" + "=" * 60)
        print(text)
        print("=" * 60)


def print_prompt(prompt: str):
    """Print a demo prompt."""
    if RICH_AVAILABLE:
        console.print(f"\n[bold yellow]DEMO PROMPT:[/bold yellow]")
        console.print(Panel(prompt, style="yellow"))
    else:
        print(f"\n>>> DEMO PROMPT:")
        print(f"    \"{prompt}\"")


def print_response(response: str):
    """Print agent response."""
    if RICH_AVAILABLE:
        console.print(f"\n[bold green]AGENT RESPONSE:[/bold green]")
        console.print(Panel(response, style="green"))
    else:
        print(f"\n<<< AGENT RESPONSE:")
        print(f"    {response}")


def print_json_response(data: dict):
    """Print JSON response."""
    if RICH_AVAILABLE:
        console.print("[dim]Response Data:[/dim]")
        console.print_json(json.dumps(data, indent=2, default=str))
    else:
        print("Response Data:")
        print(json.dumps(data, indent=2, default=str))


# Demo prompts for the webinar
DEMO_PROMPTS = [
    {
        "step": 1,
        "title": "Discovery - What inventory is available?",
        "prompt": "What CTV streaming inventory do you have available for Q1-Q2 2026? I'm looking for premium publishers like HBO Max, Peacock, Paramount+, and Hulu with household targeting capabilities.",
        "description": "This natural language query demonstrates how buyer agents can discover inventory without knowing specific product IDs or API parameters."
    },
    {
        "step": 2,
        "title": "Pricing Inquiry - Get tier-specific rates",
        "prompt": "I'm from Agency ABC representing Rivian Automotive. What's your best CPM pricing for 15 million CTV impressions across your premium streaming inventory from March through June 2026?",
        "description": "By revealing agency and advertiser identity, the buyer unlocks tiered pricing. The seller agent will provide better rates than public pricing."
    },
    {
        "step": 3,
        "title": "Request Deal IDs for DSP Activation",
        "prompt": "I'd like to create a Preferred Deal for 5 million impressions on your CTV inventory at $15 CPM for Rivian's R2 launch campaign running March 1 to June 30, 2026. Please provide Deal IDs I can activate in Amazon DSP and The Trade Desk.",
        "description": "This request triggers deal creation. The seller agent will generate Deal IDs that can be used in traditional DSP platforms."
    },
    {
        "step": 4,
        "title": "Book OpenDirect Lines",
        "prompt": "Please create an order for Rivian R2 CTV Campaign with a budget of $875,000 per month for 4 months. Book line items for your HBO Max, Peacock, and Paramount+ inventory with the Deal IDs we just created.",
        "description": "The seller agent creates OpenDirect order and line items, booking the inventory with the negotiated deal terms."
    },
    {
        "step": 5,
        "title": "Performance Campaign Inquiry",
        "prompt": "For the same Rivian R2 campaign, I also need performance inventory - desktop and mobile video, display banners, and native ads across ComScore Top 200 publishers. Budget is $200,000 per month optimizing for conversions. What can you offer?",
        "description": "Demonstrates multi-channel campaign planning with the same conversation context."
    },
    {
        "step": 6,
        "title": "Mobile App Campaign",
        "prompt": "Finally, I need mobile app install inventory for the Rivian app with deep links to the R2 reservation page. Budget is $100,000 per month, targeting iOS and Android users interested in electric vehicles and outdoor activities.",
        "description": "Shows how the A2A protocol handles different inventory types in the same conversation."
    },
]


async def run_interactive_demo():
    """Run the demo in interactive mode."""
    print_header("RIVIAN R2 CAMPAIGN - A2A INTERACTIVE DEMO")

    if RICH_AVAILABLE:
        console.print("\n[bold]This demo uses the A2A (Agent-to-Agent) protocol[/bold]")
        console.print("[dim]Natural language requests are interpreted by AI on the seller side[/dim]\n")

    # Create buyer identity
    identity = BuyerIdentity(
        seat_id="amazon-dsp-001",
        seat_name="Amazon DSP",
        agency_id="agency-abc-001",
        agency_name="Agency ABC",
        advertiser_id="rivian-automotive-001",
        advertiser_name="Rivian Automotive",
        advertiser_industry="Automotive",
    )

    if RICH_AVAILABLE:
        console.print(f"[bold]Buyer Identity:[/bold] {identity.agency_name} + {identity.advertiser_name}")
        console.print(f"[bold]Access Tier:[/bold] {identity.get_access_tier().value}")
        console.print(f"[bold]Tier Discount:[/bold] {identity.get_discount_percentage()}%\n")

    # Connect with A2A protocol
    async with UnifiedClient(protocol=Protocol.A2A, buyer_identity=identity) as client:
        if RICH_AVAILABLE:
            console.print("[green]:white_check_mark: Connected to IAB Tech Lab server[/green]")
            console.print("[dim]Protocol: A2A (Agent-to-Agent)[/dim]\n")

        for demo in DEMO_PROMPTS:
            if RICH_AVAILABLE:
                console.print(f"\n[bold cyan]Step {demo['step']}: {demo['title']}[/bold cyan]")
                console.print(f"[dim]{demo['description']}[/dim]")
            else:
                print(f"\n=== Step {demo['step']}: {demo['title']} ===")
                print(f"({demo['description']})")

            # Show the prompt
            print_prompt(demo['prompt'])

            # Ask to continue in interactive mode
            if RICH_AVAILABLE:
                proceed = Confirm.ask("\nExecute this prompt?", default=True)
            else:
                response = input("\nExecute this prompt? [Y/n]: ").strip().lower()
                proceed = response != 'n'

            if proceed:
                try:
                    # Send the natural language request
                    result = await client.send_natural_language(demo['prompt'])

                    if result.success:
                        if result.data:
                            if isinstance(result.data, str):
                                print_response(result.data)
                            else:
                                print_response(str(result.data)[:500])
                                if isinstance(result.data, dict):
                                    print_json_response(result.data)
                        else:
                            print_response("Request processed successfully")
                    else:
                        if RICH_AVAILABLE:
                            console.print(f"[red]Error: {result.error}[/red]")
                        else:
                            print(f"Error: {result.error}")
                except Exception as e:
                    if RICH_AVAILABLE:
                        console.print(f"[yellow]Note: {e}[/yellow]")
                    else:
                        print(f"Note: {e}")

            if RICH_AVAILABLE:
                console.print("[dim]" + "-" * 60 + "[/dim]")

    print_header("A2A DEMO COMPLETE")


async def run_automated_demo():
    """Run the demo automatically with all prompts."""
    print_header("RIVIAN R2 CAMPAIGN - A2A AUTOMATED DEMO")

    if RICH_AVAILABLE:
        console.print("\n[bold]Running all demo prompts automatically...[/bold]\n")

    identity = BuyerIdentity(
        seat_id="amazon-dsp-001",
        seat_name="Amazon DSP",
        agency_id="agency-abc-001",
        agency_name="Agency ABC",
        advertiser_id="rivian-automotive-001",
        advertiser_name="Rivian Automotive",
        advertiser_industry="Automotive",
    )

    results = []

    async with UnifiedClient(protocol=Protocol.A2A, buyer_identity=identity) as client:
        if RICH_AVAILABLE:
            console.print("[green]:white_check_mark: Connected to IAB Tech Lab server[/green]\n")

        for demo in DEMO_PROMPTS:
            if RICH_AVAILABLE:
                console.print(f"\n[bold cyan]Step {demo['step']}: {demo['title']}[/bold cyan]")
            else:
                print(f"\n=== Step {demo['step']}: {demo['title']} ===")

            print_prompt(demo['prompt'])

            try:
                result = await client.send_natural_language(demo['prompt'])

                if result.success:
                    response_text = ""
                    if result.data:
                        if isinstance(result.data, str):
                            response_text = result.data
                        else:
                            response_text = str(result.data)[:300]
                    print_response(response_text or "Request processed")

                    results.append({
                        'step': demo['step'],
                        'title': demo['title'],
                        'prompt': demo['prompt'],
                        'success': True,
                        'response': result.data,
                    })
                else:
                    print_response(f"Error: {result.error}")
                    results.append({
                        'step': demo['step'],
                        'title': demo['title'],
                        'prompt': demo['prompt'],
                        'success': False,
                        'error': result.error,
                    })

            except Exception as e:
                if RICH_AVAILABLE:
                    console.print(f"[yellow]Note: {e}[/yellow]")
                results.append({
                    'step': demo['step'],
                    'title': demo['title'],
                    'prompt': demo['prompt'],
                    'success': False,
                    'error': str(e),
                })

            await asyncio.sleep(0.5)  # Small delay between requests

    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'protocol': 'A2A',
        'buyer': {
            'agency': identity.agency_name,
            'advertiser': identity.advertiser_name,
            'tier': identity.get_access_tier().value,
        },
        'demo_results': results,
    }

    output_path = Path(__file__).parent / "rivian_a2a_output.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    if RICH_AVAILABLE:
        console.print(f"\n[dim]Results saved to: {output_path}[/dim]")

    print_header("A2A DEMO COMPLETE")


def print_demo_script():
    """Print the demo script for the webinar."""
    print_header("RIVIAN R2 A2A DEMO - WEBINAR SCRIPT")

    if RICH_AVAILABLE:
        console.print("\n[bold]Demo Prompts for Webinar Presentation[/bold]")
        console.print("[dim]Copy these prompts to use during your live demo[/dim]\n")

        for demo in DEMO_PROMPTS:
            console.print(f"\n[bold cyan]Step {demo['step']}: {demo['title']}[/bold cyan]")
            console.print(f"[dim]{demo['description']}[/dim]")
            console.print(Panel(demo['prompt'], style="yellow", title="Prompt"))
    else:
        print("\nDemo Prompts for Webinar Presentation")
        print("-" * 60)

        for demo in DEMO_PROMPTS:
            print(f"\n=== Step {demo['step']}: {demo['title']} ===")
            print(f"Description: {demo['description']}")
            print(f"\nPrompt:")
            print(f'  "{demo["prompt"]}"')


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "script":
            print_demo_script()
            return
        elif mode == "auto":
            asyncio.run(run_automated_demo())
            return

    # Default: interactive mode
    asyncio.run(run_interactive_demo())


if __name__ == "__main__":
    print("""
Rivian R2 Campaign - A2A Demo
=============================

Usage:
  python rivian_a2a_demo.py          # Interactive demo
  python rivian_a2a_demo.py auto     # Automated demo
  python rivian_a2a_demo.py script   # Print demo script for webinar
""")
    main()
