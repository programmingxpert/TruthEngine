"""Domain entities and enums for the Source Ingestion bounded context."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class SourceCategory(StrEnum):
    """Refined classification of web source categories."""

    GOVERNMENT = "GOVERNMENT"
    NEWS = "NEWS"
    ACADEMIC = "ACADEMIC"
    ORGANIZATION = "ORGANIZATION"
    CORPORATE = "CORPORATE"
    DISCUSSION = "DISCUSSION"
    BLOG = "BLOG"
    GENERAL = "GENERAL"


@dataclass(frozen=True, slots=True)
class Source:
    """A canonical source publisher represented by its base domain/host."""

    id: UUID
    domain: str
    source_category: SourceCategory
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    """An immutable snapshot of a single fetched URL belonging to a Source."""

    id: UUID
    source_id: UUID
    url: str
    fetched_at: datetime
    content_hash: str
    content_type: str
    http_status: int | None
    title: str
    extracted_text: str
    original_html: str
    content_length: int | None
    fetch_duration_ms: int | None
    etag: str | None
    last_modified: datetime | None
    encoding: str | None
    metadata: dict[str, Any]
    snapshot_version: int
