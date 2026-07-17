"""SQLAlchemy models and repositories for document segments and passages."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from truthengine.core.database import Base
from truthengine.investigations.candidates.domain import (
    CandidatePassage,
    DocumentSegment,
)
from truthengine.investigations.candidates.repository import (
    CandidatePassageRepository,
    DocumentSegmentRepository,
)


class DocumentSegmentRecord(Base):
    """SQLAlchemy ORM record for the document_segments table."""

    __tablename__ = "document_segments"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str | None] = mapped_column(String(256), nullable=True)
    heading_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    paragraph_order: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_section: Mapped[str | None] = mapped_column(String(256), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    character_range_start: Mapped[int] = mapped_column(Integer, nullable=False)
    character_range_end: Mapped[int] = mapped_column(Integer, nullable=False)
    token_estimate: Mapped[int] = mapped_column(Integer, nullable=False)

    passages: Mapped[list["CandidatePassageRecord"]] = relationship(
        "CandidatePassageRecord",
        back_populates="segment",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @classmethod
    def from_domain(cls, segment: DocumentSegment) -> "DocumentSegmentRecord":
        """Build ORM record from domain segment."""
        return cls(
            id=segment.id,
            snapshot_id=segment.snapshot_id,
            order=segment.order,
            heading=segment.heading,
            heading_level=segment.heading_level,
            paragraph_order=segment.paragraph_order,
            parent_section=segment.parent_section,
            content=segment.content,
            character_range_start=segment.character_range_start,
            character_range_end=segment.character_range_end,
            token_estimate=segment.token_estimate,
        )

    def to_domain(self) -> DocumentSegment:
        """Convert ORM record to domain segment."""
        return DocumentSegment(
            id=self.id,
            snapshot_id=self.snapshot_id,
            order=self.order,
            heading=self.heading,
            heading_level=self.heading_level,
            paragraph_order=self.paragraph_order,
            parent_section=self.parent_section,
            content=self.content,
            character_range_start=self.character_range_start,
            character_range_end=self.character_range_end,
            token_estimate=self.token_estimate,
        )


class CandidatePassageRecord(Base):
    """SQLAlchemy ORM record for the candidate_passages table."""

    __tablename__ = "candidate_passages"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    investigation_id: Mapped[UUID] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_segments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_version: Mapped[int] = mapped_column(Integer, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(64), nullable=False)
    paragraph_order: Mapped[int] = mapped_column(Integer, nullable=False)
    selection_explanation: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    selected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    segment: Mapped[DocumentSegmentRecord] = relationship(
        "DocumentSegmentRecord", back_populates="passages"
    )

    @classmethod
    def from_domain(cls, passage: CandidatePassage) -> "CandidatePassageRecord":
        """Build ORM record from domain passage."""
        return cls(
            id=passage.id,
            investigation_id=passage.investigation_id,
            segment_id=passage.segment_id,
            snapshot_version=passage.snapshot_version,
            algorithm_version=passage.algorithm_version,
            paragraph_order=passage.paragraph_order,
            selection_explanation=passage.selection_explanation,
            selected_at=passage.selected_at,
        )

    def to_domain(self) -> CandidatePassage:
        """Convert ORM record to domain passage."""
        return CandidatePassage(
            id=self.id,
            investigation_id=self.investigation_id,
            segment_id=self.segment_id,
            snapshot_version=self.snapshot_version,
            algorithm_version=self.algorithm_version,
            paragraph_order=self.paragraph_order,
            selection_explanation=self.selection_explanation,
            selected_at=self.selected_at,
        )


class SqlAlchemyDocumentSegmentRepository(DocumentSegmentRepository):
    """SQLAlchemy-backed implementation of the document segment repository."""

    def __init__(self, session: Session) -> None:
        """Initialize with database session."""
        self._session = session

    def add_all(self, segments: list[DocumentSegment]) -> None:
        """Persist a list of document segments."""
        for seg in segments:
            self._session.add(DocumentSegmentRecord.from_domain(seg))
        self._session.flush()

    def get_by_id(self, segment_id: UUID) -> DocumentSegment | None:
        """Retrieve a single segment by its UUID."""
        record = self._session.get(DocumentSegmentRecord, segment_id)
        if record is None:
            return None
        return record.to_domain()

    def get_by_snapshot_id(self, snapshot_id: UUID) -> list[DocumentSegment]:
        """Retrieve all segments parsed for a specific snapshot."""
        records = (
            self._session.query(DocumentSegmentRecord)
            .filter(DocumentSegmentRecord.snapshot_id == snapshot_id)
            .order_by(DocumentSegmentRecord.order.asc())
            .all()
        )
        return [rec.to_domain() for rec in records]


class SqlAlchemyCandidatePassageRepository(CandidatePassageRepository):
    """SQLAlchemy-backed implementation of the candidate passage repository."""

    def __init__(self, session: Session) -> None:
        """Initialize with database session."""
        self._session = session

    def add_all(self, passages: list[CandidatePassage]) -> None:
        """Persist a list of selected passages."""
        for passage in passages:
            self._session.add(CandidatePassageRecord.from_domain(passage))
        self._session.flush()

    def get_by_investigation_id(self, investigation_id: UUID) -> list[CandidatePassage]:
        """Retrieve all candidate passages selected for an investigation."""
        records = (
            self._session.query(CandidatePassageRecord)
            .filter(CandidatePassageRecord.investigation_id == investigation_id)
            .order_by(CandidatePassageRecord.selected_at.desc())
            .all()
        )
        return [rec.to_domain() for rec in records]

    def get_by_segment_id(self, segment_id: UUID) -> list[CandidatePassage]:
        """Retrieve all candidate passages referring to a specific segment."""
        records = (
            self._session.query(CandidatePassageRecord)
            .filter(CandidatePassageRecord.segment_id == segment_id)
            .all()
        )
        return [rec.to_domain() for rec in records]
