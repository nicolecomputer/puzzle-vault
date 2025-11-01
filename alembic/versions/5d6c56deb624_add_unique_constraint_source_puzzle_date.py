"""add_unique_constraint_source_puzzle_date

Revision ID: 5d6c56deb624
Revises: 6896e8ccca91
Create Date: 2025-11-01 14:41:56.344849

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5d6c56deb624"
down_revision: str | Sequence[str] | None = "6896e8ccca91"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("puzzles", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_source_puzzle_date", ["source_id", "puzzle_date"]
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("puzzles", schema=None) as batch_op:
        batch_op.drop_constraint("uq_source_puzzle_date", type_="unique")
