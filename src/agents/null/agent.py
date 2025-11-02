"""Null agent - does nothing but log that it ran."""

import logging
from datetime import datetime

from src.agents.base_agent import BaseAgent, FetchResult
from src.shared.models.source import Source

logger = logging.getLogger(__name__)


class NullAgent(BaseAgent):
    """A null agent that just prints a message and exits."""

    async def fetch_puzzles(self, source: Source) -> FetchResult:
        """
        Fetch puzzles - does nothing but log.

        Args:
            source: The source to "fetch" puzzles for

        Returns:
            FetchResult indicating success with 0 puzzles found
        """
        logger.info(f"🔵 Null agent is alive! Running for source: {source.name}")
        print(f"🔵 Null agent is alive! Running for source: {source.name}")

        return FetchResult(
            success=True,
            puzzles_found=0,
            error_message=None,
            completed_at=datetime.utcnow(),
        )
