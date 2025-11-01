"""Reset the database by recreating all tables."""

import shutil

from src.config import settings
from src.database import Base, engine
from src.models.puzzle import Puzzle  # noqa: F401
from src.models.source import Source  # noqa: F401
from src.models.user import User  # noqa: F401


def reset_database() -> None:
    """Drop all tables and recreate them."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset complete!")

    puzzles_path = settings.puzzles_path
    if puzzles_path.exists():
        for item in puzzles_path.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
                print(f"Removed puzzle folder: {item.name}")
    print("Puzzle folders cleaned!")


if __name__ == "__main__":
    reset_database()
