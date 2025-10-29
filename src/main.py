from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
import secrets

from src.database import get_db
from src.models.user import User
from src.auth import verify_password

app = FastAPI()

# Add session middleware for login management
# Generate a random secret key for sessions (will change on restart - users will need to re-login)
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(32))

templates = Jinja2Templates(directory="src/templates")
app.mount("/static", StaticFiles(directory="src/templates"), name="static")

# Shared puzzle data structure
PUZZLES = {
    "avcx": {
        "id": "avcx",
        "name": "AVCX",
        "latest_puzzle_date": "October 29",
        "total_puzzles": 42,
        "errors": 0
    }
}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> Response:
    """Serve the login page or redirect if already logged in."""
    if request.session.get("logged_in"):
        # Redirect to user puzzles page if already logged in
        user_id = request.session.get("username", "user")
        return RedirectResponse(url=f"/user/{user_id}/puzzles", status_code=303)

    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
) -> Response:
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
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "error": "Invalid username or password"}
    )


@app.get("/logout")
async def logout(request: Request) -> Response:
    """Log out the user and redirect to login page."""
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)



@app.get("/user/{id}/puzzles", response_class=HTMLResponse)
async def user_puzzles(request: Request, id: str) -> Response:
    """Display user's available puzzles."""
    # Check if user is logged in
    if not request.session.get("logged_in"):
        return RedirectResponse(url="/", status_code=401)

    return templates.TemplateResponse(
        "user_puzzles.html",
        {
            "request": request,
            "puzzles": list(PUZZLES.values())
        }
    )


@app.get("/feeds/{id}.json")
async def get_feed(id: str, key: str) -> JSONResponse:
    """Return a JSON feed for the given ID and key."""
    feed_data = {
        "version": "https://jsonfeed.org/version/1.1",
    }
    return JSONResponse(content=feed_data)


@app.get("/feeds/{id}", response_class=HTMLResponse)
async def feed_detail(request: Request, id: str) -> Response:
    """Display feed information page."""
    # Check if user is logged in
    if not request.session.get("logged_in"):
        return RedirectResponse(url="/", status_code=401)

    # TODO: This will be a lookup in the future
    feed_key = "user_key"

    # Get puzzle data from shared structure
    puzzle = PUZZLES.get(id, {
        "id": id,
        "name": "Unknown",
        "latest_puzzle_date": "N/A",
        "total_puzzles": 0,
        "errors": 0
    })

    feed_data = {
        "request": request,
        "source_title": puzzle["name"],
        "latest_puzzle_date": puzzle["latest_puzzle_date"],
        "total_puzzles": puzzle["total_puzzles"],
        "errors": puzzle["errors"],
        "feed_url": f"/feeds/{id}.json?key={feed_key}"
    }

    return templates.TemplateResponse(
        "feed_detail.html",
        feed_data
    )
