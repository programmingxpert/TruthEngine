"""Repository boundaries for document segments and candidate passages."""

from abc import ABC, abstractmethod
from uuid import UUID

from truthengine.investigations.candidates.domain import (
    CandidatePassage,
    DocumentSegment,
)


class DocumentSegmentRepository(ABC):
    """Persistence boundary for parsed document segments."""

    @abstractmethod
    def add_all(self, segments: list[DocumentSegment]) -> None:
        """Persist a list of document segments."""

    @abstractmethod
    def get_by_id(self, segment_id: UUID) -> DocumentSegment | None:
        """Retrieve a single segment by its UUID."""

    @abstractmethod
    def get_by_snapshot_id(self, snapshot_id: UUID) -> list[DocumentSegment]:
        """Retrieve all segments parsed for a specific snapshot."""


class CandidatePassageRepository(ABC):
    """Persistence boundary for selected candidate passages."""

    @abstractmethod
    def add_all(self, passages: list[CandidatePassage]) -> None:
        """Persist a list of selected passages."""

    @abstractmethod
    def get_by_investigation_id(self, investigation_id: UUID) -> list[CandidatePassage]:
        """Retrieve all candidate passages selected for an investigation."""

    @abstractmethod
    def get_by_segment_id(self, segment_id: UUID) -> list[CandidatePassage]:
        """Retrieve all candidate passages referring to a specific segment."""
