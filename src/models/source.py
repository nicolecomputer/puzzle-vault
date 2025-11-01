"""Source model for puzzle feeds."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
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
