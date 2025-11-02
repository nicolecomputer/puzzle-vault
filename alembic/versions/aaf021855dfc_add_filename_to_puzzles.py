"""add_filename_to_puzzles

Revision ID: aaf021855dfc
Revises: f23a233c6947
Create Date: 2025-11-02 14:58:23.074304

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "aaf021855dfc"
down_revision: str | Sequence[str] | None = "f23a233c6947"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("puzzles", sa.Column("filename", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("puzzles", "filename")
