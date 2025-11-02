"""remove_url_from_sources

Revision ID: 8f6ea8f5068d
Revises: 0a76538b3133
Create Date: 2025-10-29 14:23:21.017454

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "8f6ea8f5068d"
down_revision: str | Sequence[str] | None = "0a76538b3133"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # This migration is a no-op because the url column was never added to sources.
    # The initial_schema (c338b408fa30) created sources without a url column.
    # This migration is kept for migration chain continuity.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # This migration is a no-op, so downgrade does nothing
    pass
