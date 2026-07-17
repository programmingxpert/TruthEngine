"""Repository interface for persisting investigation plans."""

from abc import ABC, abstractmethod
from uuid import UUID

from truthengine.investigations.planning.domain import InvestigationPlan


class InvestigationPlanRepository(ABC):
    """Persistence boundary for investigation plans."""

    @abstractmethod
    def add(self, plan: InvestigationPlan) -> None:
        """Persist a new investigation plan."""

    @abstractmethod
    def get_by_investigation_id(self, investigation_id: UUID) -> InvestigationPlan | None:
        """Return the plan for a given investigation, if it exists."""
