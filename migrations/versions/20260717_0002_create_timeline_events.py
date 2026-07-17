"""Create timeline events table.

Revision ID: 20260717_0002
Revises: 20260717_0001
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260717_0002"
down_revision: str | None = "20260717_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the investigation_timeline_events table."""
    op.create_table(
        "investigation_timeline_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("investigation_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["investigation_id"],
            ["investigations.id"],
            name=op.f("fk_investigation_timeline_events_investigation_id_investigations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_investigation_timeline_events")),
    )
    op.create_index(
        op.f("ix_investigation_timeline_events_investigation_id"),
        "investigation_timeline_events",
        ["investigation_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the investigation_timeline_events table."""
    op.drop_index(
        op.f("ix_investigation_timeline_events_investigation_id"),
        table_name="investigation_timeline_events",
    )
    op.drop_table("investigation_timeline_events")
