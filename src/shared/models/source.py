"""Source model for puzzle feeds."""

from __future__ import annotations

import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, event
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.shared.database import Base

if TYPE_CHECKING:
    from src.shared.models.puzzle import Puzzle
    from src.shared.models.user import User


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
    timezone: Mapped[str | None] = mapped_column(String, nullable=True)
    agent_type: Mapped[str | None] = mapped_column(String, nullable=True)
    agent_config: Mapped[str | None] = mapped_column(String, nullable=True)
    agent_enabled: Mapped[bool] = mapped_column(default=False)
    schedule_enabled: Mapped[bool] = mapped_column(default=False)
    schedule_interval_hours: Mapped[int | None] = mapped_column(nullable=True)
    last_scheduled_run_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
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
    def next_run_at(self) -> datetime | None:
        """Calculate next scheduled run time."""
        if not self.schedule_enabled or not self.schedule_interval_hours:
            return None

        # If never run, next run is now (will be picked up by scheduler)
        if not self.last_scheduled_run_at:
            return datetime.utcnow()

        return self.last_scheduled_run_at + timedelta(
            hours=self.schedule_interval_hours
        )

    @property
    def has_icon(self) -> bool:
        """Check if icon.png exists for this source."""
        from src.shared.config import settings

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

    @classmethod
    def find_by_id_or_short_code(cls, identifier: str, db: Session) -> Source | None:
        """Find a source by short_code or UUID.

        Args:
            identifier: Either a short_code or UUID string
            db: Database session

        Returns:
            Source if found, None otherwise
        """
        source = db.query(cls).filter(cls.short_code == identifier).first()
        if not source:
            source = db.query(cls).filter(cls.id == identifier).first()
        return source


@event.listens_for(Source, "after_insert")
def create_source_folders_on_insert(
    mapper: object, connection: object, target: Source
) -> None:
    """Automatically create folder structure when a source is inserted."""
    from src.shared.config import settings

    target.create_folders(settings.puzzles_path)


@event.listens_for(Source, "after_delete")
def delete_source_folders_on_delete(
    mapper: object, connection: object, target: Source
) -> None:
    """Automatically delete folder structure when a source is deleted."""
    from src.shared.config import settings

    source_path = settings.puzzles_path / target.folder_name
    if source_path.exists():
        shutil.rmtree(source_path)
