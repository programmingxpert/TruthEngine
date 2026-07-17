"""Application service for investigation use cases."""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from truthengine.investigations.candidates.domain import (
    CandidatePassage,
    SelectionPolicy,
)
from truthengine.investigations.candidates.repository import (
    CandidatePassageRepository,
    DocumentSegmentRepository,
)
from truthengine.investigations.domain import (
    Investigation,
    InvestigationStatus,
    TimelineEvent,
    create_investigation,
)
from truthengine.investigations.graphs.domain import EvidenceGraph
from truthengine.investigations.graphs.repository import (
    EvidenceGraphRepository,
)
from truthengine.investigations.planning.domain import InvestigationPlan
from truthengine.investigations.planning.repository import (
    InvestigationPlanRepository,
)
from truthengine.investigations.repository import (
    InvestigationRepository,
    TimelineEventRepository,
)
from truthengine.sources.repository import SourceRepository, SourceSnapshotRepository

if TYPE_CHECKING:
    from truthengine.llm.provider import LLMProvider
    from truthengine.search.provider import SearchProvider

logger = logging.getLogger(__name__)


class InvestigationNotFoundError(Exception):
    """Raised when an investigation cannot be found."""

    def __init__(self, investigation_id: UUID) -> None:
        """Initialize the error for a missing investigation ID."""
        super().__init__(f"Investigation {investigation_id} was not found.")
        self.investigation_id = investigation_id


class InvestigationPlanNotFoundError(Exception):
    """Raised when an investigation plan cannot be found."""

    def __init__(self, investigation_id: UUID) -> None:
        """Initialize the error for a missing investigation plan ID."""
        super().__init__(f"Investigation plan for investigation {investigation_id} was not found.")
        self.investigation_id = investigation_id


class EvidenceGraphNotFoundError(Exception):
    """Raised when an evidence graph cannot be found."""

    def __init__(
        self,
        graph_id: UUID | None = None,
        investigation_id: UUID | None = None,
    ) -> None:
        """Initialize the error with either graph_id or investigation_id."""
        if graph_id is not None:
            super().__init__(f"Evidence graph {graph_id} was not found.")
        else:
            super().__init__(
                f"Latest evidence graph for investigation {investigation_id} was not found."
            )
        self.graph_id = graph_id
        self.investigation_id = investigation_id


class InvestigationService:
    """Coordinates investigation application use cases."""

    def __init__(
        self,
        repository: InvestigationRepository,
        timeline_repository: TimelineEventRepository,
        plan_repository: InvestigationPlanRepository,
        graph_repository: EvidenceGraphRepository,
        snapshot_repository: SourceSnapshotRepository,
        segment_repository: DocumentSegmentRepository,
        passage_repository: CandidatePassageRepository,
        source_repository: SourceRepository | None = None,
    ) -> None:
        """Initialize the service with repositories."""
        self._repository = repository
        self._timeline_repository = timeline_repository
        self._plan_repository = plan_repository
        self._graph_repository = graph_repository
        self._snapshot_repository = snapshot_repository
        self._segment_repository = segment_repository
        self._passage_repository = passage_repository
        self._source_repository = source_repository

    def create(self, *, query: str) -> Investigation:
        """Create and persist a new investigation."""
        investigation = create_investigation(query)
        self._repository.add(investigation)
        logger.info(
            "Investigation created",
            extra={
                "investigation_id": str(investigation.id),
                "status": investigation.status.value,
            },
        )
        return investigation

    def get(self, *, investigation_id: UUID) -> Investigation:
        """Return investigation metadata by ID."""
        investigation = self._repository.get_by_id(investigation_id)
        if investigation is None:
            raise InvestigationNotFoundError(investigation_id)
        return investigation

    def list_all(self) -> list[Investigation]:
        """Return all investigations ordered by creation date, newest first."""
        return self._repository.get_all()

    def delete(self, *, investigation_id: UUID) -> None:
        """Delete an investigation by its ID."""
        # Ensure it exists first, otherwise throws
        _ = self.get(investigation_id=investigation_id)
        self._repository.delete(investigation_id)
        logger.info(
            "Investigation deleted",
            extra={"investigation_id": str(investigation_id)},
        )

    def update_status(
        self, *, investigation_id: UUID, status: InvestigationStatus
    ) -> Investigation:
        """Update the status of an existing investigation."""
        investigation = self.get(investigation_id=investigation_id)
        updated_investigation = investigation.update_status(status)
        self._repository.update(updated_investigation)
        logger.info(
            "Investigation status updated",
            extra={
                "investigation_id": str(investigation.id),
                "old_status": investigation.status.value,
                "new_status": status.value,
            },
        )
        return updated_investigation

    def queue_workflow(self, *, investigation_id: UUID) -> Investigation:
        """Mark an investigation as queued and record a timeline checkpoint."""
        investigation = self.get(investigation_id=investigation_id)
        updated_investigation = investigation.update_status(InvestigationStatus.QUEUED)
        self._repository.update(updated_investigation)
        self._timeline_repository.add(
            TimelineEvent(
                id=uuid4(),
                investigation_id=investigation_id,
                event_type="WORKFLOW_QUEUED",
                message="Investigation workflow queued for background execution.",
                created_at=datetime.now(UTC),
                metadata={
                    "old_status": investigation.status.value,
                    "new_status": InvestigationStatus.QUEUED.value,
                },
            )
        )
        logger.info(
            "Investigation workflow queued",
            extra={"investigation_id": str(investigation_id)},
        )
        return updated_investigation

    def run_workflow(
        self,
        *,
        investigation_id: UUID,
        search_provider: "SearchProvider | None" = None,
        llm_provider: "LLMProvider | None" = None,
    ) -> Investigation:
        """Start or resume the investigation workflow synchronously."""
        from truthengine.investigations.workflow import InvestigationWorkflowOrchestrator

        orchestrator = InvestigationWorkflowOrchestrator(
            investigation_repo=self._repository,
            timeline_repo=self._timeline_repository,
            plan_repo=self._plan_repository,
            graph_repo=self._graph_repository,
            snapshot_repo=self._snapshot_repository,
            segment_repo=self._segment_repository,
            passage_repo=self._passage_repository,
            source_repo=self._source_repository,
            search_provider=search_provider,
            llm_provider=llm_provider,
        )
        return orchestrator.run(investigation_id)

    def get_timeline(self, *, investigation_id: UUID) -> list[TimelineEvent]:
        """Return all timeline events for a given investigation."""
        # Ensure investigation exists first
        _ = self.get(investigation_id=investigation_id)
        return self._timeline_repository.get_by_investigation_id(investigation_id)

    def generate_plan(self, *, investigation_id: UUID) -> InvestigationPlan:
        """Generate and persist an investigation plan for the given query."""
        # Ensure investigation exists
        investigation = self.get(investigation_id=investigation_id)

        # Check if plan already exists
        existing_plan = self._plan_repository.get_by_investigation_id(investigation_id)
        if existing_plan is not None:
            return existing_plan

        from truthengine.investigations.planning.planner import (
            InvestigationPlanner,
        )

        planner = InvestigationPlanner()
        plan = planner.plan(investigation_id=investigation_id, query=investigation.query)
        self._plan_repository.add(plan)
        logger.info(
            "Investigation plan generated",
            extra={
                "investigation_id": str(investigation_id),
                "domain": plan.detected_domain,
            },
        )
        return plan

    def get_plan(self, *, investigation_id: UUID) -> InvestigationPlan:
        """Get the persisted investigation plan or generate one on-the-fly."""
        # Ensure investigation exists first
        _ = self.get(investigation_id=investigation_id)

        plan = self._plan_repository.get_by_investigation_id(investigation_id)
        if plan is None:
            return self.generate_plan(investigation_id=investigation_id)
        return plan

    def create_initial_graph(self, *, investigation_id: UUID) -> EvidenceGraph:
        """Create version 1 of the evidence graph (empty graph) for the investigation."""
        from datetime import UTC, datetime
        from uuid import uuid4

        # Ensure investigation exists
        _ = self.get(investigation_id=investigation_id)

        # Check if version 1 already exists
        existing = self._graph_repository.get_latest_by_investigation_id(investigation_id)
        if existing is not None and existing.version >= 1:
            return existing

        graph = EvidenceGraph(
            id=uuid4(),
            investigation_id=investigation_id,
            version=1,
            created_at=datetime.now(UTC),
            claims=[],
            evidence_items=[],
            relations=[],
        )
        self._graph_repository.add(graph)
        logger.info(
            "Initial evidence graph (v1) created",
            extra={
                "investigation_id": str(investigation_id),
                "graph_id": str(graph.id),
            },
        )
        return graph

    def get_latest_graph(self, *, investigation_id: UUID) -> EvidenceGraph:
        """Return the latest version of the evidence graph, or create a default v1 graph if none exists."""
        # Ensure investigation exists
        _ = self.get(investigation_id=investigation_id)

        graph = self._graph_repository.get_latest_by_investigation_id(investigation_id)
        if graph is None:
            return self.create_initial_graph(investigation_id=investigation_id)
        return graph

    def get_graph(self, *, graph_id: UUID) -> EvidenceGraph:
        """Return the evidence graph by its specific ID. Raises error if not found."""
        graph = self._graph_repository.get_by_id(graph_id)
        if graph is None:
            raise EvidenceGraphNotFoundError(graph_id=graph_id)
        return graph

    def select_candidate_passages(
        self, *, investigation_id: UUID, policy: SelectionPolicy | None = None
    ) -> list[CandidatePassage]:
        """Normalize, segment, rank, and persist candidate passages matching query constraints."""
        from truthengine.investigations.candidates.selector import (
            rank_and_select_passages,
            segment_snapshot,
        )
        from truthengine.investigations.planning.profiles import (
            EducationProfile,
            GeneralProfile,
            TechnologyProfile,
        )

        if policy is None:
            policy = SelectionPolicy()

        # 1. Ensure investigation exists
        investigation = self.get(investigation_id=investigation_id)

        # 2. Ensure plan exists
        plan = self.get_plan(investigation_id=investigation_id)

        # 3. Resolve profile matching plan domain
        from truthengine.investigations.planning.domain import DomainProfile

        domain_lower = plan.detected_domain.lower()
        profile: DomainProfile
        if "technology" in domain_lower or "programming" in domain_lower:
            profile = TechnologyProfile()
        elif "education" in domain_lower:
            profile = EducationProfile()
        else:
            profile = GeneralProfile()

        # 4. Fetch all snapshots in the DB
        snapshots = self._snapshot_repository.get_all()
        if not snapshots:
            logger.info("No snapshots found in system to select candidates from")
            return []

        selected_passages: list[CandidatePassage] = []

        for snapshot in snapshots:
            # Check if this snapshot is already segmented in DB
            segments = self._segment_repository.get_by_snapshot_id(snapshot.id)
            if not segments:
                # Segment it on-demand
                segments = segment_snapshot(
                    snapshot.id, snapshot.extracted_text, default_heading=snapshot.title
                )
                self._segment_repository.add_all(segments)

            # Rank and select passages from these segments
            passages = rank_and_select_passages(
                investigation_id=investigation_id,
                query=investigation.query,
                segments=segments,
                snapshot_version=snapshot.snapshot_version,
                policy=policy,
                profile=profile,
            )
            selected_passages.extend(passages)

        # Apply final global policy sort and limit across all parsed snapshots
        selected_passages.sort(
            key=lambda p: float(p.selection_explanation["lexical_score"]),
            reverse=True,
        )
        final_passages = selected_passages[: policy.max_returned_passages]

        # Persist selected passages
        self._passage_repository.add_all(final_passages)
        logger.info(
            "Selected and persisted candidate passages",
            extra={
                "investigation_id": str(investigation_id),
                "count": len(final_passages),
            },
        )
        return final_passages

    def get_candidate_passages(self, *, investigation_id: UUID) -> list[CandidatePassage]:
        """Retrieve previously persisted candidate passages selected for an investigation."""
        # Ensure investigation exists first
        _ = self.get(investigation_id=investigation_id)
        return self._passage_repository.get_by_investigation_id(investigation_id)
