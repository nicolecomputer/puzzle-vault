"""Route handlers for public feed access."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from starlette.responses import Response as StarletteResponse

from src.database import get_db
from src.models.puzzle import Puzzle
from src.models.source import Source
from src.models.user import User

feed_router = APIRouter()


@feed_router.get("/feeds/{id}.json")
async def get_feed(id: str, key: str, db: Session = Depends(get_db)) -> JSONResponse:
    """Return a JSON feed for the given ID and key.

    ID can be either a short_code or a UUID.
    """
    # Authenticate user by feed key
    try:
        key_uuid = uuid.UUID(key)
    except ValueError:
        return JSONResponse({"error": "Invalid feed key"}, status_code=401)

    user = db.query(User).filter(User.feed_key == key_uuid).first()

    if not user:
        return JSONResponse({"error": "Invalid feed key"}, status_code=401)

    # Get the source - try short_code first, then UUID
    source = db.query(Source).filter(Source.short_code == id).first()
    if not source:
        source = db.query(Source).filter(Source.id == id).first()

    if not source:
        return JSONResponse({"error": "Source not found"}, status_code=404)

    # Check if user has access to this source
    source_ids = {src.id for src in user.sources}
    if source.id not in source_ids:
        return JSONResponse(
            {"error": "Access denied: User does not have access to this source"},
            status_code=403,
        )

    feed_data = {
        "version": "https://jsonfeed.org/version/1.1",
    }
    return JSONResponse(content=feed_data)


@feed_router.get("/puzzles/{puzzle_id}.puz", response_class=FileResponse)
async def download_puzzle_by_key(
    puzzle_id: str, key: str, db: Session = Depends(get_db)
) -> StarletteResponse:
    """Download a puzzle file using feed key authentication."""
    try:
        key_uuid = uuid.UUID(key)
    except ValueError:
        return JSONResponse({"error": "Invalid feed key"}, status_code=401)

    user = db.query(User).filter(User.feed_key == key_uuid).first()

    if not user:
        return JSONResponse({"error": "Invalid feed key"}, status_code=401)

    puzzle = db.query(Puzzle).filter(Puzzle.id == puzzle_id).first()

    if not puzzle:
        return JSONResponse({"error": "Puzzle not found"}, status_code=404)

    source_ids = {source.id for source in user.sources}
    if puzzle.source_id not in source_ids:
        return JSONResponse(
            {"error": "Access denied: User does not have access to this puzzle source"},
            status_code=403,
        )

    file_path = Path(puzzle.file_path)
    if not file_path.exists():
        return JSONResponse({"error": "Puzzle file not found"}, status_code=404)

    return FileResponse(
        path=file_path,
        filename=f"{puzzle.title}.puz",
        media_type="application/x-crossword",
    )
