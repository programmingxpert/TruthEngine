"""FastAPI dependencies for the investigations domain."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from truthengine.core.di import get_database_session, get_llm_provider, get_search_provider
from truthengine.investigations.candidates.dependencies import (
    get_candidate_passage_repository,
    get_document_segment_repository,
)
from truthengine.investigations.candidates.repository import (
    CandidatePassageRepository,
    DocumentSegmentRepository,
)
from truthengine.investigations.graphs.dependencies import (
    get_evidence_graph_repository,
)
from truthengine.investigations.graphs.repository import (
    EvidenceGraphRepository,
)
from truthengine.investigations.persistence import (
    SqlAlchemyInvestigationRepository,
    SqlAlchemyTimelineEventRepository,
)
from truthengine.investigations.planning.persistence import (
    SqlAlchemyInvestigationPlanRepository,
)
from truthengine.investigations.planning.repository import (
    InvestigationPlanRepository,
)
from truthengine.investigations.repository import (
    InvestigationRepository,
    TimelineEventRepository,
)
from truthengine.investigations.service import InvestigationService
from truthengine.llm.provider import LLMProvider
from truthengine.search.provider import SearchProvider
from truthengine.sources.dependencies import (
    get_source_repository,
    get_source_snapshot_repository,
)
from truthengine.sources.repository import SourceRepository, SourceSnapshotRepository


def get_investigation_repository(
    session: Annotated[Session, Depends(get_database_session)],
) -> InvestigationRepository:
    """Resolve the investigation repository for a request."""
    return SqlAlchemyInvestigationRepository(session)


def get_timeline_event_repository(
    session: Annotated[Session, Depends(get_database_session)],
) -> TimelineEventRepository:
    """Resolve the timeline event repository for a request."""
    return SqlAlchemyTimelineEventRepository(session)


def get_investigation_plan_repository(
    session: Annotated[Session, Depends(get_database_session)],
) -> InvestigationPlanRepository:
    """Resolve the investigation plan repository for a request."""
    return SqlAlchemyInvestigationPlanRepository(session)


def get_investigation_service(
    repository: Annotated[InvestigationRepository, Depends(get_investigation_repository)],
    timeline_repo: Annotated[TimelineEventRepository, Depends(get_timeline_event_repository)],
    plan_repo: Annotated[InvestigationPlanRepository, Depends(get_investigation_plan_repository)],
    graph_repo: Annotated[EvidenceGraphRepository, Depends(get_evidence_graph_repository)],
    snapshot_repo: Annotated[SourceSnapshotRepository, Depends(get_source_snapshot_repository)],
    source_repo: Annotated[SourceRepository, Depends(get_source_repository)],
    segment_repo: Annotated[DocumentSegmentRepository, Depends(get_document_segment_repository)],
    passage_repo: Annotated[CandidatePassageRepository, Depends(get_candidate_passage_repository)],
    search_provider: Annotated[SearchProvider, Depends(get_search_provider)],
    llm_provider: Annotated[LLMProvider | None, Depends(get_llm_provider)],
) -> InvestigationService:
    """Resolve the investigation application service for a request."""
    return InvestigationService(
        repository=repository,
        timeline_repository=timeline_repo,
        plan_repository=plan_repo,
        graph_repository=graph_repo,
        snapshot_repository=snapshot_repo,
        segment_repository=segment_repo,
        passage_repository=passage_repo,
        source_repository=source_repo,
    )


def get_providers(
    search_provider: Annotated[SearchProvider, Depends(get_search_provider)],
    llm_provider: Annotated[LLMProvider | None, Depends(get_llm_provider)],
) -> tuple[SearchProvider, LLMProvider | None]:
    """Resolve both providers as a tuple for use in workflow endpoints."""
    return search_provider, llm_provider
