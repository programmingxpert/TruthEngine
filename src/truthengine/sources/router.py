"""HTTP routes for sources and snapshots."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from truthengine.core.exception_handlers import AppError
from truthengine.sources.dependencies import get_source_service
from truthengine.sources.schemas import (
    IngestSourceRequest,
    SourceResponse,
    SourceSnapshotResponse,
)
from truthengine.sources.service import (
    SnapshotNotFoundError,
    SourceNotFoundError,
    SourceService,
)

sources_router = APIRouter(prefix="/sources", tags=["sources"])
snapshots_router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@sources_router.post(
    "/ingest",
    response_model=SourceSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_source_endpoint(
    request: IngestSourceRequest,
    service: Annotated[SourceService, Depends(get_source_service)],
) -> SourceSnapshotResponse:
    """Ingest a target URL, validating security bounds and deduplicating content."""
    try:
        snapshot = service.ingest(url=request.url)
    except ValueError as exc:
        raise AppError(
            code="invalid_request",
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    return SourceSnapshotResponse.from_domain(snapshot)


@sources_router.get("/{source_id}", response_model=SourceResponse)
def get_source_endpoint(
    source_id: UUID,
    service: Annotated[SourceService, Depends(get_source_service)],
) -> SourceResponse:
    """Retrieve canonical source publisher details by ID."""
    try:
        source = service.get_source(source_id)
    except SourceNotFoundError as exc:
        raise AppError(
            code="source_not_found",
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    return SourceResponse.from_domain(source)


@snapshots_router.get("/{snapshot_id}", response_model=SourceSnapshotResponse)
def get_snapshot_endpoint(
    snapshot_id: UUID,
    service: Annotated[SourceService, Depends(get_source_service)],
) -> SourceSnapshotResponse:
    """Retrieve an immutable versioned snapshot by ID."""
    try:
        snapshot = service.get_snapshot(snapshot_id)
    except SnapshotNotFoundError as exc:
        raise AppError(
            code="snapshot_not_found",
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    return SourceSnapshotResponse.from_domain(snapshot)
