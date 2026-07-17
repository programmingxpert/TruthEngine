"""Add original HTML to source snapshots.

Revision ID: 20260717_0007
Revises: 20260717_0006
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260717_0007"
down_revision: str | None = "20260717_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add original HTML storage for crawler snapshots."""
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.add_column(
            "source_snapshots",
            sa.Column("original_html", sa.Text(), nullable=False, server_default=""),
        )
    else:
        op.add_column(
            "source_snapshots",
            sa.Column("original_html", sa.Text(), nullable=False, server_default=""),
        )
        op.alter_column("source_snapshots", "original_html", server_default=None)


def downgrade() -> None:
    """Remove original HTML storage from crawler snapshots."""
    op.drop_column("source_snapshots", "original_html")
