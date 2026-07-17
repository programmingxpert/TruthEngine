"""Repository interfaces for persisting sources and snapshots."""

from abc import ABC, abstractmethod
from uuid import UUID

from truthengine.sources.domain import Source, SourceSnapshot


class SourceRepository(ABC):
    """Persistence boundary for canonical sources."""

    @abstractmethod
    def add(self, source: Source) -> None:
        """Persist a new source."""

    @abstractmethod
    def get_by_id(self, source_id: UUID) -> Source | None:
        """Retrieve a source by its UUID."""

    @abstractmethod
    def get_by_domain(self, domain: str) -> Source | None:
        """Retrieve a source by its canonical domain."""


class SourceSnapshotRepository(ABC):
    """Persistence boundary for immutable source snapshots."""

    @abstractmethod
    def add(self, snapshot: SourceSnapshot) -> None:
        """Persist a new source snapshot."""

    @abstractmethod
    def get_by_id(self, snapshot_id: UUID) -> SourceSnapshot | None:
        """Retrieve a snapshot by its UUID."""

    @abstractmethod
    def get_by_hash(self, source_id: UUID, content_hash: str) -> SourceSnapshot | None:
        """Retrieve a snapshot matching the source ID and content fingerprint."""

    @abstractmethod
    def get_latest_version(self, source_id: UUID) -> int:
        """Return the maximum snapshot version recorded for this source (returns 0 if none)."""

    @abstractmethod
    def get_all(self) -> list[SourceSnapshot]:
        """Retrieve all persisted source snapshots."""
