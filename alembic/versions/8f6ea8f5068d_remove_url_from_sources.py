"""remove_url_from_sources

Revision ID: 8f6ea8f5068d
Revises: 0a76538b3133
Create Date: 2025-10-29 14:23:21.017454

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f6ea8f5068d'
down_revision: Union[str, Sequence[str], None] = '0a76538b3133'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('sources', schema=None) as batch_op:
        batch_op.drop_column('url')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('sources', schema=None) as batch_op:
        batch_op.add_column(sa.Column('url', sa.VARCHAR(), nullable=False))
