"""Base agent interface and types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

from src.shared.models.source import Source


@dataclass
class FetchResult:
    """Result of a fetch operation."""

    success: bool
    puzzles_found: int
    error_message: str | None = None
    completed_at: datetime | None = None


class BaseAgent(ABC):
    """Base class for all puzzle agents."""

    @abstractmethod
    async def fetch_puzzles(self, source: Source) -> FetchResult:
        """
        Fetch puzzles for the given source and place them in the import folder.

        Args:
            source: The source to fetch puzzles for

        Returns:
            FetchResult with status information
        """
        pass


class AgentConfig(BaseModel):
    """Base config class for agents."""

    pass
