"""Puzzle model for crossword puzzles."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.database import Base

if TYPE_CHECKING:
    from src.shared.models.source import Source


class Puzzle(Base):
    """Puzzle model for crossword puzzles."""

    __tablename__ = "puzzles"
    __table_args__ = (
        UniqueConstraint("source_id", "file_hash", name="uq_source_file_hash"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    source_id: Mapped[str] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=True)
    puzzle_date: Mapped[date] = mapped_column(Date, nullable=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=True)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    source: Mapped[Source] = relationship("Source", back_populates="puzzles")

    def preview_path(self) -> Path:
        """Get the path to the preview image for this puzzle.

        Returns:
            Path to the preview image file
        """
        puz_path = Path(self.file_path)
        if self.filename:
            preview_filename = Path(self.filename).stem + ".preview.svg"
            return puz_path.parent / preview_filename
        return puz_path.parent / f"{self.id}.preview.svg"

    def has_preview(self) -> bool:
        """Check if a preview image exists for this puzzle.

        Returns:
            True if preview image exists, False otherwise
        """
        return self.preview_path().exists()
