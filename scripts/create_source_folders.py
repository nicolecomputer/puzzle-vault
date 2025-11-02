"""Create folder structure for existing sources.

This script ensures all existing sources have their required folder structure.
Run with: uv run python scripts/create_source_folders.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shared.config import settings
from src.shared.database import SessionLocal
from src.shared.models.source import Source


def main() -> None:
    """Create folder structure for all existing sources."""
    db_path = settings.DATA_PATH / "puzfeed.db"
    print(f"Database: {db_path}\n")

    if not db_path.exists():
        print("❌ Database not found. Run migrations first.")
        return

    db = SessionLocal()
    try:
        sources = db.query(Source).all()
        if not sources:
            print("No sources found in database.")
            return

        print(f"Creating folders for {len(sources)} source(s)...\n")
        for source in sources:
            source.create_folders(settings.puzzles_path)
            print(f"✓ Created folders for: {source.name} ({source.folder_name})")

        print("\n✓ All source folders created successfully!")
    except Exception as e:
        print(f"\n❌ Error creating folders: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
