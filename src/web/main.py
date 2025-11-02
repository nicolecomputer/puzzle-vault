import time
from datetime import datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from src.shared.config import settings
from src.web.routers.feed_router import feed_router
from src.web.routers.web_ui_router import web_ui_router

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    max_age=settings.SESSION_MAX_AGE,
)

CACHE_BUSTER = str(int(time.time()))

templates = Jinja2Templates(directory="src/web/templates")
templates.env.globals["cache_buster"] = CACHE_BUSTER


def format_datetime(
    dt: datetime | None, format_str: str = "%b %d, %Y %I:%M:%S %p"
) -> str:
    """Format datetime with timezone awareness."""
    if dt is None:
        return "N/A"
    return dt.strftime(format_str)


templates.env.filters["format_datetime"] = format_datetime

app.mount("/static", StaticFiles(directory="src/web/templates"), name="static")

# Include all routes from routers
app.include_router(web_ui_router)
app.include_router(feed_router)
