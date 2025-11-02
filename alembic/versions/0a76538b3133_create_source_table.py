"""create_source_table

Revision ID: 0a76538b3133
Revises: c338b408fa30
Create Date: 2025-10-29 14:17:19.405560

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0a76538b3133"
down_revision: str | Sequence[str] | None = "c338b408fa30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # This migration is a no-op because the sources table was already created
    # in the initial_schema migration (c338b408fa30).
    # This migration file is kept for migration chain continuity.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # This migration is a no-op, so downgrade does nothing
    pass
