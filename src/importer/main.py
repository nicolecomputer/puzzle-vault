"""Main entry point for the puzzle importer service."""

import logging
import signal

from src.importer.watcher import ImportScanner
from src.shared.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

scanner: ImportScanner | None = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global scanner
    logger.info("Shutdown signal received, stopping...")
    if scanner:
        scanner.stop()


def main():
    """Start the importer service."""
    global scanner

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    data_path = settings.DATA_PATH
    puzzles_path = settings.puzzles_path

    logger.info("Starting puzzle importer service")
    logger.info(f"Data path: {data_path}")
    logger.info(f"Puzzles path: {puzzles_path}")

    scan_interval = settings.IMPORTER_SCAN_INTERVAL
    scanner = ImportScanner(puzzles_path, scan_interval=scan_interval)
    scanner.start()

    logger.info(
        f"Importer ready. Scanning every {scan_interval} seconds. Press Ctrl+C to quit."
    )

    try:
        scanner.wait()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        if scanner:
            scanner.stop()

    logger.info("Importer service stopped")


if __name__ == "__main__":
    main()
