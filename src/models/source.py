"""Source model for puzzle feeds."""
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid
from src.database import Base

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.puzzle import Puzzle


class Source(Base):
    """Source model for puzzle feeds."""
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="sources")
    puzzles: Mapped[list["Puzzle"]] = relationship("Puzzle", back_populates="source", cascade="all, delete-orphan")
