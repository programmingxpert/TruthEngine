"""Deterministic planner executing registered planning rules on queries."""

from datetime import UTC, datetime
from uuid import UUID

from truthengine.investigations.planning.domain import DomainProfile, InvestigationPlan
from truthengine.investigations.planning.profiles import (
    EducationProfile,
    GeneralProfile,
    TechnologyProfile,
)


class InvestigationPlanner:
    """Deterministic Planner that classifies queries and generates InvestigationPlans."""

    def __init__(self, profiles: list[DomainProfile] | None = None) -> None:
        """Initialize the planner with registered profiles, falling back to default set."""
        if profiles is not None:
            self._profiles = list(profiles)
        else:
            self._profiles = [
                EducationProfile(),
                TechnologyProfile(),
                GeneralProfile(),
            ]

    def plan(self, *, investigation_id: UUID, query: str) -> InvestigationPlan:
        """Analyze a query and output a structured, deterministic InvestigationPlan."""
        # 1. Select the matching profile
        profile = self._select_profile(query)

        # 2. Generate specific details
        details = profile.generate_plan_details(query)

        # 3. Build plan dataclass
        return InvestigationPlan(
            investigation_id=investigation_id,
            detected_domain=profile.name,
            objective=details["objective"],
            assumptions=details["assumptions"],
            required_evidence_categories=details["required_evidence_categories"],
            preferred_source_categories=profile.preferred_source_categories,
            excluded_source_categories=profile.excluded_source_categories,
            retrieval_strategy=details["retrieval_strategy"],
            success_criteria=profile.success_criteria_templates,
            limitations=details["limitations"],
            planning_timestamp=datetime.now(UTC),
            planner_version="1.0.0",
        )

    def _select_profile(self, query: str) -> DomainProfile:
        """Select the first matching profile. Fallback to GeneralProfile."""
        for profile in self._profiles:
            if profile.name != "General" and profile.matches(query):
                return profile
        for profile in self._profiles:
            if profile.name == "General":
                return profile
        msg = "No General fallback profile registered in planner."
        raise ValueError(msg)
