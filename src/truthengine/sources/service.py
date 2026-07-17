"""Application service coordinating source ingestion and querying."""

import logging
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse
from uuid import UUID, uuid4

from truthengine.sources.domain import Source, SourceCategory, SourceSnapshot
from truthengine.sources.pipeline import compute_fingerprint, fetch_url
from truthengine.sources.repository import SourceRepository, SourceSnapshotRepository
from truthengine.sources.security import normalize_url

logger = logging.getLogger(__name__)


class SourceNotFoundError(Exception):
    """Raised when a canonical source record is not found."""

    def __init__(self, source_id: UUID) -> None:
        """Initialize with missing source ID."""
        super().__init__(f"Source {source_id} was not found.")
        self.source_id = source_id


class SnapshotNotFoundError(Exception):
    """Raised when a specific source snapshot record is not found."""

    def __init__(self, snapshot_id: UUID) -> None:
        """Initialize with missing snapshot ID."""
        super().__init__(f"Snapshot {snapshot_id} was not found.")
        self.snapshot_id = snapshot_id


class SourceService:
    """Coordinates the ingestion pipeline and queries for sources and snapshots."""

    def __init__(
        self,
        source_repository: SourceRepository,
        snapshot_repository: SourceSnapshotRepository,
    ) -> None:
        """Initialize with repositories."""
        self._source_repository = source_repository
        self._snapshot_repository = snapshot_repository

    def get_source(self, source_id: UUID) -> Source:
        """Retrieve a canonical source by ID, raising SourceNotFoundError if missing."""
        source = self._source_repository.get_by_id(source_id)
        if source is None:
            raise SourceNotFoundError(source_id)
        return source

    def get_snapshot(self, snapshot_id: UUID) -> SourceSnapshot:
        """Retrieve a snapshot by ID, raising SnapshotNotFoundError if missing."""
        snapshot = self._snapshot_repository.get_by_id(snapshot_id)
        if snapshot is None:
            raise SnapshotNotFoundError(snapshot_id)
        return snapshot

    def ingest(self, *, url: str) -> SourceSnapshot:
        """Normalize, fetch, fingerprint, and persist the webpage content or error details."""
        normalized_url = normalize_url(url)
        parsed = urlparse(normalized_url)
        domain = parsed.hostname or parsed.netloc or "unknown"

        # 1. Scrape URL
        fetch_result = fetch_url(normalized_url)

        # 2. Get or create root Source record
        source = self._source_repository.get_by_domain(domain)
        if source is None:
            source = Source(
                id=uuid4(),
                domain=domain,
                source_category=SourceCategory.GENERAL,
                created_at=datetime.now(UTC),
            )
            self._source_repository.add(source)

        # 3. Fingerprint
        if fetch_result.success:
            content_hash = compute_fingerprint(fetch_result.extracted_text)
        else:
            # Hash error codes to deduplicate failed fetches
            content_hash = compute_fingerprint(fetch_result.error_message or "failed_fetch")

        # 4. Check for duplicate snapshot
        existing = self._snapshot_repository.get_by_hash(source.id, content_hash)
        if existing is not None:
            logger.info(
                "Duplicate snapshot detected; returning existing record",
                extra={
                    "source_id": str(source.id),
                    "snapshot_id": str(existing.id),
                    "version": existing.snapshot_version,
                },
            )
            return existing

        # 5. Resolve version
        latest_version = self._snapshot_repository.get_latest_version(source.id)
        new_version = latest_version + 1

        # 6. Build and save snapshot
        metadata: dict[str, Any] = {
            "crawler_user_agent": "TruthEngineBot/1.0.0",
        }
        if not fetch_result.success:
            metadata.update(
                {
                    "error_type": fetch_result.error_type,
                    "error_message": fetch_result.error_message,
                }
            )

        snapshot = SourceSnapshot(
            id=uuid4(),
            source_id=source.id,
            url=normalized_url,
            fetched_at=fetch_result.fetched_at,
            content_hash=content_hash,
            content_type=fetch_result.content_type,
            http_status=fetch_result.http_status,
            title=fetch_result.title if fetch_result.success else "Failed Fetch",
            extracted_text=fetch_result.extracted_text,
            original_html=fetch_result.original_html,
            content_length=fetch_result.content_length,
            fetch_duration_ms=fetch_result.fetch_duration_ms,
            etag=fetch_result.etag,
            last_modified=fetch_result.last_modified,
            encoding=fetch_result.encoding,
            metadata=metadata,
            snapshot_version=new_version,
        )

        self._snapshot_repository.add(snapshot)
        logger.info(
            "New source snapshot persisted",
            extra={
                "source_id": str(source.id),
                "snapshot_id": str(snapshot.id),
                "version": snapshot.snapshot_version,
                "success": fetch_result.success,
            },
        )
        return snapshot
