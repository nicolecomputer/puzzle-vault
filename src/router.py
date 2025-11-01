"""Route handlers for the puz-feed application."""

from typing import Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import Response as StarletteResponse

from src.auth import require_auth, verify_password
from src.database import get_db
from src.models.source import Source
from src.models.user import User

router = APIRouter()


def get_templates() -> Jinja2Templates:
    """Get templates instance from main app."""
    from src.main import templates  # type: ignore[attr-defined]

    return templates


def get_puzzles() -> dict[str, dict[str, Any]]:
    """Get puzzles data from main app."""
    from src.main import PUZZLES  # type: ignore[attr-defined]

    return PUZZLES


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> StarletteResponse:
    """Serve the login page or redirect if already logged in."""
    if request.session.get("logged_in"):
        # Redirect to user puzzles page if already logged in
        user_id = request.session.get("username", "user")
        return RedirectResponse(url=f"/user/{user_id}/puzzles", status_code=303)

    templates = get_templates()
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
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
        return RedirectResponse(url=f"/user/{username}/puzzles", status_code=303)

    # Invalid credentials - show login page with error
    templates = get_templates()
    return templates.TemplateResponse(
        "index.html", {"request": request, "error": "Invalid username or password"}
    )


@router.get("/logout")
async def logout(request: Request) -> StarletteResponse:
    """Log out the user and redirect to login page."""
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@router.get("/user/{id}/puzzles", response_class=HTMLResponse)
@require_auth
async def user_puzzles(request: Request, id: str) -> StarletteResponse:
    """Display user's available puzzles."""
    templates = get_templates()
    PUZZLES = get_puzzles()
    return templates.TemplateResponse(
        "user_puzzles.html", {"request": request, "puzzles": list(PUZZLES.values())}
    )


@router.get("/sources/new", response_class=HTMLResponse)
@require_auth
async def new_source(request: Request) -> StarletteResponse:
    """Display form for creating a new source."""
    templates = get_templates()
    username = request.session.get("username")
    return templates.TemplateResponse(
        "new_source.html", {"request": request, "username": username}
    )


@router.post("/sources", response_class=HTMLResponse)
@require_auth
async def create_source(
    request: Request,
    name: str = Form(...),
    db: Session = Depends(get_db),
) -> StarletteResponse:
    """Create a new source and redirect to puzzles page."""
    user_id = request.session.get("user_id")
    username = request.session.get("username")

    source = Source(name=name, user_id=user_id)
    db.add(source)
    db.commit()

    return RedirectResponse(url=f"/user/{username}/puzzles", status_code=303)


@router.get("/feeds/{id}.json")
async def get_feed(id: str, key: str) -> JSONResponse:
    """Return a JSON feed for the given ID and key."""
    feed_data = {
        "version": "https://jsonfeed.org/version/1.1",
    }
    return JSONResponse(content=feed_data)


@router.get("/feeds/{id}", response_class=HTMLResponse)
@require_auth
async def feed_detail(request: Request, id: str) -> StarletteResponse:
    """Display feed information page."""
    # TODO: This will be a lookup in the future
    feed_key = "user_key"

    # Get puzzle data from shared structure
    PUZZLES = get_puzzles()
    puzzle = PUZZLES.get(
        id,
        {
            "id": id,
            "name": "Unknown",
            "latest_puzzle_date": "N/A",
            "total_puzzles": 0,
            "errors": 0,
        },
    )

    feed_data = {
        "request": request,
        "source_title": puzzle["name"],
        "latest_puzzle_date": puzzle["latest_puzzle_date"],
        "total_puzzles": puzzle["total_puzzles"],
        "errors": puzzle["errors"],
        "feed_url": f"/feeds/{id}.json?key={feed_key}",
    }

    templates = get_templates()
    return templates.TemplateResponse("feed_detail.html", feed_data)
