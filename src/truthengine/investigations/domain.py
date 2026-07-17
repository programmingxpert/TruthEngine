"""Domain model for investigations."""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class InvestigationStatus(StrEnum):
    """Lifecycle states for an investigation."""

    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COLLECTING_SOURCES = "COLLECTING_SOURCES"
    ANALYZING = "ANALYZING"
    GENERATING_REPORT = "GENERATING_REPORT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class TimelineEvent:
    """An immutable audit log event representing a significant action during an investigation."""

    id: UUID
    investigation_id: UUID
    event_type: str
    message: str
    created_at: datetime
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Investigation:
    """A user request for TruthEngine to investigate a claim or question."""

    id: UUID
    query: str
    status: InvestigationStatus
    created_at: datetime
    updated_at: datetime

    def update_status(self, status: InvestigationStatus) -> "Investigation":
        """Return a new copy of the investigation with an updated status and timestamp."""
        from dataclasses import replace

        return replace(self, status=status, updated_at=datetime.now(UTC))


def normalize_query(query: str) -> str:
    """Normalize and validate an investigation query."""
    normalized_query = " ".join(query.strip().split())
    if not normalized_query:
        msg = "Investigation query must not be empty."
        raise ValueError(msg)
    if len(normalized_query) > 2_000:
        msg = "Investigation query must be 2,000 characters or fewer."
        raise ValueError(msg)
    return normalized_query


def create_investigation(query: str) -> Investigation:
    """Create a new investigation in the CREATED state."""
    now = datetime.now(UTC)
    return Investigation(
        id=uuid4(),
        query=normalize_query(query),
        status=InvestigationStatus.CREATED,
        created_at=now,
        updated_at=now,
    )
