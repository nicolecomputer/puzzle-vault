from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="src/templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Serve the home page with Hello World message."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/feed/{id}.json")
async def get_feed(id: str, key: str) -> JSONResponse:
    """Return a JSON feed for the given ID and key."""
    feed_data = {
        "version": "https://jsonfeed.org/version/1.1",
    }
    return JSONResponse(content=feed_data)
