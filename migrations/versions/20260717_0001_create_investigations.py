"""Create investigations table.

Revision ID: 20260717_0001
Revises:
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260717_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the investigations table."""
    op.create_table(
        "investigations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_investigations")),
    )
    op.create_index(
        op.f("ix_investigations_status"),
        "investigations",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the investigations table."""
    op.drop_index(op.f("ix_investigations_status"), table_name="investigations")
    op.drop_table("investigations")
