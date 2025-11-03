"""xword-dl agent - downloads puzzles using the xword-dl library."""

import json
import logging
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import xword_dl  # type: ignore[import]

from src.agents.base_agent import BaseAgent, FetchResult
from src.agents.xword_dl.config import XwordDlConfig
from src.shared.config import settings
from src.shared.models.source import Source

logger = logging.getLogger(__name__)


class XwordDlAgent(BaseAgent):
    """An agent that uses xword-dl to download puzzles from various outlets."""

    async def fetch_puzzles(self, source: Source) -> FetchResult:
        """
        Fetch puzzles using xword-dl.

        Args:
            source: The source to fetch puzzles for

        Returns:
            FetchResult with status information
        """
        # Parse config
        config = XwordDlConfig.model_validate_json(source.agent_config or "{}")

        logger.info(
            f"🔍 xword-dl agent running for source: {source.name} (outlet: {config.outlet_keyword})"
        )

        # Determine the import directory
        import_dir = settings.puzzles_path / source.folder_name / "import"
        import_dir.mkdir(parents=True, exist_ok=True)

        puzzles_found = 0
        errors = []

        # Determine timezone for date calculations
        # If source has timezone, use it; otherwise use system local time
        tz = ZoneInfo(source.timezone) if source.timezone else None
        now = datetime.now(tz=tz)

        # Fetch puzzles for the last N days (in the source's timezone)
        end_date = now.date()
        start_date = end_date - timedelta(days=config.days_to_fetch - 1)

        logger.info(
            f"Fetching {config.days_to_fetch} day(s) of puzzles from {start_date} to {end_date}"
            + (f" (timezone: {source.timezone})" if source.timezone else "")
        )

        current_date = start_date
        while current_date <= end_date:
            try:
                logger.info(f"Attempting to download puzzle for {current_date}")

                # Build kwargs for xword_dl
                kwargs = {"date": current_date.strftime("%Y-%m-%d")}

                # Add authentication if provided
                if config.username:
                    kwargs["username"] = config.username
                if config.password:
                    kwargs["password"] = config.password

                # Download the puzzle using xword-dl
                puzzle, filename = xword_dl.by_keyword(config.outlet_keyword, **kwargs)

                # Generate a safe filename from the date
                safe_filename = f"{config.outlet_keyword}_{current_date.isoformat()}"

                # Save the .puz file
                puz_path = import_dir / f"{safe_filename}.puz"
                puzzle.save(str(puz_path))
                logger.info(f"✅ Saved puzzle to {puz_path.name}")

                # Create metadata file
                metadata = {
                    "puzzle_date": current_date.isoformat(),
                    "title": puzzle.title or "Untitled",
                    "author": puzzle.author or None,
                }

                meta_path = import_dir / f"{safe_filename}.meta.json"
                with open(meta_path, "w") as f:
                    json.dump(metadata, f, indent=2)
                logger.info(f"✅ Saved metadata to {meta_path.name}")

                puzzles_found += 1

            except Exception as e:
                error_msg = f"Failed to download puzzle for {current_date}: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)

            current_date += timedelta(days=1)

        # Determine success
        success = puzzles_found > 0
        error_message = (
            None
            if success
            else "; ".join(errors)
            if errors
            else "No puzzles downloaded"
        )

        logger.info(
            f"🎯 Completed: {puzzles_found} puzzle(s) downloaded"
            + (f", {len(errors)} error(s)" if errors else "")
        )

        return FetchResult(
            success=success,
            puzzles_found=puzzles_found,
            error_message=error_message if not success else None,
            completed_at=datetime.now(UTC),
        )
