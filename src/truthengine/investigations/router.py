"""HTTP routes for investigation metadata."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from truthengine.core.di import AppContainer, get_container, get_database_session
from truthengine.core.exception_handlers import AppError
from truthengine.investigations.background import run_investigation_workflow
from truthengine.investigations.dependencies import get_investigation_service
from truthengine.investigations.domain import InvestigationStatus
from truthengine.investigations.schemas import (
    CandidatePassageResponse,
    CreateInvestigationRequest,
    CreateInvestigationResponse,
    EvidenceGraphResponse,
    InvestigationMetadataResponse,
    InvestigationPlanResponse,
    TimelineEventResponse,
)
from truthengine.investigations.service import (
    EvidenceGraphNotFoundError,
    InvestigationNotFoundError,
    InvestigationPlanNotFoundError,
    InvestigationService,
)

router = APIRouter(prefix="/investigations", tags=["investigations"])
graphs_router = APIRouter(prefix="/graphs", tags=["graphs"])


@router.get("", response_model=list[InvestigationMetadataResponse])
def list_investigations_endpoint(
    service: Annotated[InvestigationService, Depends(get_investigation_service)],
) -> list[InvestigationMetadataResponse]:
    """Return a list of all investigations for the dashboard."""
    investigations = service.list_all()
    return [InvestigationMetadataResponse.from_domain(inv) for inv in investigations]


@router.post(
    "",
    response_model=CreateInvestigationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_investigation_endpoint(
    request: CreateInvestigationRequest,
    service: Annotated[InvestigationService, Depends(get_investigation_service)],
) -> CreateInvestigationResponse:
    """Create a new investigation."""
    investigation = service.create(query=request.query)
    return CreateInvestigationResponse.from_domain(investigation)


@router.get("/{investigation_id}", response_model=InvestigationMetadataResponse)
def get_investigation_endpoint(
    investigation_id: UUID,
    service: Annotated[InvestigationService, Depends(get_investigation_service)],
) -> InvestigationMetadataResponse:
    """Return metadata for a single investigation."""
    try:
        investigation = service.get(investigation_id=investigation_id)
    except InvestigationNotFoundError as exc:
        raise AppError(
            code="investigation_not_found",
            message="Investigation was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    return InvestigationMetadataResponse.from_domain(investigation)


@router.delete("/{investigation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investigation_endpoint(
    investigation_id: UUID,
    service: Annotated[InvestigationService, Depends(get_investigation_service)],
) -> None:
    """Delete an investigation and all its associated timeline, graph, and plan data."""
    try:
        service.delete(investigation_id=investigation_id)
    except InvestigationNotFoundError as exc:
        raise AppError(
            code="investigation_not_found",
            message="Investigation was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc


@router.post("/{investigation_id}/run", response_model=InvestigationMetadataResponse)
def run_investigation_endpoint(
    investigation_id: UUID,
    background_tasks: BackgroundTasks,
    session: Annotated[Session, Depends(get_database_session)],
    service: Annotated[InvestigationService, Depends(get_investigation_service)],
    container: Annotated[AppContainer, Depends(get_container)],
) -> InvestigationMetadataResponse:
    """Queue the execution pipeline for an investigation, commit request changes early to avoid deadlocks, and return immediately."""
    try:
        investigation = service.get(investigation_id=investigation_id)
        if investigation.status in {
            InvestigationStatus.CREATED,
            InvestigationStatus.FAILED,
            InvestigationStatus.CANCELLED,
        }:
            investigation = service.queue_workflow(investigation_id=investigation_id)
            session.commit()  # Release row lock immediately so background runner doesn't deadlock
            background_tasks.add_task(run_investigation_workflow, container, investigation_id)
    except InvestigationNotFoundError as exc:
        raise AppError(
            code="investigation_not_found",
            message="Investigation was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    return InvestigationMetadataResponse.from_domain(investigation)


@router.get("/{investigation_id}/timeline", response_model=list[TimelineEventResponse])
def get_investigation_timeline_endpoint(
    investigation_id: UUID,
    service: Annotated[InvestigationService, Depends(get_investigation_service)],
) -> list[TimelineEventResponse]:
    """Return all timeline events for a single investigation."""
    try:
        events = service.get_timeline(investigation_id=investigation_id)
    except InvestigationNotFoundError as exc:
        raise AppError(
            code="investigation_not_found",
            message="Investigation was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    return [TimelineEventResponse.from_domain(event) for event in events]


@router.post("/{investigation_id}/plan", response_model=InvestigationPlanResponse)
def generate_investigation_plan_endpoint(
    investigation_id: UUID,
    service: Annotated[InvestigationService, Depends(get_investigation_service)],
) -> InvestigationPlanResponse:
    """Generate and persist an investigation plan for the given investigation."""
    try:
        plan = service.generate_plan(investigation_id=investigation_id)
    except InvestigationNotFoundError as exc:
        raise AppError(
            code="investigation_not_found",
            message="Investigation was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    return InvestigationPlanResponse.from_domain(plan)


@router.get("/{investigation_id}/plan", response_model=InvestigationPlanResponse)
def get_investigation_plan_endpoint(
    investigation_id: UUID,
    service: Annotated[InvestigationService, Depends(get_investigation_service)],
) -> InvestigationPlanResponse:
    """Retrieve the investigation plan for a given investigation."""
    try:
        plan = service.get_plan(investigation_id=investigation_id)
    except InvestigationNotFoundError as exc:
        raise AppError(
            code="investigation_not_found",
            message="Investigation was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    except InvestigationPlanNotFoundError as exc:
        raise AppError(
            code="investigation_plan_not_found",
            message="Investigation plan was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    return InvestigationPlanResponse.from_domain(plan)


@router.post(
    "/{investigation_id}/graphs",
    response_model=EvidenceGraphResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_initial_graph_endpoint(
    investigation_id: UUID,
    service: Annotated[InvestigationService, Depends(get_investigation_service)],
) -> EvidenceGraphResponse:
    """Create version 1 (empty graph) for the investigation."""
    try:
        graph = service.create_initial_graph(investigation_id=investigation_id)
    except InvestigationNotFoundError as exc:
        raise AppError(
            code="investigation_not_found",
            message="Investigation was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    return EvidenceGraphResponse.from_domain(graph)


@router.get("/{investigation_id}/graphs/latest", response_model=EvidenceGraphResponse)
def get_latest_graph_endpoint(
    investigation_id: UUID,
    service: Annotated[InvestigationService, Depends(get_investigation_service)],
) -> EvidenceGraphResponse:
    """Return the latest version of the evidence graph."""
    try:
        graph = service.get_latest_graph(investigation_id=investigation_id)
    except InvestigationNotFoundError as exc:
        raise AppError(
            code="investigation_not_found",
            message="Investigation was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    except EvidenceGraphNotFoundError as exc:
        raise AppError(
            code="evidence_graph_not_found",
            message="Evidence graph was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    return EvidenceGraphResponse.from_domain(graph)


@graphs_router.get("/{graph_id}", response_model=EvidenceGraphResponse)
def get_graph_endpoint(
    graph_id: UUID,
    service: Annotated[InvestigationService, Depends(get_investigation_service)],
) -> EvidenceGraphResponse:
    """Retrieve the full evidence graph by its specific ID."""
    try:
        graph = service.get_graph(graph_id=graph_id)
    except EvidenceGraphNotFoundError as exc:
        raise AppError(
            code="evidence_graph_not_found",
            message="Evidence graph was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    return EvidenceGraphResponse.from_domain(graph)


@router.post("/{investigation_id}/candidates", response_model=list[CandidatePassageResponse])
def select_candidate_passages_endpoint(
    investigation_id: UUID,
    service: Annotated[InvestigationService, Depends(get_investigation_service)],
) -> list[CandidatePassageResponse]:
    """Segment, rank, and select candidate passages for an investigation."""
    try:
        passages = service.select_candidate_passages(investigation_id=investigation_id)
    except InvestigationNotFoundError as exc:
        raise AppError(
            code="investigation_not_found",
            message="Investigation was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    except InvestigationPlanNotFoundError as exc:
        raise AppError(
            code="investigation_plan_not_found",
            message="Investigation plan was not found. Please generate a plan first.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    return [CandidatePassageResponse.from_domain(p) for p in passages]


@router.get("/{investigation_id}/candidates", response_model=list[CandidatePassageResponse])
def get_candidate_passages_endpoint(
    investigation_id: UUID,
    service: Annotated[InvestigationService, Depends(get_investigation_service)],
) -> list[CandidatePassageResponse]:
    """Retrieve persisted candidate passages selected for an investigation."""
    try:
        passages = service.get_candidate_passages(investigation_id=investigation_id)
    except InvestigationNotFoundError as exc:
        raise AppError(
            code="investigation_not_found",
            message="Investigation was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    return [CandidatePassageResponse.from_domain(p) for p in passages]
