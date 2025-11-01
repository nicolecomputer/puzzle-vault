"""Route handlers for public feed access."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import Response as StarletteResponse

from src.config import settings
from src.database import get_db
from src.models.puzzle import Puzzle
from src.models.source import Source
from src.models.user import User

feed_router = APIRouter()


def get_templates() -> Jinja2Templates:
    """Get templates instance from main app."""
    from src.main import templates  # type: ignore[attr-defined]

    return templates


def get_base_url(request: Request) -> str:
    """Get the base URL for the application.

    Uses BASE_URL from config if set, otherwise falls back to request URL.
    """
    if settings.BASE_URL:
        return settings.BASE_URL.rstrip("/")

    # Fall back to request scheme and host
    return f"{request.url.scheme}://{request.url.netloc}"


@feed_router.get("/feeds/{id}.json")
async def get_feed(
    id: str,
    key: str,
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Return a JSON feed for the given ID and key.

    ID can be either a short_code or a UUID.
    Supports pagination with ?page=N parameter.
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

    # Get base URL for constructing absolute URLs
    base_url = get_base_url(request)

    # Use short_code if available for feed identifier
    feed_identifier = source.short_code if source.short_code else source.id

    # Sort puzzles by puzzle_date (most recent first)
    # Puzzles without dates go to the end
    all_puzzles = sorted(
        source.puzzles,
        key=lambda p: p.puzzle_date if p.puzzle_date else p.created_at,
        reverse=True,
    )

    # Pagination
    per_page = 50
    total_puzzles = len(all_puzzles)
    total_pages = (total_puzzles + per_page - 1) // per_page if total_puzzles > 0 else 1

    # Ensure page is within valid range
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page
    puzzles = all_puzzles[offset : offset + per_page]

    # Build feed data
    feed_data: dict[str, object] = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": source.name,
        "home_page_url": f"{base_url}/sources/{source.id}",
        "feed_url": f"{base_url}/feeds/{feed_identifier}.json?key={key}",
        "description": f"A Puzzlecast feed for source: {source.name}",
    }

    # Add next_url if there are more pages
    if page < total_pages:
        feed_data["next_url"] = (
            f"{base_url}/feeds/{feed_identifier}.json?key={key}&page={page + 1}"
        )

    # Build items array
    items: list[dict[str, object]] = []
    for puzzle in puzzles:
        # Build the item URL (puzzle detail page)
        item_url = f"{base_url}/puzzles/{puzzle.id}?key={key}"

        # Create the item
        item: dict[str, object] = {
            "id": item_url,  # Use full URL as ID per spec recommendation
            "url": item_url,
            "title": puzzle.title,
        }

        # Add content_text (required by spec - must have content_text or content_html)
        # Build a simple description of the puzzle
        content_parts = [puzzle.title]
        if puzzle.author:
            content_parts.append(f"By {puzzle.author}")
        if puzzle.puzzle_date:
            content_parts.append(
                f"Published {puzzle.puzzle_date.strftime('%B %d, %Y')}"
            )
        item["content_text"] = " • ".join(content_parts)

        # Add author if present
        if puzzle.author:
            item["authors"] = [{"name": puzzle.author}]

        # Add date_published if puzzle_date is present
        if puzzle.puzzle_date:
            # Convert date to RFC 3339 format (YYYY-MM-DD with time at midnight UTC)
            item["date_published"] = f"{puzzle.puzzle_date.isoformat()}T00:00:00Z"

        # Add attachment for the .puz file
        download_url = f"{base_url}/puzzles/{puzzle.id}.puz?key={key}"
        item["attachments"] = [
            {
                "url": download_url,
                "mime_type": "application/x-crossword",
            }
        ]

        items.append(item)

    feed_data["items"] = items

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


@feed_router.get("/puzzles/{puzzle_id}")
async def puzzle_detail(
    puzzle_id: str, key: str, request: Request, db: Session = Depends(get_db)
) -> StarletteResponse:
    """Display puzzle detail page using feed key authentication."""
    # Authenticate user by feed key
    try:
        key_uuid = uuid.UUID(key)
    except ValueError:
        return JSONResponse({"error": "Invalid feed key"}, status_code=401)

    user = db.query(User).filter(User.feed_key == key_uuid).first()

    if not user:
        return JSONResponse({"error": "Invalid feed key"}, status_code=401)

    # Get the puzzle
    puzzle = db.query(Puzzle).filter(Puzzle.id == puzzle_id).first()

    if not puzzle:
        return JSONResponse({"error": "Puzzle not found"}, status_code=404)

    # Check if user has access to this puzzle's source
    source_ids = {source.id for source in user.sources}
    if puzzle.source_id not in source_ids:
        return JSONResponse(
            {"error": "Access denied: User does not have access to this puzzle source"},
            status_code=403,
        )

    # Get the source information
    source = db.query(Source).filter(Source.id == puzzle.source_id).first()

    if not source:
        return JSONResponse({"error": "Source not found"}, status_code=404)

    templates = get_templates()
    return templates.TemplateResponse(
        "puzzle_detail.html",
        {
            "request": request,
            "puzzle": puzzle,
            "source": source,
            "feed_key": key,
        },
    )
