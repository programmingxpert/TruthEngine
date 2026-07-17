"""REST Pydantic transport models for the sources context."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from truthengine.sources.domain import Source, SourceSnapshot


class IngestSourceRequest(BaseModel):
    """Payload to trigger web page ingestion."""

    url: str = Field(..., description="The canonical target URL to fetch and parse.")


class SourceResponse(BaseModel):
    """Transport schema representing a canonical publisher origin."""

    source_id: UUID
    domain: str
    source_category: str
    created_at: datetime

    @classmethod
    def from_domain(cls, source: Source) -> "SourceResponse":
        """Build response payload from domain entity."""
        return cls(
            source_id=source.id,
            domain=source.domain,
            source_category=source.source_category.value,
            created_at=source.created_at,
        )


class SourceSnapshotResponse(BaseModel):
    """Transport schema representing an immutable web snapshot or logged fetch error."""

    snapshot_id: UUID
    source_id: UUID
    url: str
    fetched_at: datetime
    content_hash: str
    content_type: str
    http_status: int | None
    title: str
    extracted_text: str
    content_length: int | None
    fetch_duration_ms: int | None
    etag: str | None
    last_modified: datetime | None
    encoding: str | None
    metadata: dict[str, Any]
    snapshot_version: int

    @classmethod
    def from_domain(cls, snapshot: SourceSnapshot) -> "SourceSnapshotResponse":
        """Build response payload from domain entity."""
        return cls(
            snapshot_id=snapshot.id,
            source_id=snapshot.source_id,
            url=snapshot.url,
            fetched_at=snapshot.fetched_at,
            content_hash=snapshot.content_hash,
            content_type=snapshot.content_type,
            http_status=snapshot.http_status,
            title=snapshot.title,
            extracted_text=snapshot.extracted_text,
            content_length=snapshot.content_length,
            fetch_duration_ms=snapshot.fetch_duration_ms,
            etag=snapshot.etag,
            last_modified=snapshot.last_modified,
            encoding=snapshot.encoding,
            metadata=snapshot.metadata,
            snapshot_version=snapshot.snapshot_version,
        )
