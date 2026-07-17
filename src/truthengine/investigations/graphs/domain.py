"""Domain models and enums for the versioned evidence graph."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ClaimType(StrEnum):
    """Semantic type of claim."""

    PRIMARY = "PRIMARY"
    SUPPORTING = "SUPPORTING"


class ClaimStatus(StrEnum):
    """Verification status of a claim."""

    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    REFUTED = "REFUTED"


class RelationType(StrEnum):
    """Logical mapping type for an evidence relation edge."""

    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CONTEXT = "CONTEXT"
    UNRELATED = "UNRELATED"


@dataclass(frozen=True, slots=True)
class Claim:
    """A semantic claim node in the evidence graph."""

    id: UUID
    graph_id: UUID
    text: str
    claim_type: ClaimType
    status: ClaimStatus


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    """A grounded factual snippet extracted from a source snapshot."""

    id: UUID
    graph_id: UUID
    source_snapshot_id: UUID | None
    quote: str
    location: str
    extracted_at: datetime


@dataclass(frozen=True, slots=True)
class EvidenceRelation:
    """A logical relationship edge connecting an EvidenceItem to a Claim."""

    id: UUID
    graph_id: UUID
    claim_id: UUID
    evidence_item_id: UUID
    relation_type: RelationType


@dataclass(frozen=True, slots=True)
class EvidenceGraph:
    """An immutable, versioned snapshot of the investigation's evidence graph."""

    id: UUID
    investigation_id: UUID
    version: int
    created_at: datetime
    claims: list[Claim]
    evidence_items: list[EvidenceItem]
    relations: list[EvidenceRelation]
