"""add_timezone_to_sources

Revision ID: f23a233c6947
Revises: 4e75adccff01
Create Date: 2025-11-02 14:42:04.909324

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f23a233c6947"
down_revision: str | Sequence[str] | None = "4e75adccff01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("sources", sa.Column("timezone", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("sources", "timezone")
