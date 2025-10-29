from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="src/templates")
app.mount("/static", StaticFiles(directory="src/templates"), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Serve the home page with Hello World message."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/feeds/{id}", response_class=HTMLResponse)
async def feed_detail(request: Request, id: str) -> HTMLResponse:
    """Display feed information page."""
    # TODO: This will be a lookup in the future
    feed_key = "user_key"

    # Mock data - replace with actual data source later
    feed_data = {
        "request": request,
        "source_title": "AVXC",
        "latest_puzzle_date": "October 29",
        "total_puzzles": 42,
        "errors": 0,
        "feed_url": f"/feeds/{id}.json?key={feed_key}"
    }

    return templates.TemplateResponse(
        "feed_detail.html",
        feed_data
    )


@app.get("/feeds/{id}.json")
async def get_feed(id: str, key: str) -> JSONResponse:
    """Return a JSON feed for the given ID and key."""
    feed_data = {
        "version": "https://jsonfeed.org/version/1.1",
    }
    return JSONResponse(content=feed_data)
