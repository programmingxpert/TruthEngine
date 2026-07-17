"""Repository interface for investigation persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from truthengine.investigations.domain import Investigation, TimelineEvent


class InvestigationRepository(ABC):
    """Persistence boundary for investigations."""

    @abstractmethod
    def add(self, investigation: Investigation) -> None:
        """Persist a new investigation."""

    @abstractmethod
    def get_by_id(self, investigation_id: UUID) -> Investigation | None:
        """Return an investigation by ID, if it exists."""

    @abstractmethod
    def get_all(self) -> list[Investigation]:
        """Return all investigations, ordered by created_at descending."""

    @abstractmethod
    def update(self, investigation: Investigation) -> None:
        """Update an existing investigation."""

    @abstractmethod
    def delete(self, investigation_id: UUID) -> None:
        """Delete an investigation by UUID."""


class TimelineEventRepository(ABC):
    """Persistence boundary for timeline events."""

    @abstractmethod
    def add(self, event: TimelineEvent) -> None:
        """Persist a new timeline event."""

    @abstractmethod
    def get_by_investigation_id(self, investigation_id: UUID) -> list[TimelineEvent]:
        """Return all timeline events for a given investigation, ordered by created_at."""
