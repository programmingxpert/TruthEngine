"""Dependency injection declarations for the sources context."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from truthengine.core.di import get_database_session
from truthengine.sources.persistence import (
    SqlAlchemySourceRepository,
    SqlAlchemySourceSnapshotRepository,
)
from truthengine.sources.repository import SourceRepository, SourceSnapshotRepository
from truthengine.sources.service import SourceService


def get_source_repository(
    session: Annotated[Session, Depends(get_database_session)],
) -> SourceRepository:
    """Resolve the source repository."""
    return SqlAlchemySourceRepository(session)


def get_source_snapshot_repository(
    session: Annotated[Session, Depends(get_database_session)],
) -> SourceSnapshotRepository:
    """Resolve the source snapshot repository."""
    return SqlAlchemySourceSnapshotRepository(session)


def get_source_service(
    source_repo: Annotated[SourceRepository, Depends(get_source_repository)],
    snapshot_repo: Annotated[SourceSnapshotRepository, Depends(get_source_snapshot_repository)],
) -> SourceService:
    """Resolve the source service."""
    return SourceService(source_repo, snapshot_repo)
