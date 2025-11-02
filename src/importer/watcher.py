"""File system watcher for puzzle import directories."""

import logging
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.importer.processor import FileProcessor

logger = logging.getLogger(__name__)


class ImportEventHandler(FileSystemEventHandler):
    """Handles file system events in import directories."""

    def __init__(self, processor: FileProcessor):
        self.processor = processor
        self._process_lock = threading.Lock()
        self._pending_process = False
        self._debounce_timer: threading.Timer | None = None

    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if event.is_directory:
            return

        if isinstance(event.src_path, bytes):
            return

        path = Path(event.src_path)
        if path.suffix in {".puz", ".json"}:
            logger.info(f"New file detected: {path.name}")
            self._schedule_process()

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if event.is_directory:
            return

        if isinstance(event.src_path, bytes):
            return

        path = Path(event.src_path)
        if path.suffix in {".puz", ".json"}:
            logger.debug(f"File modified: {path.name}")
            self._schedule_process()

    def _schedule_process(self):
        """Schedule a processing run with debouncing."""
        with self._process_lock:
            if self._debounce_timer:
                self._debounce_timer.cancel()

            self._debounce_timer = threading.Timer(1.0, self._run_process)
            self._debounce_timer.start()

    def _run_process(self):
        """Run the processor."""
        try:
            logger.info("Processing import directories...")
            self.processor.process_all()
            logger.info("Processing complete")
        except Exception as e:
            logger.exception(f"Error during processing: {e}")


class ImportWatcher:
    """Watches import directories for new puzzle files."""

    def __init__(self, puzzles_path: Path):
        self.puzzles_path = puzzles_path
        self.processor = FileProcessor()
        self.observer = Observer()
        self.event_handler = ImportEventHandler(self.processor)

    def start(self):
        """Start watching all import directories."""
        if not self.puzzles_path.exists():
            logger.warning(f"Puzzles path does not exist: {self.puzzles_path}")
            return

        watched_dirs = []
        for source_dir in self.puzzles_path.iterdir():
            if not source_dir.is_dir():
                continue

            import_dir = source_dir / "import"
            if import_dir.exists():
                self.observer.schedule(
                    self.event_handler, str(import_dir), recursive=False
                )
                watched_dirs.append(import_dir)
                logger.info(f"Watching: {import_dir}")

        if not watched_dirs:
            logger.warning("No import directories found to watch")
            return

        self.observer.start()
        logger.info(f"Started watching {len(watched_dirs)} import directories")

        logger.info("Running initial scan...")
        try:
            self.processor.process_all()
            logger.info("Initial scan complete")
        except Exception as e:
            logger.exception(f"Error during initial scan: {e}")

    def stop(self):
        """Stop watching."""
        try:
            self.observer.stop()
            self.observer.join(timeout=2.0)
        except Exception as e:
            logger.warning(f"Error stopping observer: {e}")
        logger.info("Stopped watching import directories")

    def wait(self):
        """Wait for the observer to finish (blocks until stop is called)."""
        try:
            while self.observer.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
