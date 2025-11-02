"""add_agent_scheduling_fields

Revision ID: 342af1a1f122
Revises: aaf021855dfc
Create Date: 2025-11-02 16:07:01.032396

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "342af1a1f122"
down_revision: str | Sequence[str] | None = "aaf021855dfc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "sources",
        sa.Column("schedule_enabled", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column(
        "sources", sa.Column("schedule_interval_hours", sa.Integer(), nullable=True)
    )
    op.add_column(
        "sources", sa.Column("last_scheduled_run_at", sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("sources", "last_scheduled_run_at")
    op.drop_column("sources", "schedule_interval_hours")
    op.drop_column("sources", "schedule_enabled")
