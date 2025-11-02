"""Source model for puzzle feeds."""

from __future__ import annotations

import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.puzzle import Puzzle
    from src.models.user import User


class Source(Base):
    """Source model for puzzle feeds."""

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    short_code: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped[User] = relationship("User", back_populates="sources")
    puzzles: Mapped[list[Puzzle]] = relationship(
        "Puzzle", back_populates="source", cascade="all, delete-orphan"
    )

    @property
    def folder_name(self) -> str:
        """Return short_code if available, otherwise UUID."""
        return self.short_code if self.short_code else self.id

    @property
    def has_icon(self) -> bool:
        """Check if icon.png exists for this source."""
        from src.config import settings

        icon_path = settings.puzzles_path / self.folder_name / "icon.png"
        return icon_path.exists()

    def icon_url(self, base_url: str) -> str | None:
        """Return icon URL if icon exists, otherwise None."""
        if not self.has_icon:
            return None
        return f"{base_url}/sources/{self.folder_name}/icon.png"

    def create_folders(self, base_path: Path) -> None:
        """Create the folder structure for this source."""
        source_path = base_path / self.folder_name
        for subfolder in ["import", "puzzles", "errors"]:
            folder_path = source_path / subfolder
            folder_path.mkdir(parents=True, exist_ok=True)


@event.listens_for(Source, "after_insert")
def create_source_folders_on_insert(
    mapper: object, connection: object, target: Source
) -> None:
    """Automatically create folder structure when a source is inserted."""
    from src.config import settings

    target.create_folders(settings.puzzles_path)


@event.listens_for(Source, "after_delete")
def delete_source_folders_on_delete(
    mapper: object, connection: object, target: Source
) -> None:
    """Automatically delete folder structure when a source is deleted."""
    from src.config import settings

    source_path = settings.puzzles_path / target.folder_name
    if source_path.exists():
        shutil.rmtree(source_path)
