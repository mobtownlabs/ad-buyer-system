"""Channel Specialist Crews for inventory research and booking."""

from typing import Any

from crewai import Crew, Process, Task

from ..agents.level2.branding_agent import create_branding_agent
from ..agents.level2.ctv_agent import create_ctv_agent
from ..agents.level2.mobile_app_agent import create_mobile_app_agent
from ..agents.level2.performance_agent import create_performance_agent
from ..agents.level3.execution_agent import create_execution_agent
from ..agents.level3.research_agent import create_research_agent
from ..clients.opendirect_client import OpenDirectClient
from ..config.settings import settings
from ..tools.execution.line_management import BookLineTool, CreateLineTool, ReserveLineTool
from ..tools.execution.order_management import CreateOrderTool
from ..tools.research.avails_check import AvailsCheckTool
from ..tools.research.product_search import ProductSearchTool


def _create_research_tools(client: OpenDirectClient) -> list[Any]:
    """Create research tools with the OpenDirect client."""
    return [
        ProductSearchTool(client),
        AvailsCheckTool(client),
    ]


def _create_execution_tools(client: OpenDirectClient) -> list[Any]:
    """Create execution tools with the OpenDirect client."""
    return [
        CreateOrderTool(client),
        CreateLineTool(client),
        ReserveLineTool(client),
        BookLineTool(client),
    ]


def create_branding_crew(
    client: OpenDirectClient,
    channel_brief: dict[str, Any],
) -> Crew:
    """Create the Branding Specialist crew.

    Args:
        client: OpenDirect API client
        channel_brief: Channel-specific brief with budget, dates, etc.

    Returns:
        Configured Branding Crew
    """
    # Create tools
    research_tools = _create_research_tools(client)
    execution_tools = _create_execution_tools(client)

    # Create agents with tools
    branding_agent = create_branding_agent()
    research_agent = create_research_agent(tools=research_tools)
    execution_agent = create_execution_agent(tools=execution_tools)

    # Define research task
    research_task = Task(
        description=f"""
Research premium display and video inventory for a branding campaign:

Budget: ${channel_brief.get('budget', 0):,.2f}
Flight: {channel_brief.get('start_date')} to {channel_brief.get('end_date')}
Target Audience: {channel_brief.get('target_audience', {})}
Objectives: {channel_brief.get('objectives', [])}
Quality Requirements: Viewability > 70%, Brand Safety verified

Search for:
1. High-impact display placements (homepage takeovers, roadblocks)
2. Premium video placements (in-stream, outstream)
3. Cross-device reach opportunities

For the top 5 products, check availability and pricing for the flight dates.
Provide ranked recommendations with rationale.
""",
        expected_output="""List of recommended products:
[
    {
        "product_id": "...",
        "product_name": "...",
        "publisher": "...",
        "format": "...",
        "impressions": X,
        "cpm": Y,
        "cost": Z,
        "rationale": "..."
    }
]""",
        agent=research_agent,
    )

    # Define recommendation task
    recommendation_task = Task(
        description="""
Review the research findings and select the best inventory for this
branding campaign. Consider:

1. Alignment with campaign objectives
2. Budget efficiency
3. Reach and frequency
4. Quality metrics

Finalize your recommendations for approval.
""",
        expected_output="""Final recommendations with booking priority:
{
    "recommendations": [...],
    "total_impressions": X,
    "total_cost": Y,
    "summary": "..."
}""",
        agent=branding_agent,
        context=[research_task],
    )

    return Crew(
        agents=[branding_agent, research_agent, execution_agent],
        tasks=[research_task, recommendation_task],
        process=Process.hierarchical,
        manager_agent=branding_agent,
        memory=settings.crew_memory_enabled,
        verbose=settings.crew_verbose,
    )


def create_mobile_crew(
    client: OpenDirectClient,
    channel_brief: dict[str, Any],
) -> Crew:
    """Create the Mobile App Install Specialist crew.

    Args:
        client: OpenDirect API client
        channel_brief: Channel-specific brief with budget, dates, etc.

    Returns:
        Configured Mobile App Crew
    """
    # Create tools
    research_tools = _create_research_tools(client)
    execution_tools = _create_execution_tools(client)

    # Create agents with tools
    mobile_agent = create_mobile_app_agent()
    research_agent = create_research_agent(tools=research_tools)
    execution_agent = create_execution_agent(tools=execution_tools)

    # Define research task
    research_task = Task(
        description=f"""
Research mobile app install inventory:

Budget: ${channel_brief.get('budget', 0):,.2f}
Flight: {channel_brief.get('start_date')} to {channel_brief.get('end_date')}
Target Audience: {channel_brief.get('target_audience', {})}
Objectives: {channel_brief.get('objectives', [])}

Search for:
1. In-app interstitial placements
2. Rewarded video inventory
3. Mobile web placements
4. Inventory with low fraud rates

Focus on publishers with MMP integrations for proper attribution.
Provide ranked recommendations with rationale.
""",
        expected_output="""List of recommended products with fraud scores and MMP support.""",
        agent=research_agent,
    )

    recommendation_task = Task(
        description="""
Review the research findings and select the best mobile inventory.
Prioritize quality over scale - low fraud and proper attribution are critical.
""",
        expected_output="""Final recommendations with booking priority.""",
        agent=mobile_agent,
        context=[research_task],
    )

    return Crew(
        agents=[mobile_agent, research_agent, execution_agent],
        tasks=[research_task, recommendation_task],
        process=Process.hierarchical,
        manager_agent=mobile_agent,
        memory=settings.crew_memory_enabled,
        verbose=settings.crew_verbose,
    )


def create_ctv_crew(
    client: OpenDirectClient,
    channel_brief: dict[str, Any],
) -> Crew:
    """Create the CTV Specialist crew.

    Args:
        client: OpenDirect API client
        channel_brief: Channel-specific brief with budget, dates, etc.

    Returns:
        Configured CTV Crew
    """
    # Create tools
    research_tools = _create_research_tools(client)
    execution_tools = _create_execution_tools(client)

    # Create agents with tools
    ctv_agent = create_ctv_agent()
    research_agent = create_research_agent(tools=research_tools)
    execution_agent = create_execution_agent(tools=execution_tools)

    # Define research task
    research_task = Task(
        description=f"""
Research Connected TV and streaming inventory:

Budget: ${channel_brief.get('budget', 0):,.2f}
Flight: {channel_brief.get('start_date')} to {channel_brief.get('end_date')}
Target Audience: {channel_brief.get('target_audience', {})}
Objectives: {channel_brief.get('objectives', [])}

Search for:
1. Premium streaming platforms (Hulu, Peacock, etc.)
2. FAST channels (Pluto, Tubi, Freevee)
3. Device-specific inventory (Roku, Fire TV, etc.)
4. PMPs with household targeting

Prioritize brand-safe, premium content environments.
Provide ranked recommendations with rationale.
""",
        expected_output="""List of recommended CTV products with household reach estimates.""",
        agent=research_agent,
    )

    recommendation_task = Task(
        description="""
Review the research findings and select the best CTV inventory.
Balance reach with frequency management across devices.
""",
        expected_output="""Final recommendations with booking priority.""",
        agent=ctv_agent,
        context=[research_task],
    )

    return Crew(
        agents=[ctv_agent, research_agent, execution_agent],
        tasks=[research_task, recommendation_task],
        process=Process.hierarchical,
        manager_agent=ctv_agent,
        memory=settings.crew_memory_enabled,
        verbose=settings.crew_verbose,
    )


def create_performance_crew(
    client: OpenDirectClient,
    channel_brief: dict[str, Any],
) -> Crew:
    """Create the Performance/Remarketing Specialist crew.

    Args:
        client: OpenDirect API client
        channel_brief: Channel-specific brief with budget, dates, etc.

    Returns:
        Configured Performance Crew
    """
    # Create tools
    research_tools = _create_research_tools(client)
    execution_tools = _create_execution_tools(client)

    # Create agents with tools
    performance_agent = create_performance_agent()
    research_agent = create_research_agent(tools=research_tools)
    execution_agent = create_execution_agent(tools=execution_tools)

    # Define research task
    research_task = Task(
        description=f"""
Research performance and remarketing inventory:

Budget: ${channel_brief.get('budget', 0):,.2f}
Flight: {channel_brief.get('start_date')} to {channel_brief.get('end_date')}
Target Audience: {channel_brief.get('target_audience', {})}
Objectives: {channel_brief.get('objectives', [])}
KPIs: {channel_brief.get('kpis', {})}

Search for:
1. Retargeting-optimized inventory
2. Conversion-focused placements
3. Dynamic creative-enabled publishers
4. Performance-priced inventory (CPA/CPC options)

Prioritize inventory with strong conversion histories.
Provide ranked recommendations with rationale.
""",
        expected_output="""List of recommended products with conversion rate estimates.""",
        agent=research_agent,
    )

    recommendation_task = Task(
        description="""
Review the research findings and select the best performance inventory.
Optimize for ROAS and conversion efficiency.
""",
        expected_output="""Final recommendations with booking priority.""",
        agent=performance_agent,
        context=[research_task],
    )

    return Crew(
        agents=[performance_agent, research_agent, execution_agent],
        tasks=[research_task, recommendation_task],
        process=Process.hierarchical,
        manager_agent=performance_agent,
        memory=settings.crew_memory_enabled,
        verbose=settings.crew_verbose,
    )
