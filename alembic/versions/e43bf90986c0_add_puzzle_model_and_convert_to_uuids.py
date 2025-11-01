"""add_puzzle_model_and_convert_to_uuids

Revision ID: e43bf90986c0
Revises: 8f6ea8f5068d
Create Date: 2025-10-29 15:33:21.124840

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e43bf90986c0'
down_revision: Union[str, Sequence[str], None] = '8f6ea8f5068d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('sources', schema=None) as batch_op:
        batch_op.alter_column('id',
                   existing_type=sa.INTEGER(),
                   type_=sa.String(length=36),
                   existing_nullable=False)
        batch_op.drop_index('ix_sources_id')

    op.create_table('puzzles',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('source_id', sa.String(length=36), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('author', sa.String(), nullable=True),
    sa.Column('puzzle_date', sa.Date(), nullable=True),
    sa.Column('file_path', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('puzzles')

    with op.batch_alter_table('sources', schema=None) as batch_op:
        batch_op.create_index('ix_sources_id', ['id'], unique=False)
        batch_op.alter_column('id',
                   existing_type=sa.String(length=36),
                   type_=sa.INTEGER(),
                   existing_nullable=False)
