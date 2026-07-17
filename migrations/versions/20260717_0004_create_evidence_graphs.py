"""Create evidence graphs tables.

Revision ID: 20260717_0004
Revises: 20260717_0003
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260717_0004"
down_revision: str | None = "20260717_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the evidence graphs, claims, evidence items, and relations tables."""
    # 1. Create evidence_graphs
    op.create_table(
        "evidence_graphs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("investigation_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["investigation_id"],
            ["investigations.id"],
            name=op.f("fk_evidence_graphs_investigation_id_investigations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_graphs")),
        sa.UniqueConstraint(
            "investigation_id",
            "version",
            name="uq_evidence_graphs_investigation_id_version",
        ),
    )
    op.create_index(
        op.f("ix_evidence_graphs_investigation_id"),
        "evidence_graphs",
        ["investigation_id"],
        unique=False,
    )

    # 2. Create claims
    op.create_table(
        "claims",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("graph_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["graph_id"],
            ["evidence_graphs.id"],
            name=op.f("fk_claims_graph_id_evidence_graphs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_claims")),
    )
    op.create_index(op.f("ix_claims_graph_id"), "claims", ["graph_id"], unique=False)

    # 3. Create evidence_items
    op.create_table(
        "evidence_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("graph_id", sa.Uuid(), nullable=False),
        sa.Column("source_snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=256), nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["graph_id"],
            ["evidence_graphs.id"],
            name=op.f("fk_evidence_items_graph_id_evidence_graphs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_items")),
    )
    op.create_index(
        op.f("ix_evidence_items_graph_id"),
        "evidence_items",
        ["graph_id"],
        unique=False,
    )

    # 4. Create evidence_relations
    op.create_table(
        "evidence_relations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("graph_id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_item_id", sa.Uuid(), nullable=False),
        sa.Column("relation_type", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["graph_id"],
            ["evidence_graphs.id"],
            name=op.f("fk_evidence_relations_graph_id_evidence_graphs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["claim_id"],
            ["claims.id"],
            name=op.f("fk_evidence_relations_claim_id_claims"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_item_id"],
            ["evidence_items.id"],
            name=op.f("fk_evidence_relations_evidence_item_id_evidence_items"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_relations")),
    )
    op.create_index(
        op.f("ix_evidence_relations_graph_id"),
        "evidence_relations",
        ["graph_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evidence_relations_claim_id"),
        "evidence_relations",
        ["claim_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evidence_relations_evidence_item_id"),
        "evidence_relations",
        ["evidence_item_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the evidence graphs, claims, evidence items, and relations tables."""
    op.drop_table("evidence_relations")
    op.drop_table("evidence_items")
    op.drop_table("claims")
    op.drop_table("evidence_graphs")
