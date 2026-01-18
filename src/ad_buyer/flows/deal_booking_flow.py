"""Deal Booking Flow - main workflow for booking advertising deals."""

import json
from datetime import datetime
from typing import Any

from crewai.flow.flow import Flow, listen, or_, start

from ..clients.opendirect_client import OpenDirectClient
from ..crews.channel_crews import (
    create_branding_crew,
    create_ctv_crew,
    create_mobile_crew,
    create_performance_crew,
)
from ..crews.portfolio_crew import create_portfolio_crew
from ..models.flow_state import (
    BookingState,
    ChannelAllocation,
    ChannelBrief,
    ExecutionStatus,
    ProductRecommendation,
)


class DealBookingFlow(Flow[BookingState]):
    """Event-driven flow for end-to-end deal booking workflow.

    Flow steps:
    1. Receive and validate campaign brief
    2. Portfolio manager allocates budget across channels
    3. Channel specialists research inventory (parallel)
    4. Consolidate recommendations for approval
    5. Human approval checkpoint
    6. Execute bookings
    7. Confirm and report
    """

    def __init__(self, client: OpenDirectClient):
        """Initialize the flow with OpenDirect client.

        Args:
            client: OpenDirect API client for publisher interactions
        """
        super().__init__()
        self._client = client

    @start()
    def receive_campaign_brief(self) -> dict[str, Any]:
        """Entry point: validate and store campaign brief."""
        brief = self.state.campaign_brief

        # Validate required fields
        required = ["objectives", "budget", "start_date", "end_date", "target_audience"]
        missing = [f for f in required if f not in brief]

        if missing:
            self.state.errors.append(f"Missing required fields: {missing}")
            self.state.execution_status = ExecutionStatus.VALIDATION_FAILED
            return {"status": "failed", "errors": self.state.errors}

        # Validate budget
        if brief.get("budget", 0) <= 0:
            self.state.errors.append("Budget must be greater than 0")
            self.state.execution_status = ExecutionStatus.VALIDATION_FAILED
            return {"status": "failed", "errors": self.state.errors}

        self.state.execution_status = ExecutionStatus.BRIEF_RECEIVED
        self.state.updated_at = datetime.utcnow()

        return {"status": "success", "brief": brief}

    @listen(receive_campaign_brief)
    def allocate_budget(self, brief_result: dict[str, Any]) -> dict[str, Any]:
        """Portfolio manager determines channel budget allocation."""
        if brief_result.get("status") != "success":
            return brief_result

        try:
            # Create and run portfolio crew
            portfolio_crew = create_portfolio_crew(
                client=self._client,
                campaign_brief=self.state.campaign_brief,
            )

            result = portfolio_crew.kickoff()

            # Parse allocation result
            # The result should be a JSON string with allocations
            result_str = str(result)

            # Try to extract JSON from the result
            allocations = self._parse_allocations(result_str)

            # Store allocations
            for channel, alloc_data in allocations.items():
                if alloc_data.get("budget", 0) > 0:
                    self.state.budget_allocations[channel] = ChannelAllocation(
                        channel=channel,
                        budget=alloc_data["budget"],
                        percentage=alloc_data.get("percentage", 0),
                        rationale=alloc_data.get("rationale", ""),
                    )

            self.state.execution_status = ExecutionStatus.BUDGET_ALLOCATED
            self.state.updated_at = datetime.utcnow()

            return {
                "status": "success",
                "allocations": {k: v.model_dump() for k, v in self.state.budget_allocations.items()},
            }

        except Exception as e:
            self.state.errors.append(f"Budget allocation failed: {e}")
            self.state.execution_status = ExecutionStatus.FAILED
            return {"status": "failed", "error": str(e)}

    def _parse_allocations(self, result_str: str) -> dict[str, Any]:
        """Parse allocation JSON from crew result."""
        # Try to find JSON in the result
        try:
            # Look for JSON block
            start_idx = result_str.find("{")
            end_idx = result_str.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = result_str[start_idx:end_idx]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Default allocations if parsing fails
        total_budget = self.state.campaign_brief.get("budget", 0)
        return {
            "branding": {"budget": total_budget * 0.4, "percentage": 40, "rationale": "Default allocation"},
            "performance": {"budget": total_budget * 0.4, "percentage": 40, "rationale": "Default allocation"},
            "ctv": {"budget": total_budget * 0.2, "percentage": 20, "rationale": "Default allocation"},
            "mobile_app": {"budget": 0, "percentage": 0, "rationale": "Not allocated"},
        }

    @listen(allocate_budget)
    def research_branding(self, allocation_result: dict[str, Any]) -> dict[str, Any]:
        """Branding specialist researches display/video inventory."""
        if allocation_result.get("status") != "success":
            return {"channel": "branding", "status": "skipped"}

        branding_alloc = self.state.budget_allocations.get("branding")
        if not branding_alloc or branding_alloc.budget <= 0:
            return {"channel": "branding", "status": "no_budget"}

        try:
            self.state.execution_status = ExecutionStatus.RESEARCHING

            channel_brief = self._create_channel_brief("branding", branding_alloc)
            crew = create_branding_crew(self._client, channel_brief)
            result = crew.kickoff()

            recommendations = self._parse_recommendations(str(result), "branding")
            self.state.channel_recommendations["branding"] = recommendations
            self.state.updated_at = datetime.utcnow()

            return {"channel": "branding", "status": "success", "count": len(recommendations)}

        except Exception as e:
            self.state.errors.append(f"Branding research failed: {e}")
            return {"channel": "branding", "status": "failed", "error": str(e)}

    @listen(allocate_budget)
    def research_ctv(self, allocation_result: dict[str, Any]) -> dict[str, Any]:
        """CTV specialist researches streaming inventory."""
        if allocation_result.get("status") != "success":
            return {"channel": "ctv", "status": "skipped"}

        ctv_alloc = self.state.budget_allocations.get("ctv")
        if not ctv_alloc or ctv_alloc.budget <= 0:
            return {"channel": "ctv", "status": "no_budget"}

        try:
            channel_brief = self._create_channel_brief("ctv", ctv_alloc)
            crew = create_ctv_crew(self._client, channel_brief)
            result = crew.kickoff()

            recommendations = self._parse_recommendations(str(result), "ctv")
            self.state.channel_recommendations["ctv"] = recommendations
            self.state.updated_at = datetime.utcnow()

            return {"channel": "ctv", "status": "success", "count": len(recommendations)}

        except Exception as e:
            self.state.errors.append(f"CTV research failed: {e}")
            return {"channel": "ctv", "status": "failed", "error": str(e)}

    @listen(allocate_budget)
    def research_mobile(self, allocation_result: dict[str, Any]) -> dict[str, Any]:
        """Mobile specialist researches app install inventory."""
        if allocation_result.get("status") != "success":
            return {"channel": "mobile_app", "status": "skipped"}

        mobile_alloc = self.state.budget_allocations.get("mobile_app")
        if not mobile_alloc or mobile_alloc.budget <= 0:
            return {"channel": "mobile_app", "status": "no_budget"}

        try:
            channel_brief = self._create_channel_brief("mobile_app", mobile_alloc)
            crew = create_mobile_crew(self._client, channel_brief)
            result = crew.kickoff()

            recommendations = self._parse_recommendations(str(result), "mobile_app")
            self.state.channel_recommendations["mobile_app"] = recommendations
            self.state.updated_at = datetime.utcnow()

            return {"channel": "mobile_app", "status": "success", "count": len(recommendations)}

        except Exception as e:
            self.state.errors.append(f"Mobile research failed: {e}")
            return {"channel": "mobile_app", "status": "failed", "error": str(e)}

    @listen(allocate_budget)
    def research_performance(self, allocation_result: dict[str, Any]) -> dict[str, Any]:
        """Performance specialist researches remarketing inventory."""
        if allocation_result.get("status") != "success":
            return {"channel": "performance", "status": "skipped"}

        perf_alloc = self.state.budget_allocations.get("performance")
        if not perf_alloc or perf_alloc.budget <= 0:
            return {"channel": "performance", "status": "no_budget"}

        try:
            channel_brief = self._create_channel_brief("performance", perf_alloc)
            crew = create_performance_crew(self._client, channel_brief)
            result = crew.kickoff()

            recommendations = self._parse_recommendations(str(result), "performance")
            self.state.channel_recommendations["performance"] = recommendations
            self.state.updated_at = datetime.utcnow()

            return {"channel": "performance", "status": "success", "count": len(recommendations)}

        except Exception as e:
            self.state.errors.append(f"Performance research failed: {e}")
            return {"channel": "performance", "status": "failed", "error": str(e)}

    def _create_channel_brief(
        self, channel: str, allocation: ChannelAllocation
    ) -> dict[str, Any]:
        """Create a channel-specific brief from campaign brief and allocation."""
        return ChannelBrief(
            channel=channel,
            budget=allocation.budget,
            start_date=self.state.campaign_brief.get("start_date", ""),
            end_date=self.state.campaign_brief.get("end_date", ""),
            target_audience=self.state.campaign_brief.get("target_audience", {}),
            objectives=self.state.campaign_brief.get("objectives", []),
            kpis=self.state.campaign_brief.get("kpis", {}),
        ).model_dump(by_alias=True)

    def _parse_recommendations(
        self, result_str: str, channel: str
    ) -> list[ProductRecommendation]:
        """Parse recommendations from crew result."""
        recommendations = []

        try:
            # Try to find JSON array in result
            start_idx = result_str.find("[")
            end_idx = result_str.rfind("]") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = result_str[start_idx:end_idx]
                items = json.loads(json_str)

                for item in items:
                    rec = ProductRecommendation(
                        product_id=item.get("product_id", "unknown"),
                        product_name=item.get("product_name", "Unknown Product"),
                        publisher=item.get("publisher", "Unknown"),
                        channel=channel,
                        format=item.get("format"),
                        impressions=item.get("impressions", 0),
                        cpm=item.get("cpm", 0),
                        cost=item.get("cost", 0),
                        rationale=item.get("rationale"),
                    )
                    recommendations.append(rec)
        except (json.JSONDecodeError, KeyError):
            # If parsing fails, create a placeholder recommendation
            pass

        return recommendations

    @listen(or_(research_branding, research_ctv, research_mobile, research_performance))
    def consolidate_recommendations(self, channel_result: dict[str, Any]) -> dict[str, Any]:
        """Consolidate all channel recommendations for approval."""
        # Check if all active channels have reported
        active_channels = [
            ch for ch, alloc in self.state.budget_allocations.items()
            if alloc.budget > 0
        ]
        completed_channels = list(self.state.channel_recommendations.keys())

        # Check if we're still waiting for channels
        pending = set(active_channels) - set(completed_channels)
        if pending:
            return {"status": "waiting", "pending": list(pending)}

        # All channels complete - consolidate
        self.state.pending_approvals = []

        for channel, recs in self.state.channel_recommendations.items():
            for rec in recs:
                rec.status = "pending_approval"
                self.state.pending_approvals.append(rec)

        self.state.execution_status = ExecutionStatus.AWAITING_APPROVAL
        self.state.updated_at = datetime.utcnow()

        return {
            "status": "ready_for_approval",
            "total_recommendations": len(self.state.pending_approvals),
            "by_channel": {
                ch: len(recs) for ch, recs in self.state.channel_recommendations.items()
            },
        }

    def approve_recommendations(self, approved_ids: list[str]) -> dict[str, Any]:
        """Approve specific recommendations for booking.

        This method is called externally (from CLI/API) after human review.

        Args:
            approved_ids: List of product IDs to approve for booking

        Returns:
            Status of the approval and next steps
        """
        approved_set = set(approved_ids)

        for rec in self.state.pending_approvals:
            if rec.product_id in approved_set:
                rec.status = "approved"
            else:
                rec.status = "rejected"

        self.state.execution_status = ExecutionStatus.EXECUTING_BOOKINGS
        self.state.updated_at = datetime.utcnow()

        return self._execute_bookings()

    def approve_all(self) -> dict[str, Any]:
        """Approve all pending recommendations.

        Returns:
            Status of the approval and booking execution
        """
        all_ids = [rec.product_id for rec in self.state.pending_approvals]
        return self.approve_recommendations(all_ids)

    def _execute_bookings(self) -> dict[str, Any]:
        """Execute bookings for all approved recommendations."""
        from ..models.flow_state import BookedLine

        approved = [
            rec for rec in self.state.pending_approvals
            if rec.status == "approved"
        ]

        if not approved:
            self.state.execution_status = ExecutionStatus.COMPLETED
            return {"status": "success", "booked": 0, "message": "No recommendations approved"}

        # In a full implementation, this would use the Execution Agent
        # to create orders and book lines. For now, we track the approvals.
        for rec in approved:
            booked = BookedLine(
                line_id=f"line_{rec.product_id}",
                order_id="order_pending",
                product_id=rec.product_id,
                product_name=rec.product_name,
                channel=rec.channel,
                impressions=rec.impressions,
                cost=rec.cost,
                booking_status="pending_execution",
                booked_at=datetime.utcnow(),
            )
            self.state.booked_lines.append(booked)

        self.state.execution_status = ExecutionStatus.COMPLETED
        self.state.updated_at = datetime.utcnow()

        return {
            "status": "success",
            "booked": len(self.state.booked_lines),
            "total_impressions": sum(b.impressions for b in self.state.booked_lines),
            "total_cost": sum(b.cost for b in self.state.booked_lines),
        }

    def get_status(self) -> dict[str, Any]:
        """Get current flow status.

        Returns:
            Current state summary
        """
        return {
            "execution_status": self.state.execution_status.value,
            "budget_allocations": {
                k: v.model_dump() for k, v in self.state.budget_allocations.items()
            },
            "recommendations_by_channel": {
                ch: len(recs) for ch, recs in self.state.channel_recommendations.items()
            },
            "pending_approvals": len(self.state.pending_approvals),
            "booked_lines": len(self.state.booked_lines),
            "errors": self.state.errors,
            "updated_at": self.state.updated_at.isoformat(),
        }
