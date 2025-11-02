"""Null agent - does nothing but log that it ran."""

import logging
from datetime import datetime

from src.agents.base_agent import BaseAgent, FetchResult
from src.agents.null.config import NullConfig
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
        # Parse config
        config = NullConfig.model_validate_json(source.agent_config or "{}")

        logger.info(f"🔵 Null agent running for source: {source.name}")

        if config.extra_string:
            logger.info(f"Extra config string: {config.extra_string}")

        logger.info("Null agent does nothing - this is a test agent")
        logger.info("No puzzles will be fetched")

        return FetchResult(
            success=True,
            puzzles_found=0,
            error_message=None,
            completed_at=datetime.utcnow(),
        )
