"""Create document segments and candidate passages tables.

Revision ID: 20260717_0006
Revises: 20260717_0005
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260717_0006"
down_revision: str | None = "20260717_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the document_segments and candidate_passages tables."""
    # 1. Create document_segments
    op.create_table(
        "document_segments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("heading", sa.String(length=256), nullable=True),
        sa.Column("heading_level", sa.Integer(), nullable=True),
        sa.Column("paragraph_order", sa.Integer(), nullable=False),
        sa.Column("parent_section", sa.String(length=256), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("character_range_start", sa.Integer(), nullable=False),
        sa.Column("character_range_end", sa.Integer(), nullable=False),
        sa.Column("token_estimate", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["source_snapshots.id"],
            name=op.f("fk_document_segments_snapshot_id_source_snapshots"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_segments")),
    )
    op.create_index(
        op.f("ix_document_segments_snapshot_id"),
        "document_segments",
        ["snapshot_id"],
        unique=False,
    )

    # 2. Create candidate_passages
    op.create_table(
        "candidate_passages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("investigation_id", sa.Uuid(), nullable=False),
        sa.Column("segment_id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_version", sa.Integer(), nullable=False),
        sa.Column("algorithm_version", sa.String(length=64), nullable=False),
        sa.Column("paragraph_order", sa.Integer(), nullable=False),
        sa.Column("selection_explanation", sa.JSON(), nullable=False),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["investigation_id"],
            ["investigations.id"],
            name=op.f("fk_candidate_passages_investigation_id_investigations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["segment_id"],
            ["document_segments.id"],
            name=op.f("fk_candidate_passages_segment_id_document_segments"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_passages")),
    )
    op.create_index(
        op.f("ix_candidate_passages_investigation_id"),
        "candidate_passages",
        ["investigation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_candidate_passages_segment_id"),
        "candidate_passages",
        ["segment_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the document_segments and candidate_passages tables."""
    op.drop_table("candidate_passages")
    op.drop_table("document_segments")
