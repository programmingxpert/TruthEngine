"""SQLAlchemy implementation of the planner persistence layer."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column

from truthengine.core.database import Base
from truthengine.investigations.planning.domain import InvestigationPlan
from truthengine.investigations.planning.repository import InvestigationPlanRepository


class InvestigationPlanRecord(Base):
    """SQLAlchemy ORM record for the investigation_plans table."""

    __tablename__ = "investigation_plans"

    investigation_id: Mapped[UUID] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), primary_key=True
    )
    detected_domain: Mapped[str] = mapped_column(String(length=64), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    assumptions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    required_evidence_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    preferred_source_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    excluded_source_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    retrieval_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    success_criteria: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    limitations: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    planning_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planner_version: Mapped[str] = mapped_column(String(length=32), nullable=False)

    @classmethod
    def from_domain(cls, plan: InvestigationPlan) -> "InvestigationPlanRecord":
        """Create a persistence record from a domain plan."""
        return cls(
            investigation_id=plan.investigation_id,
            detected_domain=plan.detected_domain,
            objective=plan.objective,
            assumptions=plan.assumptions,
            required_evidence_categories=plan.required_evidence_categories,
            preferred_source_categories=plan.preferred_source_categories,
            excluded_source_categories=plan.excluded_source_categories,
            retrieval_strategy=plan.retrieval_strategy,
            success_criteria=plan.success_criteria,
            limitations=plan.limitations,
            planning_timestamp=plan.planning_timestamp,
            planner_version=plan.planner_version,
        )

    def to_domain(self) -> InvestigationPlan:
        """Convert a persistence record to a domain plan."""
        return InvestigationPlan(
            investigation_id=self.investigation_id,
            detected_domain=self.detected_domain,
            objective=self.objective,
            assumptions=self.assumptions,
            required_evidence_categories=self.required_evidence_categories,
            preferred_source_categories=self.preferred_source_categories,
            excluded_source_categories=self.excluded_source_categories,
            retrieval_strategy=self.retrieval_strategy,
            success_criteria=self.success_criteria,
            limitations=self.limitations,
            planning_timestamp=self.planning_timestamp,
            planner_version=self.planner_version,
        )


class SqlAlchemyInvestigationPlanRepository(InvestigationPlanRepository):
    """SQLAlchemy-backed implementation of the investigation plan repository."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a request-scoped database session."""
        self._session = session

    def add(self, plan: InvestigationPlan) -> None:
        """Persist a new investigation plan."""
        self._session.add(InvestigationPlanRecord.from_domain(plan))
        self._session.flush()

    def get_by_investigation_id(self, investigation_id: UUID) -> InvestigationPlan | None:
        """Return the plan for a given investigation, if it exists."""
        record = self._session.get(InvestigationPlanRecord, investigation_id)
        if record is None:
            return None
        return record.to_domain()
