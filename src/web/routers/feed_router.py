"""Route handlers for public feed access."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import Response as StarletteResponse

from src.shared.config import settings
from src.shared.database import get_db
from src.shared.models.puzzle import Puzzle
from src.shared.models.source import Source
from src.shared.models.user import User
from src.shared.request_utils import get_base_url
from src.web.auth import (
    get_user_from_key,
    user_has_puzzle_access,
    user_has_source_access,
)
from src.web.feed_utils import build_feed_data, paginate_items, sort_puzzles_by_date

feed_router = APIRouter()


def get_templates() -> Jinja2Templates:
    """Get templates instance from main app."""
    from src.web.main import templates  # type: ignore[attr-defined]

    return templates


@feed_router.get("/feeds/{id}.json")
async def get_feed(
    id: str,
    request: Request,
    page: int = 1,
    user: User = Depends(get_user_from_key),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Return a JSON feed for the given ID and key.

    ID can be either a short_code or a UUID.
    Supports pagination with ?page=N parameter.
    """
    source = Source.find_by_id_or_short_code(id, db)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if not user_has_source_access(user, source):
        raise HTTPException(
            status_code=403,
            detail="Access denied: User does not have access to this source",
        )

    base_url = get_base_url(request)
    all_puzzles = sort_puzzles_by_date(source.puzzles)
    puzzles, total_pages, validated_page = paginate_items(all_puzzles, page)

    feed_data = build_feed_data(
        source, puzzles, base_url, str(user.feed_key), validated_page, total_pages
    )

    return JSONResponse(content=feed_data)


@feed_router.get("/puzzles/{puzzle_id}.preview.svg", response_class=FileResponse)
async def get_puzzle_preview(
    puzzle_id: str, db: Session = Depends(get_db)
) -> StarletteResponse:
    """Get puzzle preview image (public, no authentication required)."""
    puzzle = db.query(Puzzle).filter(Puzzle.id == puzzle_id).first()
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")

    preview_path = puzzle.preview_path()
    if not preview_path.exists():
        raise HTTPException(status_code=404, detail="Preview image not found")

    return FileResponse(
        path=preview_path,
        media_type="image/svg+xml",
        headers={"Content-Disposition": "inline"},
    )


@feed_router.get("/puzzles/{puzzle_id}.puz", response_class=FileResponse)
async def download_puzzle_by_key(
    puzzle_id: str,
    user: User = Depends(get_user_from_key),
    db: Session = Depends(get_db),
) -> StarletteResponse:
    """Download a puzzle file using feed key authentication."""
    puzzle = db.query(Puzzle).filter(Puzzle.id == puzzle_id).first()
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")

    if not user_has_puzzle_access(user, puzzle):
        raise HTTPException(
            status_code=403,
            detail="Access denied: User does not have access to this puzzle source",
        )

    file_path = Path(puzzle.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Puzzle file not found")

    return FileResponse(
        path=file_path,
        filename=f"{puzzle.title}.puz",
        media_type="application/x-crossword",
    )


@feed_router.get("/puzzles/{puzzle_id}")
async def puzzle_detail(
    puzzle_id: str,
    request: Request,
    user: User = Depends(get_user_from_key),
    db: Session = Depends(get_db),
) -> StarletteResponse:
    """Display puzzle detail page using feed key authentication."""
    puzzle = db.query(Puzzle).filter(Puzzle.id == puzzle_id).first()
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")

    if not user_has_puzzle_access(user, puzzle):
        raise HTTPException(
            status_code=403,
            detail="Access denied: User does not have access to this puzzle source",
        )

    source = db.query(Source).filter(Source.id == puzzle.source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    templates = get_templates()
    return templates.TemplateResponse(
        "puzzle_detail.html",
        {
            "request": request,
            "puzzle": puzzle,
            "source": source,
            "feed_key": str(user.feed_key),
        },
    )


@feed_router.get("/sources/{folder_name}/icon.png", response_class=FileResponse)
async def get_source_icon(
    folder_name: str, db: Session = Depends(get_db)
) -> StarletteResponse:
    """Get a source icon file (public, no authentication required)."""
    source = Source.find_by_id_or_short_code(folder_name, db)
    if not source:
        return JSONResponse({"error": "Source not found"}, status_code=404)

    icon_path = settings.puzzles_path / source.folder_name / "icon.png"
    if not icon_path.exists():
        return JSONResponse({"error": "Icon not found"}, status_code=404)

    return FileResponse(
        path=icon_path,
        media_type="image/png",
        headers={"Content-Disposition": "inline"},
    )
