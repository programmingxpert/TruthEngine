"""HTTP transport schemas for investigation endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from truthengine.investigations.candidates.domain import CandidatePassage
from truthengine.investigations.domain import (
    Investigation,
    InvestigationStatus,
    TimelineEvent,
    normalize_query,
)
from truthengine.investigations.graphs.domain import (
    Claim,
    EvidenceGraph,
    EvidenceItem,
    EvidenceRelation,
)
from truthengine.investigations.planning.domain import InvestigationPlan


class CreateInvestigationRequest(BaseModel):
    """Request body for creating an investigation."""

    query: str = Field(
        min_length=1,
        max_length=2_000,
        description="Claim or question the user wants TruthEngine to investigate.",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        """Normalize and validate the submitted investigation query."""
        return normalize_query(value)


class CreateInvestigationResponse(BaseModel):
    """Response body returned after creating an investigation."""

    investigation_id: UUID
    status: InvestigationStatus

    @classmethod
    def from_domain(cls, investigation: Investigation) -> "CreateInvestigationResponse":
        """Build a response from a domain investigation."""
        return cls(investigation_id=investigation.id, status=investigation.status)


class InvestigationMetadataResponse(BaseModel):
    """Metadata response for a single investigation."""

    investigation_id: UUID
    query: str
    status: InvestigationStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, investigation: Investigation) -> "InvestigationMetadataResponse":
        """Build a metadata response from a domain investigation."""
        return cls(
            investigation_id=investigation.id,
            query=investigation.query,
            status=investigation.status,
            created_at=investigation.created_at,
            updated_at=investigation.updated_at,
        )


class TimelineEventResponse(BaseModel):
    """Transport schema for an investigation timeline event."""

    id: UUID
    investigation_id: UUID
    event_type: str
    message: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict, serialization_alias="metadata")

    @classmethod
    def from_domain(cls, event: TimelineEvent) -> "TimelineEventResponse":
        """Build a timeline event schema from domain object."""
        return cls(
            id=event.id,
            investigation_id=event.investigation_id,
            event_type=event.event_type,
            message=event.message,
            created_at=event.created_at,
            metadata=event.metadata,
        )


class InvestigationPlanResponse(BaseModel):
    """Transport schema for an investigation plan."""

    investigation_id: UUID
    detected_domain: str
    objective: str
    assumptions: list[str]
    required_evidence_categories: list[str]
    preferred_source_categories: list[str]
    excluded_source_categories: list[str]
    retrieval_strategy: str
    success_criteria: list[str]
    limitations: list[str]
    planning_timestamp: datetime
    planner_version: str

    @classmethod
    def from_domain(cls, plan: "InvestigationPlan") -> "InvestigationPlanResponse":
        """Build an investigation plan response schema from the domain object."""
        return cls(
            investigation_id=plan.investigation_id,
            detected_domain=plan.detected_domain,
            objective=plan.objective,
            assumptions=plan.assumptions,
            required_evidence_categories=plan.required_evidence_categories,
            preferred_source_categories=plan.preferred_source_categories,
            excluded_source_categories=plan.excluded_source_categories,
            retrieval_strategy=plan.retrieval_strategy,
            success_criteria=plan.success_criteria,
            limitations=plan.limitations,
            planning_timestamp=plan.planning_timestamp,
            planner_version=plan.planner_version,
        )


class ClaimResponse(BaseModel):
    """Transport schema for a Claim node."""

    id: UUID
    graph_id: UUID
    text: str
    claim_type: str
    status: str

    @classmethod
    def from_domain(cls, node: Claim) -> "ClaimResponse":
        """Build a ClaimResponse schema from the domain object."""
        return cls(
            id=node.id,
            graph_id=node.graph_id,
            text=node.text,
            claim_type=node.claim_type.value,
            status=node.status.value,
        )


class EvidenceItemResponse(BaseModel):
    """Transport schema for an EvidenceItem node."""

    id: UUID
    graph_id: UUID
    source_snapshot_id: UUID | None
    quote: str
    location: str
    extracted_at: datetime

    @classmethod
    def from_domain(cls, node: EvidenceItem) -> "EvidenceItemResponse":
        """Build an EvidenceItemResponse schema from the domain object."""
        return cls(
            id=node.id,
            graph_id=node.graph_id,
            source_snapshot_id=node.source_snapshot_id,
            quote=node.quote,
            location=node.location,
            extracted_at=node.extracted_at,
        )


class EvidenceRelationResponse(BaseModel):
    """Transport schema for an EvidenceRelation edge."""

    id: UUID
    graph_id: UUID
    claim_id: UUID
    evidence_item_id: UUID
    relation_type: str

    @classmethod
    def from_domain(cls, edge: EvidenceRelation) -> "EvidenceRelationResponse":
        """Build an EvidenceRelationResponse schema from the domain object."""
        return cls(
            id=edge.id,
            graph_id=edge.graph_id,
            claim_id=edge.claim_id,
            evidence_item_id=edge.evidence_item_id,
            relation_type=edge.relation_type.value,
        )


class EvidenceGraphResponse(BaseModel):
    """Transport schema for the complete EvidenceGraph."""

    graph_id: UUID
    investigation_id: UUID
    version: int
    created_at: datetime
    claims: list[ClaimResponse]
    evidence_items: list[EvidenceItemResponse]
    relations: list[EvidenceRelationResponse]

    @classmethod
    def from_domain(cls, graph: EvidenceGraph) -> "EvidenceGraphResponse":
        """Build an EvidenceGraphResponse schema from the domain object."""
        return cls(
            graph_id=graph.id,
            investigation_id=graph.investigation_id,
            version=graph.version,
            created_at=graph.created_at,
            claims=[ClaimResponse.from_domain(c) for c in graph.claims],
            evidence_items=[
                EvidenceItemResponse.from_domain(item) for item in graph.evidence_items
            ],
            relations=[EvidenceRelationResponse.from_domain(rel) for rel in graph.relations],
        )


class CandidatePassageResponse(BaseModel):
    """Transport schema representing a selected CandidatePassage."""

    passage_id: UUID
    investigation_id: UUID
    segment_id: UUID
    snapshot_version: int
    algorithm_version: str
    paragraph_order: int
    selection_explanation: dict[str, Any]
    selected_at: datetime

    @classmethod
    def from_domain(cls, passage: CandidatePassage) -> "CandidatePassageResponse":
        """Build response payload from domain entity."""
        return cls(
            passage_id=passage.id,
            investigation_id=passage.investigation_id,
            segment_id=passage.segment_id,
            snapshot_version=passage.snapshot_version,
            algorithm_version=passage.algorithm_version,
            paragraph_order=passage.paragraph_order,
            selection_explanation=passage.selection_explanation,
            selected_at=passage.selected_at,
        )
