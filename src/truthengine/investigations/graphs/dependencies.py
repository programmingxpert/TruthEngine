"""FastAPI dependencies for the evidence graph storage layer."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from truthengine.core.di import get_database_session
from truthengine.investigations.graphs.persistence import SqlAlchemyEvidenceGraphRepository
from truthengine.investigations.graphs.repository import EvidenceGraphRepository


def get_evidence_graph_repository(
    session: Annotated[Session, Depends(get_database_session)],
) -> EvidenceGraphRepository:
    """Resolve the evidence graph repository for a request."""
    return SqlAlchemyEvidenceGraphRepository(session)
