"""Agent logging utilities for capturing agent run output."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from src.shared.models.source import Source


class AgentLogger:
    """Logger for capturing agent run output to JSON files."""

    def __init__(self, source: Source, data_path: Path) -> None:
        """
        Initialize agent logger.

        Args:
            source: Source being processed
            data_path: Base data path for logs
        """
        self.source = source
        self.source_id = source.folder_name
        self.started_at = datetime.utcnow()
        self.logs: list[dict[str, Any]] = []

        # Create agents directory structure
        self.agents_path = data_path / "agents" / self.source_id
        self.agents_path.mkdir(parents=True, exist_ok=True)

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        """
        Add a log entry.

        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
            **kwargs: Additional context to include
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs,
        }
        self.logs.append(entry)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.log("ERROR", message, **kwargs)

    def exception(self, message: str, exc: Exception) -> None:
        """Log exception."""
        self.log(
            "ERROR",
            message,
            exception=str(exc),
            exception_type=type(exc).__name__,
        )

    def save(
        self, success: bool, puzzles_found: int = 0, error_message: str | None = None
    ) -> Path:
        """
        Save the log file.

        Args:
            success: Whether the agent run succeeded
            puzzles_found: Number of puzzles found
            error_message: Error message if failed

        Returns:
            Path to the saved log file
        """
        completed_at = datetime.utcnow()

        # Format: YYYYMMDD_HHMMSS.json
        timestamp = self.started_at.strftime("%Y%m%d_%H%M%S")
        log_file = self.agents_path / f"{timestamp}.json"

        log_data = {
            "source_id": self.source.id,
            "source_name": self.source.name,
            "agent_type": self.source.agent_type,
            "started_at": self.started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": (completed_at - self.started_at).total_seconds(),
            "success": success,
            "puzzles_found": puzzles_found,
            "error_message": error_message,
            "logs": self.logs,
        }

        with open(log_file, "w") as f:
            json.dump(log_data, f, indent=2)

        return log_file


class AgentLogHandler(logging.Handler):
    """Logging handler that captures logs to AgentLogger."""

    def __init__(self, agent_logger: AgentLogger) -> None:
        """
        Initialize handler.

        Args:
            agent_logger: AgentLogger instance to write to
        """
        super().__init__()
        self.agent_logger = agent_logger

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record."""
        try:
            msg = self.format(record)
            self.agent_logger.log(
                record.levelname,
                msg,
                logger=record.name,
            )
        except Exception:
            self.handleError(record)
