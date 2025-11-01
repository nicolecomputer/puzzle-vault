import time

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from src.config import settings
from src.router import router

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    max_age=settings.SESSION_MAX_AGE,
)

CACHE_BUSTER = str(int(time.time()))

templates = Jinja2Templates(directory="src/templates")
templates.env.globals["cache_buster"] = CACHE_BUSTER
app.mount("/static", StaticFiles(directory="src/templates"), name="static")

# Include all routes from router
app.include_router(router)
