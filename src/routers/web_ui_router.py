"""Route handlers for the web UI."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import Response as StarletteResponse

from src.auth import get_user_from_session, require_auth, verify_password
from src.database import get_db
from src.feed_utils import paginate_items, sort_puzzles_by_date
from src.models.puzzle import Puzzle
from src.models.source import Source
from src.models.user import User
from src.pagination_utils import paginate
from src.source_utils import normalize_short_code

web_ui_router = APIRouter()


def get_templates() -> Jinja2Templates:
    """Get templates instance from main app."""
    from src.main import templates  # type: ignore[attr-defined]

    return templates


@web_ui_router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> StarletteResponse:
    """Serve the login page or redirect if already logged in."""
    if request.session.get("logged_in"):
        # Redirect to user puzzles page if already logged in
        user_id = request.session.get("username", "user")
        return RedirectResponse(url=f"/user/{user_id}/sources", status_code=303)

    templates = get_templates()
    return templates.TemplateResponse("index.html", {"request": request})


@web_ui_router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> StarletteResponse:
    """Handle login form submission."""
    # Query user from database
    user = db.query(User).filter(User.username == username).first()

    # Check if user exists and password is correct
    if user and verify_password(password, user.password_hash):
        # Set session
        request.session["logged_in"] = True
        request.session["username"] = username
        request.session["user_id"] = user.id
        # Redirect to user puzzles page
        return RedirectResponse(url=f"/user/{username}/sources", status_code=303)

    # Invalid credentials - show login page with error
    templates = get_templates()
    return templates.TemplateResponse(
        "index.html", {"request": request, "error": "Invalid username or password"}
    )


@web_ui_router.get("/logout")
async def logout(request: Request) -> StarletteResponse:
    """Log out the user and redirect to login page."""
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@web_ui_router.get("/user/{id}/sources", response_class=HTMLResponse)
@require_auth
async def user_sources(
    request: Request, id: str, page: int = 1, db: Session = Depends(get_db)
) -> StarletteResponse:
    """Display user's available sources."""
    user = get_user_from_session(request, db)

    query = (
        db.query(Source)
        .filter(Source.user_id == user.id)
        .order_by(Source.updated_at.desc())
    )
    all_sources = query.all()

    per_page = 30
    sources, total_pages, validated_page = paginate(all_sources, page, per_page)

    base_url = str(request.base_url).rstrip("/")

    templates = get_templates()
    return templates.TemplateResponse(
        "user_sources.html",
        {
            "request": request,
            "sources": sources,
            "page": validated_page,
            "total_pages": total_pages,
            "user_id": id,
            "base_url": base_url,
        },
    )


@web_ui_router.get("/sources/new", response_class=HTMLResponse)
@require_auth
async def new_source(request: Request) -> StarletteResponse:
    """Display form for creating a new source."""
    templates = get_templates()
    username = request.session.get("username")
    return templates.TemplateResponse(
        "new_source.html", {"request": request, "username": username}
    )


@web_ui_router.post("/sources", response_class=HTMLResponse)
@require_auth
async def create_source(
    request: Request,
    name: str = Form(...),
    short_code: str | None = Form(None),
    db: Session = Depends(get_db),
) -> StarletteResponse:
    """Create a new source and redirect to sources page."""
    user = get_user_from_session(request, db)
    username = request.session.get("username")

    normalized_short_code = normalize_short_code(short_code)

    source = Source(name=name, user_id=user.id, short_code=normalized_short_code)
    db.add(source)
    db.commit()

    return RedirectResponse(url=f"/user/{username}/sources", status_code=303)


@web_ui_router.get("/sources/{id}", response_class=HTMLResponse)
@require_auth
async def source_detail(
    request: Request, id: str, page: int = 1, db: Session = Depends(get_db)
) -> StarletteResponse:
    """Display source information page."""
    user = get_user_from_session(request, db)

    source = db.query(Source).filter(Source.id == id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    all_puzzles = sort_puzzles_by_date(source.puzzles)
    per_page = 30
    puzzles, total_pages, validated_page = paginate_items(all_puzzles, page, per_page)

    feed_identifier = source.short_code if source.short_code else source.id

    templates = get_templates()
    return templates.TemplateResponse(
        "source_detail.html",
        {
            "request": request,
            "source_title": source.name,
            "latest_puzzle_date": all_puzzles[0].puzzle_date if all_puzzles else "N/A",
            "total_puzzles": len(all_puzzles),
            "errors": 0,
            "feed_url": f"/feeds/{feed_identifier}.json?key={user.feed_key}",
            "feed_key": str(user.feed_key),
            "puzzles": puzzles,
            "source_id": id,
            "page": validated_page,
            "total_pages": total_pages,
        },
    )


@web_ui_router.get("/puzzles/{puzzle_id}/download", response_class=FileResponse)
@require_auth
async def download_puzzle(
    puzzle_id: str, db: Session = Depends(get_db)
) -> StarletteResponse:
    """Download a puzzle file."""
    puzzle = db.query(Puzzle).filter(Puzzle.id == puzzle_id).first()
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")

    file_path = Path(puzzle.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Puzzle file not found")

    return FileResponse(
        path=file_path,
        filename=f"{puzzle.title}.puz",
        media_type="application/x-crossword",
    )
