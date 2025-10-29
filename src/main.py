from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

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
async def home(request: Request) -> HTMLResponse:
    """Serve the home page with Hello World message."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/user/{id}/puzzles", response_class=HTMLResponse)
async def user_puzzles(request: Request, id: str) -> HTMLResponse:
    """Display user's available puzzles."""
    return templates.TemplateResponse(
        "user_puzzles.html",
        {
            "request": request,
            "puzzles": list(PUZZLES.values())
        }
    )


@app.get("/feeds/{id}", response_class=HTMLResponse)
async def feed_detail(request: Request, id: str) -> HTMLResponse:
    """Display feed information page."""
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


@app.get("/feeds/{id}.json")
async def get_feed(id: str, key: str) -> JSONResponse:
    """Return a JSON feed for the given ID and key."""
    feed_data = {
        "version": "https://jsonfeed.org/version/1.1",
    }
    return JSONResponse(content=feed_data)
