"""SQLAlchemy models and repositories for sources and snapshots."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from truthengine.core.database import Base
from truthengine.sources.domain import Source, SourceCategory, SourceSnapshot
from truthengine.sources.repository import SourceRepository, SourceSnapshotRepository


class SourceRecord(Base):
    """SQLAlchemy ORM record for the sources table."""

    __tablename__ = "sources"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    domain: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    source_category: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    snapshots: Mapped[list["SourceSnapshotRecord"]] = relationship(
        "SourceSnapshotRecord",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @classmethod
    def from_domain(cls, domain_obj: Source) -> "SourceRecord":
        """Build ORM record from domain source."""
        return cls(
            id=domain_obj.id,
            domain=domain_obj.domain,
            source_category=domain_obj.source_category.value,
            created_at=domain_obj.created_at,
        )

    def to_domain(self) -> Source:
        """Convert ORM record to domain source."""
        return Source(
            id=self.id,
            domain=self.domain,
            source_category=SourceCategory(self.source_category),
            created_at=self.created_at,
        )


class SourceSnapshotRecord(Base):
    """SQLAlchemy ORM record for the source_snapshots table."""

    __tablename__ = "source_snapshots"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    original_html: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fetch_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    etag: Mapped[str | None] = mapped_column(String(256), nullable=True)
    last_modified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    encoding: Mapped[str | None] = mapped_column(String(64), nullable=True)
    snapshot_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)
    snapshot_version: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "content_hash",
            name="uq_source_snapshots_source_id_content_hash",
        ),
    )

    source: Mapped[SourceRecord] = relationship("SourceRecord", back_populates="snapshots")

    @classmethod
    def from_domain(cls, domain_obj: SourceSnapshot) -> "SourceSnapshotRecord":
        """Build ORM record from domain snapshot."""
        return cls(
            id=domain_obj.id,
            source_id=domain_obj.source_id,
            url=domain_obj.url,
            fetched_at=domain_obj.fetched_at,
            content_hash=domain_obj.content_hash,
            content_type=domain_obj.content_type,
            http_status=domain_obj.http_status,
            title=domain_obj.title,
            extracted_text=domain_obj.extracted_text,
            original_html=domain_obj.original_html,
            content_length=domain_obj.content_length,
            fetch_duration_ms=domain_obj.fetch_duration_ms,
            etag=domain_obj.etag,
            last_modified=domain_obj.last_modified,
            encoding=domain_obj.encoding,
            snapshot_metadata=domain_obj.metadata,
            snapshot_version=domain_obj.snapshot_version,
        )

    def to_domain(self) -> SourceSnapshot:
        """Convert ORM record to domain snapshot."""
        return SourceSnapshot(
            id=self.id,
            source_id=self.source_id,
            url=self.url,
            fetched_at=self.fetched_at,
            content_hash=self.content_hash,
            content_type=self.content_type,
            http_status=self.http_status,
            title=self.title,
            extracted_text=self.extracted_text,
            original_html=self.original_html,
            content_length=self.content_length,
            fetch_duration_ms=self.fetch_duration_ms,
            etag=self.etag,
            last_modified=self.last_modified,
            encoding=self.encoding,
            metadata=self.snapshot_metadata,
            snapshot_version=self.snapshot_version,
        )


class SqlAlchemySourceRepository(SourceRepository):
    """SQLAlchemy-backed implementation of the source repository."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session."""
        self._session = session

    def add(self, source: Source) -> None:
        """Persist a new source."""
        self._session.add(SourceRecord.from_domain(source))
        self._session.flush()

    def get_by_id(self, source_id: UUID) -> Source | None:
        """Retrieve a source by UUID."""
        record = self._session.get(SourceRecord, source_id)
        if record is None:
            return None
        return record.to_domain()

    def get_by_domain(self, domain: str) -> Source | None:
        """Retrieve a source by canonical domain."""
        record = self._session.query(SourceRecord).filter(SourceRecord.domain == domain).first()
        if record is None:
            return None
        return record.to_domain()


class SqlAlchemySourceSnapshotRepository(SourceSnapshotRepository):
    """SQLAlchemy-backed implementation of the source snapshot repository."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session."""
        self._session = session

    def add(self, snapshot: SourceSnapshot) -> None:
        """Persist a new source snapshot."""
        self._session.add(SourceSnapshotRecord.from_domain(snapshot))
        self._session.flush()

    def get_by_id(self, snapshot_id: UUID) -> SourceSnapshot | None:
        """Retrieve a snapshot by UUID."""
        record = self._session.get(SourceSnapshotRecord, snapshot_id)
        if record is None:
            return None
        return record.to_domain()

    def get_by_hash(self, source_id: UUID, content_hash: str) -> SourceSnapshot | None:
        """Retrieve a snapshot matching the source ID and content fingerprint."""
        record = (
            self._session.query(SourceSnapshotRecord)
            .filter(
                SourceSnapshotRecord.source_id == source_id,
                SourceSnapshotRecord.content_hash == content_hash,
            )
            .first()
        )
        if record is None:
            return None
        return record.to_domain()

    def get_latest_version(self, source_id: UUID) -> int:
        """Return the maximum snapshot version recorded for this source (returns 0 if none)."""
        latest = (
            self._session.query(SourceSnapshotRecord.snapshot_version)
            .filter(SourceSnapshotRecord.source_id == source_id)
            .order_by(SourceSnapshotRecord.snapshot_version.desc())
            .first()
        )
        if latest is None:
            return 0
        return int(latest[0])

    def get_all(self) -> list[SourceSnapshot]:
        """Retrieve all persisted source snapshots."""
        records = self._session.query(SourceSnapshotRecord).all()
        return [rec.to_domain() for rec in records]
