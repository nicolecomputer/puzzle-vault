from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from src.router import router
from src.config import settings

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    max_age=settings.SESSION_MAX_AGE
)

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

# Include all routes from router
app.include_router(router)
