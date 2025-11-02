"""Main entry point for the puzzle importer service."""

import logging
import signal
import time

from src.shared.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info("Shutdown signal received, stopping...")
    shutdown_requested = True


def main():
    """Start the importer service."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    data_path = settings.DATA_PATH
    puzzles_path = settings.puzzles_path

    logger.info("Starting puzzle importer service")
    logger.info(f"Data path: {data_path}")
    logger.info(f"Puzzles path: {puzzles_path}")
    logger.info("Importer ready. Press Ctrl+C to quit.")

    try:
        while not shutdown_requested:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")

    logger.info("Importer service stopped")


if __name__ == "__main__":
    main()
