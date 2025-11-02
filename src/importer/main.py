"""Main entry point for the puzzle importer service."""

import logging
import signal

from src.importer.watcher import ImportWatcher
from src.shared.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

watcher: ImportWatcher | None = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global watcher
    logger.info("Shutdown signal received, stopping...")
    if watcher:
        watcher.stop()


def main():
    """Start the importer service."""
    global watcher

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    data_path = settings.DATA_PATH
    puzzles_path = settings.puzzles_path

    logger.info("Starting puzzle importer service")
    logger.info(f"Data path: {data_path}")
    logger.info(f"Puzzles path: {puzzles_path}")

    watcher = ImportWatcher(puzzles_path)
    watcher.start()

    logger.info("Importer ready. Watching for new files. Press Ctrl+C to quit.")

    try:
        watcher.wait()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        if watcher:
            watcher.stop()

    logger.info("Importer service stopped")


if __name__ == "__main__":
    main()
