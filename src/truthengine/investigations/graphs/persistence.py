"""SQLAlchemy models and repository for persisting versioned evidence graphs."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from truthengine.core.database import Base
from truthengine.investigations.graphs.domain import (
    Claim,
    ClaimStatus,
    ClaimType,
    EvidenceGraph,
    EvidenceItem,
    EvidenceRelation,
    RelationType,
)
from truthengine.investigations.graphs.repository import EvidenceGraphRepository


class EvidenceGraphRecord(Base):
    """SQLAlchemy ORM record for the evidence_graphs table."""

    __tablename__ = "evidence_graphs"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    investigation_id: Mapped[UUID] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "investigation_id",
            "version",
            name="uq_evidence_graphs_investigation_id_version",
        ),
    )

    claims: Mapped[list["ClaimRecord"]] = relationship(
        "ClaimRecord",
        back_populates="graph",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    evidence_items: Mapped[list["EvidenceItemRecord"]] = relationship(
        "EvidenceItemRecord",
        back_populates="graph",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    relations: Mapped[list["EvidenceRelationRecord"]] = relationship(
        "EvidenceRelationRecord",
        back_populates="graph",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    @classmethod
    def from_domain(cls, graph: EvidenceGraph) -> "EvidenceGraphRecord":
        """Build ORM record from domain graph."""
        record = cls(
            id=graph.id,
            investigation_id=graph.investigation_id,
            version=graph.version,
            created_at=graph.created_at,
        )
        record.claims = [
            ClaimRecord(
                id=c.id,
                graph_id=c.graph_id,
                text=c.text,
                claim_type=c.claim_type.value,
                status=c.status.value,
            )
            for c in graph.claims
        ]
        record.evidence_items = [
            EvidenceItemRecord(
                id=item.id,
                graph_id=item.graph_id,
                source_snapshot_id=item.source_snapshot_id,
                quote=item.quote,
                location=item.location,
                extracted_at=item.extracted_at,
            )
            for item in graph.evidence_items
        ]
        record.relations = [
            EvidenceRelationRecord(
                id=rel.id,
                graph_id=rel.graph_id,
                claim_id=rel.claim_id,
                evidence_item_id=rel.evidence_item_id,
                relation_type=rel.relation_type.value,
            )
            for rel in graph.relations
        ]
        return record

    def to_domain(self) -> EvidenceGraph:
        """Convert ORM record to domain graph."""
        claims = [
            Claim(
                id=c.id,
                graph_id=c.graph_id,
                text=c.text,
                claim_type=ClaimType(c.claim_type),
                status=ClaimStatus(c.status),
            )
            for c in self.claims
        ]
        evidence_items = [
            EvidenceItem(
                id=item.id,
                graph_id=item.graph_id,
                source_snapshot_id=item.source_snapshot_id,
                quote=item.quote,
                location=item.location,
                extracted_at=item.extracted_at,
            )
            for item in self.evidence_items
        ]
        relations = [
            EvidenceRelation(
                id=rel.id,
                graph_id=rel.graph_id,
                claim_id=rel.claim_id,
                evidence_item_id=rel.evidence_item_id,
                relation_type=RelationType(rel.relation_type),
            )
            for rel in self.relations
        ]
        return EvidenceGraph(
            id=self.id,
            investigation_id=self.investigation_id,
            version=self.version,
            created_at=self.created_at,
            claims=claims,
            evidence_items=evidence_items,
            relations=relations,
        )


class ClaimRecord(Base):
    """SQLAlchemy ORM record for the claims table."""

    __tablename__ = "claims"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    graph_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_graphs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(length=32), nullable=False)
    status: Mapped[str] = mapped_column(String(length=32), nullable=False)

    graph: Mapped[EvidenceGraphRecord] = relationship(
        "EvidenceGraphRecord", back_populates="claims"
    )


class EvidenceItemRecord(Base):
    """SQLAlchemy ORM record for the evidence_items table."""

    __tablename__ = "evidence_items"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    graph_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_graphs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_snapshot_id: Mapped[UUID | None] = mapped_column(nullable=True)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(length=256), nullable=False)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    graph: Mapped[EvidenceGraphRecord] = relationship(
        "EvidenceGraphRecord", back_populates="evidence_items"
    )


class EvidenceRelationRecord(Base):
    """SQLAlchemy ORM record for the evidence_relations table."""

    __tablename__ = "evidence_relations"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    graph_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_graphs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relation_type: Mapped[str] = mapped_column(String(length=32), nullable=False)

    graph: Mapped[EvidenceGraphRecord] = relationship(
        "EvidenceGraphRecord", back_populates="relations"
    )


class SqlAlchemyEvidenceGraphRepository(EvidenceGraphRepository):
    """SQLAlchemy-backed implementation of the evidence graph repository."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a request-scoped database session."""
        self._session = session

    def add(self, graph: EvidenceGraph) -> None:
        """Persist a new version of the evidence graph with all its nodes and edges."""
        self._session.add(EvidenceGraphRecord.from_domain(graph))
        self._session.flush()

    def get_by_id(self, graph_id: UUID) -> EvidenceGraph | None:
        """Return the evidence graph by ID, including all nodes and relations."""
        record = self._session.get(EvidenceGraphRecord, graph_id)
        if record is None:
            return None
        return record.to_domain()

    def get_latest_by_investigation_id(self, investigation_id: UUID) -> EvidenceGraph | None:
        """Return the latest version of the evidence graph for the given investigation."""
        record = (
            self._session.query(EvidenceGraphRecord)
            .filter(EvidenceGraphRecord.investigation_id == investigation_id)
            .order_by(EvidenceGraphRecord.version.desc())
            .first()
        )
        if record is None:
            return None
        return record.to_domain()
