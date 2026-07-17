"""Dependency injection declarations for candidate passage selections."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from truthengine.core.di import get_database_session
from truthengine.investigations.candidates.persistence import (
    SqlAlchemyCandidatePassageRepository,
    SqlAlchemyDocumentSegmentRepository,
)
from truthengine.investigations.candidates.repository import (
    CandidatePassageRepository,
    DocumentSegmentRepository,
)


def get_document_segment_repository(
    session: Annotated[Session, Depends(get_database_session)],
) -> DocumentSegmentRepository:
    """Resolve the document segment repository."""
    return SqlAlchemyDocumentSegmentRepository(session)


def get_candidate_passage_repository(
    session: Annotated[Session, Depends(get_database_session)],
) -> CandidatePassageRepository:
    """Resolve the candidate passage repository."""
    return SqlAlchemyCandidatePassageRepository(session)
