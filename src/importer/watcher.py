"""Periodic scanner for puzzle import directories."""

import logging
import threading
import time
from pathlib import Path

from src.importer.processor import FileProcessor

logger = logging.getLogger(__name__)


class ImportScanner:
    """Periodically scans import directories for new puzzle files."""

    def __init__(self, puzzles_path: Path, scan_interval: int = 15):
        self.puzzles_path = puzzles_path
        self.scan_interval = scan_interval
        self.processor = FileProcessor()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self):
        """Start the periodic scanner."""
        if not self.puzzles_path.exists():
            logger.warning(f"Puzzles path does not exist: {self.puzzles_path}")
            return

        self._running = True
        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()

        logger.info(
            f"Started periodic scanner (interval: {self.scan_interval} seconds)"
        )

        logger.info("Running initial scan...")
        try:
            self.processor.process_all()
            logger.info("Initial scan complete")
        except Exception as e:
            logger.exception(f"Error during initial scan: {e}")

    def stop(self):
        """Stop the scanner."""
        logger.info("Stopping scanner...")
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Scanner stopped")

    def wait(self):
        """Wait for the scanner to finish (blocks until stop is called)."""
        try:
            while self._running and self._thread and self._thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    def _scan_loop(self):
        """Main scanning loop."""
        while self._running:
            try:
                # Sleep in 1-second intervals to respond quickly to shutdown
                for _ in range(self.scan_interval):
                    if not self._running:
                        return
                    time.sleep(1)

                if not self._running:
                    break

                self.processor.process_all()
            except Exception as e:
                logger.exception(f"Error during scan: {e}")
