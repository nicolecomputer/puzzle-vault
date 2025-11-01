"""File processor for importing puzzles from imports/ directories."""

import json
import logging
import shutil
from datetime import date, datetime
from pathlib import Path

import puz

from src.config import settings
from src.database import SessionLocal
from src.models.puzzle import Puzzle
from src.models.source import Source

logger = logging.getLogger(__name__)


class FileProcessor:
    """Processes puzzle files from /data/puzzles/{source-id}/imports/."""

    def __init__(self):
        self.data_dir = settings.puzzles_path

    def process_all(self):
        """Process all pending imports across all source directories."""
        if not self.data_dir.exists():
            logger.warning(f"Data directory does not exist: {self.data_dir}")
            return

        db = SessionLocal()
        try:
            sources = db.query(Source).all()
            source_lookup = {}
            for source in sources:
                source_lookup[source.folder_name] = source.id

            for source_dir in self.data_dir.iterdir():
                if not source_dir.is_dir():
                    continue

                folder_name = source_dir.name
                source_id = source_lookup.get(folder_name)

                if not source_id:
                    logger.warning(f"Unknown source folder: {folder_name}")
                    continue

                imports_dir = source_dir / "import"

                if not imports_dir.exists():
                    continue

                self._process_source(source_id, folder_name, imports_dir)
        finally:
            db.close()

    def _process_source(self, source_id: str, folder_name: str, imports_dir: Path):
        """Process all ready imports for a single source."""
        ready_pairs = self._find_ready_pairs(imports_dir)

        for puz_file, meta_file in ready_pairs:
            try:
                self._process_one(source_id, folder_name, puz_file, meta_file)
            except Exception as e:
                logger.exception(f"Failed to process {puz_file.name}")
                self._move_to_errors(folder_name, puz_file, meta_file, str(e))

    def _find_ready_pairs(self, imports_dir: Path) -> list[tuple[Path, Path]]:
        """Find all .puz files that have corresponding .meta.json files."""
        ready = []

        for puz_file in imports_dir.glob("*.puz"):
            meta_file = puz_file.with_suffix(".meta.json")

            if meta_file.exists():
                ready.append((puz_file, meta_file))

        return ready

    def _process_one(
        self, source_id: str, folder_name: str, puz_file: Path, meta_file: Path
    ):
        """Process a single puzzle import."""
        with open(meta_file) as f:
            metadata = json.load(f)

        puzzle_date = metadata.get("puzzle_date")
        if not puzzle_date:
            raise ValueError("Missing required field: puzzle_date")

        puzzle_file = puz.read(str(puz_file))

        title = metadata.get("title") or puzzle_file.title or "Untitled"
        author = metadata.get("author") or puzzle_file.author

        db = SessionLocal()
        try:
            puzzle = Puzzle(
                source_id=source_id,
                title=title,
                author=author,
                puzzle_date=date.fromisoformat(puzzle_date),
                file_path=str(puz_file),
            )

            db.add(puzzle)
            db.commit()
            db.refresh(puzzle)

            logger.info(f"Created puzzle {puzzle.id}: {title} ({puzzle_date})")

            self._move_to_puzzles(folder_name, puz_file, meta_file, puzzle.id)

        finally:
            db.close()

    def _move_to_puzzles(
        self, folder_name: str, puz_file: Path, meta_file: Path, puzzle_id: str
    ):
        """Move successfully processed files to puzzles/ directory."""
        puzzles_dir = self.data_dir / folder_name / "puzzles"
        puzzles_dir.mkdir(parents=True, exist_ok=True)

        dest_puz = puzzles_dir / f"{puzzle_id}.puz"
        dest_meta = puzzles_dir / f"{puzzle_id}.meta.json"

        shutil.move(str(puz_file), str(dest_puz))
        shutil.move(str(meta_file), str(dest_meta))

        logger.info(f"Moved files to {puzzles_dir}")

    def _move_to_errors(
        self, folder_name: str, puz_file: Path, meta_file: Path, error_msg: str
    ):
        """Move failed imports to errors/ directory."""
        errors_dir = self.data_dir / folder_name / "errors"
        errors_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_name = puz_file.stem

        dest_puz = errors_dir / f"{base_name}_{timestamp}.puz"
        dest_meta = errors_dir / f"{base_name}_{timestamp}.meta.json"
        error_file = errors_dir / f"{base_name}_{timestamp}.error.txt"

        shutil.move(str(puz_file), str(dest_puz))
        if meta_file.exists():
            shutil.move(str(meta_file), str(dest_meta))

        error_file.write_text(error_msg)

        logger.error(f"Moved failed import to {errors_dir}: {error_msg}")


def main():
    """Run processor once (for testing)."""
    logging.basicConfig(level=logging.INFO)
    processor = FileProcessor()
    processor.process_all()


if __name__ == "__main__":
    main()
