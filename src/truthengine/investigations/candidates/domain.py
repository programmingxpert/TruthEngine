"""Domain entities and policy definitions for candidate passage selection."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SelectionPolicy:
    """Configurable boundaries and heuristics for filtering candidate passages."""

    min_lexical_threshold: float = 1.0
    max_returned_passages: int = 5
    diversity_rules: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DocumentSegment:
    """A structurally parsed snippet of text from a source snapshot."""

    id: UUID
    snapshot_id: UUID
    order: int
    heading: str | None
    heading_level: int | None
    paragraph_order: int
    parent_section: str | None
    content: str
    character_range_start: int
    character_range_end: int
    token_estimate: int


@dataclass(frozen=True, slots=True)
class CandidatePassage:
    """A structural passage deemed relevant to an investigation with machine-readable reasons."""

    id: UUID
    investigation_id: UUID
    segment_id: UUID
    snapshot_version: int
    algorithm_version: str
    paragraph_order: int
    selection_explanation: dict[str, Any]
    selected_at: datetime
