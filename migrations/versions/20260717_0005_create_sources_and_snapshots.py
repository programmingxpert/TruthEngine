"""Create sources and snapshots tables.

Revision ID: 20260717_0005
Revises: 20260717_0004
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260717_0005"
down_revision: str | None = "20260717_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the sources and source_snapshots tables."""
    # 1. Create sources
    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("domain", sa.String(length=256), nullable=False),
        sa.Column("source_category", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sources")),
        sa.UniqueConstraint("domain", name="uq_sources_domain"),
    )
    op.create_index(op.f("ix_sources_domain"), "sources", ["domain"], unique=True)

    # 2. Create source_snapshots
    op.create_table(
        "source_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("content_length", sa.Integer(), nullable=True),
        sa.Column("fetch_duration_ms", sa.Integer(), nullable=True),
        sa.Column("etag", sa.String(length=256), nullable=True),
        sa.Column("last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("encoding", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("snapshot_version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name=op.f("fk_source_snapshots_source_id_sources"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_snapshots")),
        sa.UniqueConstraint(
            "source_id",
            "content_hash",
            name="uq_source_snapshots_source_id_content_hash",
        ),
    )
    op.create_index(
        op.f("ix_source_snapshots_source_id"),
        "source_snapshots",
        ["source_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the sources and source_snapshots tables."""
    op.drop_table("source_snapshots")
    op.drop_table("sources")
