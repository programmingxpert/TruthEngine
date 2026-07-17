"""SQLAlchemy persistence implementation for investigations."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column

from truthengine.core.database import Base
from truthengine.investigations.domain import Investigation, InvestigationStatus, TimelineEvent
from truthengine.investigations.repository import (
    InvestigationRepository,
    TimelineEventRepository,
)


class InvestigationRecord(Base):
    """SQLAlchemy ORM record for the investigations table."""

    __tablename__ = "investigations"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(length=32), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    @classmethod
    def from_domain(cls, investigation: Investigation) -> "InvestigationRecord":
        """Create a persistence record from a domain investigation."""
        return cls(
            id=investigation.id,
            query=investigation.query,
            status=investigation.status.value,
            created_at=investigation.created_at,
            updated_at=investigation.updated_at,
        )

    def to_domain(self) -> Investigation:
        """Convert a persistence record to a domain investigation."""
        return Investigation(
            id=self.id,
            query=self.query,
            status=InvestigationStatus(self.status),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class SqlAlchemyInvestigationRepository(InvestigationRepository):
    """SQLAlchemy-backed implementation of the investigation repository."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a request-scoped database session."""
        self._session = session

    def add(self, investigation: Investigation) -> None:
        """Persist a new investigation."""
        self._session.add(InvestigationRecord.from_domain(investigation))
        self._session.flush()

    def get_by_id(self, investigation_id: UUID) -> Investigation | None:
        """Return an investigation by ID, if it exists."""
        record = self._session.get(InvestigationRecord, investigation_id)
        if record is None:
            return None
        return record.to_domain()

    def get_all(self) -> list[Investigation]:
        """Return all investigations, ordered by created_at descending."""
        records = (
            self._session.query(InvestigationRecord)
            .order_by(InvestigationRecord.created_at.desc())
            .all()
        )
        return [record.to_domain() for record in records]

    def update(self, investigation: Investigation) -> None:
        """Update an existing investigation."""
        record = self._session.get(InvestigationRecord, investigation.id)
        if record is None:
            msg = f"Investigation record {investigation.id} not found."
            raise ValueError(msg)
        record.status = investigation.status.value
        record.updated_at = investigation.updated_at
        self._session.flush()

    def delete(self, investigation_id: UUID) -> None:
        """Delete an investigation by UUID."""
        record = self._session.get(InvestigationRecord, investigation_id)
        if record is not None:
            self._session.delete(record)
            self._session.flush()


class TimelineEventRecord(Base):
    """SQLAlchemy ORM record for the investigation_timeline_events table."""

    __tablename__ = "investigation_timeline_events"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    investigation_id: Mapped[UUID] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(length=64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)

    @classmethod
    def from_domain(cls, event: TimelineEvent) -> "TimelineEventRecord":
        """Create a persistence record from a domain timeline event."""
        return cls(
            id=event.id,
            investigation_id=event.investigation_id,
            event_type=event.event_type,
            message=event.message,
            created_at=event.created_at,
            payload=event.metadata,
        )

    def to_domain(self) -> TimelineEvent:
        """Convert a persistence record to a domain timeline event."""
        return TimelineEvent(
            id=self.id,
            investigation_id=self.investigation_id,
            event_type=self.event_type,
            message=self.message,
            created_at=self.created_at,
            metadata=self.payload,
        )


class SqlAlchemyTimelineEventRepository(TimelineEventRepository):
    """SQLAlchemy-backed implementation of the timeline event repository."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a request-scoped database session."""
        self._session = session

    def add(self, event: TimelineEvent) -> None:
        """Persist a new timeline event."""
        self._session.add(TimelineEventRecord.from_domain(event))
        self._session.flush()

    def get_by_investigation_id(self, investigation_id: UUID) -> list[TimelineEvent]:
        """Return all timeline events for a given investigation, ordered by created_at."""
        records = (
            self._session.query(TimelineEventRecord)
            .filter(TimelineEventRecord.investigation_id == investigation_id)
            .order_by(TimelineEventRecord.created_at.asc())
            .all()
        )
        return [record.to_domain() for record in records]
