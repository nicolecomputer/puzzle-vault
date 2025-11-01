"""Route handlers for the puz-feed application."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import Response as StarletteResponse

from src.auth import require_auth, verify_password
from src.database import get_db
from src.models.puzzle import Puzzle
from src.models.source import Source
from src.models.user import User

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
    templates = get_templates()
    user_id = request.session.get("user_id")

    per_page = 30
    offset = (page - 1) * per_page

    query = db.query(Source).filter(Source.user_id == user_id)
    total_sources = query.count()
    sources = query.offset(offset).limit(per_page).all()

    total_pages = (total_sources + per_page - 1) // per_page

    return templates.TemplateResponse(
        "user_sources.html",
        {
            "request": request,
            "sources": sources,
            "page": page,
            "total_pages": total_pages,
            "user_id": id,
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
    """Create a new source and redirect to puzzles page."""
    user_id = request.session.get("user_id")
    username = request.session.get("username")

    if short_code:
        short_code = short_code.strip()
        if short_code == "":
            short_code = None

    source = Source(name=name, user_id=user_id, short_code=short_code)
    db.add(source)
    db.commit()

    return RedirectResponse(url=f"/user/{username}/sources", status_code=303)


@web_ui_router.get("/sources/{id}", response_class=HTMLResponse)
@require_auth
async def source_detail(
    request: Request, id: str, page: int = 1, db: Session = Depends(get_db)
) -> StarletteResponse:
    """Display source information page."""
    user_id = request.session.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    feed_key = str(user.feed_key) if user else ""

    source = db.query(Source).filter(Source.id == id).first()

    if source:
        source_name = source.name
        total_puzzles = len(source.puzzles)
        all_puzzles = sorted(
            source.puzzles, key=lambda p: p.puzzle_date or p.created_at, reverse=True
        )
        latest_puzzle_date = all_puzzles[0].puzzle_date if all_puzzles else None

        # Pagination
        per_page = 30
        offset = (page - 1) * per_page
        puzzles = all_puzzles[offset : offset + per_page]
        total_pages = (total_puzzles + per_page - 1) // per_page
    else:
        source_name = "Unknown"
        total_puzzles = 0
        puzzles = []
        latest_puzzle_date = None
        total_pages = 0

    feed_data = {
        "request": request,
        "source_title": source_name,
        "latest_puzzle_date": latest_puzzle_date or "N/A",
        "total_puzzles": total_puzzles,
        "errors": 0,
        "feed_url": f"/feeds/{id}.json?key={feed_key}",
        "puzzles": puzzles,
        "source_id": id,
        "page": page,
        "total_pages": total_pages,
    }

    templates = get_templates()
    return templates.TemplateResponse("source_detail.html", feed_data)


@web_ui_router.get("/puzzles/{puzzle_id}/download", response_class=FileResponse)
@require_auth
async def download_puzzle(
    puzzle_id: str, db: Session = Depends(get_db)
) -> StarletteResponse:
    """Download a puzzle file."""
    puzzle = db.query(Puzzle).filter(Puzzle.id == puzzle_id).first()

    if not puzzle:
        return JSONResponse({"error": "Puzzle not found"}, status_code=404)

    file_path = Path(puzzle.file_path)
    if not file_path.exists():
        return JSONResponse({"error": "Puzzle file not found"}, status_code=404)

    return FileResponse(
        path=file_path,
        filename=f"{puzzle.title}.puz",
        media_type="application/x-crossword",
    )
