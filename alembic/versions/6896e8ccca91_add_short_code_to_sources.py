"""add_short_code_to_sources

Revision ID: 6896e8ccca91
Revises: e43bf90986c0
Create Date: 2025-11-01 13:11:08.311434

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "6896e8ccca91"
down_revision: str | Sequence[str] | None = "e43bf90986c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("sources", schema=None) as batch_op:
        batch_op.add_column(sa.Column("short_code", sa.String(), nullable=True))
        batch_op.create_unique_constraint("uq_sources_short_code", ["short_code"])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("sources", schema=None) as batch_op:
        batch_op.drop_constraint("uq_sources_short_code", type_="unique")
        batch_op.drop_column("short_code")
