"""replace_puzzle_date_constraint_with_file_hash

Revision ID: 16516c3575c5
Revises: 5d6c56deb624
Create Date: 2025-11-01 14:58:30.263411

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "16516c3575c5"
down_revision: str | Sequence[str] | None = "5d6c56deb624"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("puzzles", schema=None) as batch_op:
        # Add file_hash column (initially nullable to allow migration)
        batch_op.add_column(sa.Column("file_hash", sa.String(length=64), nullable=True))
        # Drop old constraint
        batch_op.drop_constraint("uq_source_puzzle_date", type_="unique")
        # Add new constraint
        batch_op.create_unique_constraint(
            "uq_source_file_hash", ["source_id", "file_hash"]
        )

    # Note: Existing puzzles will have NULL file_hash
    # They should be handled by the application or manually updated


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("puzzles", schema=None) as batch_op:
        # Drop new constraint
        batch_op.drop_constraint("uq_source_file_hash", type_="unique")
        # Restore old constraint
        batch_op.create_unique_constraint(
            "uq_source_puzzle_date", ["source_id", "puzzle_date"]
        )
        # Drop file_hash column
        batch_op.drop_column("file_hash")
