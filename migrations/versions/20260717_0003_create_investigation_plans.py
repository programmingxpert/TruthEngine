"""Create investigation plans table.

Revision ID: 20260717_0003
Revises: 20260717_0002
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260717_0003"
down_revision: str | None = "20260717_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the investigation_plans table."""
    op.create_table(
        "investigation_plans",
        sa.Column(
            "investigation_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column("detected_domain", sa.String(length=64), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("required_evidence_categories", sa.JSON(), nullable=False),
        sa.Column("preferred_source_categories", sa.JSON(), nullable=False),
        sa.Column("excluded_source_categories", sa.JSON(), nullable=False),
        sa.Column("retrieval_strategy", sa.Text(), nullable=False),
        sa.Column("success_criteria", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("planning_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("planner_version", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["investigation_id"],
            ["investigations.id"],
            name=op.f("fk_investigation_plans_investigation_id_investigations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("investigation_id", name=op.f("pk_investigation_plans")),
    )


def downgrade() -> None:
    """Drop the investigation_plans table."""
    op.drop_table("investigation_plans")
