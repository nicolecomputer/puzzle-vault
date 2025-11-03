"""Route handlers for the web UI."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import Response as StarletteResponse

from src.agents.registry import AGENT_REGISTRY
from src.shared.database import get_db
from src.shared.models.agent_task import AgentTask
from src.shared.models.puzzle import Puzzle
from src.shared.models.source import Source
from src.shared.models.user import User
from src.shared.request_utils import get_base_url
from src.web.auth import (
    get_user_from_session,
    has_any_users,
    hash_password,
    require_auth,
    verify_password,
)
from src.web.feed_utils import paginate_items, sort_puzzles_by_date
from src.web.pagination_utils import paginate
from src.web.source_utils import normalize_short_code

web_ui_router = APIRouter()


def get_templates() -> Jinja2Templates:
    """Get templates instance from main app."""
    from src.web.main import templates  # type: ignore[attr-defined]

    return templates


@web_ui_router.get("/api/agents")
@require_auth
async def list_agents(request: Request) -> dict:
    """Return list of available agents with their config schemas."""
    agents = []
    for agent_info in AGENT_REGISTRY.values():
        agents.append(
            {
                "type": agent_info.type,
                "name": agent_info.name,
                "description": agent_info.description,
                "config_schema": agent_info.config_schema.model_json_schema(),
                "ui_hints": agent_info.ui_hints,
                "presets": agent_info.presets,
            }
        )
    return {"agents": agents}


@web_ui_router.get("/api/sources/short-codes")
@require_auth
async def list_user_short_codes(
    request: Request, db: Session = Depends(get_db)
) -> dict:
    """Return list of short codes for the current user's sources."""
    user = get_user_from_session(request, db)
    sources = db.query(Source).filter(Source.user_id == user.id).all()
    short_codes = [s.short_code for s in sources if s.short_code]
    return {"short_codes": short_codes}


@web_ui_router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)) -> StarletteResponse:
    """Serve the login page or redirect if already logged in."""
    if request.session.get("logged_in"):
        # Redirect to user puzzles page if already logged in
        user_id = request.session.get("username", "user")
        return RedirectResponse(url=f"/user/{user_id}/sources", status_code=303)

    # Check if any users exist
    if not has_any_users(db):
        # No users exist, redirect to user creation
        return RedirectResponse(url="/users/new", status_code=303)

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

        # Check if user has sources
        has_sources = (
            db.query(Source).filter(Source.user_id == user.id).first() is not None
        )

        # Redirect to feed if they have sources, otherwise to sources page
        if has_sources:
            return RedirectResponse(url=f"/user/{username}/feeds/new", status_code=303)
        else:
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


@web_ui_router.get("/users/new", response_class=HTMLResponse)
async def new_user_form(
    request: Request, db: Session = Depends(get_db)
) -> StarletteResponse:
    """Display form to create the first user."""
    if has_any_users(db):
        return RedirectResponse(url="/", status_code=303)

    templates = get_templates()
    return templates.TemplateResponse("new_user.html", {"request": request})


@web_ui_router.post("/users", response_class=HTMLResponse)
async def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
) -> StarletteResponse:
    """Handle user creation (only if no users exist)."""
    if has_any_users(db):
        return RedirectResponse(url="/", status_code=303)

    if password != confirm_password:
        templates = get_templates()
        return templates.TemplateResponse(
            "new_user.html", {"request": request, "error": "Passwords do not match"}
        )

    if len(password) < 6:
        templates = get_templates()
        return templates.TemplateResponse(
            "new_user.html",
            {"request": request, "error": "Password must be at least 6 characters"},
        )

    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        templates = get_templates()
        return templates.TemplateResponse(
            "new_user.html",
            {"request": request, "error": "Username already exists"},
        )

    new_user = User(username=username, password_hash=hash_password(password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    request.session["logged_in"] = True
    request.session["username"] = username
    request.session["user_id"] = new_user.id

    return RedirectResponse(url=f"/user/{username}/sources", status_code=303)


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

    base_url = get_base_url(request)

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


@web_ui_router.get("/user/{id}/feeds/new", response_class=HTMLResponse)
@require_auth
async def user_feeds_new(
    request: Request, id: str, page: int = 1, db: Session = Depends(get_db)
) -> StarletteResponse:
    """Display all user's puzzles in reverse chronological order, 7 days per page."""
    user = get_user_from_session(request, db)

    all_puzzles = db.query(Puzzle).join(Source).filter(Source.user_id == user.id).all()
    sorted_puzzles = sort_puzzles_by_date(all_puzzles)

    if not sorted_puzzles:
        templates = get_templates()
        return templates.TemplateResponse(
            "user_feeds_new.html",
            {
                "request": request,
                "puzzles": [],
                "page": 1,
                "total_pages": 1,
                "user_id": id,
            },
        )

    # Group puzzles by date
    from collections import defaultdict

    puzzles_by_date = defaultdict(list)
    for puzzle in sorted_puzzles:
        puzzle_date = (
            puzzle.puzzle_date if puzzle.puzzle_date else puzzle.created_at.date()
        )
        puzzles_by_date[puzzle_date].append(puzzle)

    # Get unique dates in order
    unique_dates = sorted(puzzles_by_date.keys(), reverse=True)

    # Paginate by 7 days at a time
    days_per_page = 7
    total_pages = (len(unique_dates) + days_per_page - 1) // days_per_page
    validated_page = max(1, min(page, total_pages))

    start_idx = (validated_page - 1) * days_per_page
    end_idx = start_idx + days_per_page
    page_dates = unique_dates[start_idx:end_idx]

    # Get all puzzles for the dates on this page
    page_puzzles = []
    for puzzle_date in page_dates:
        page_puzzles.extend(puzzles_by_date[puzzle_date])

    templates = get_templates()
    return templates.TemplateResponse(
        "user_feeds_new.html",
        {
            "request": request,
            "puzzles": page_puzzles,
            "page": validated_page,
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


@web_ui_router.get("/sources/new_custom", response_class=HTMLResponse)
@require_auth
async def new_source_custom(request: Request) -> StarletteResponse:
    """Display form for creating a custom source."""
    templates = get_templates()
    username = request.session.get("username")
    return templates.TemplateResponse(
        "new_source_custom.html", {"request": request, "username": username}
    )


@web_ui_router.post("/sources/preset", response_class=HTMLResponse)
@require_auth
async def create_preset_source(
    request: Request,
    agent_type: str = Form(...),
    preset_data: str = Form(...),
    db: Session = Depends(get_db),
) -> StarletteResponse:
    """Create a new source from a preset configuration."""
    import json

    user = get_user_from_session(request, db)

    # Parse the preset data
    preset = json.loads(preset_data)

    normalized_short_code = normalize_short_code(preset.get("short_code"))

    # Auto-enable 3-hour schedule for preset agents
    schedule_enabled = True
    schedule_interval_hours = 3

    # Convert preset config to JSON string if it exists
    agent_config = None
    if "config" in preset and preset["config"]:
        agent_config = json.dumps(preset["config"])

    source = Source(
        name=preset["name"],
        user_id=user.id,
        short_code=normalized_short_code,
        timezone=None,
        agent_type=agent_type,
        agent_config=agent_config,
        agent_enabled=True,
        schedule_enabled=schedule_enabled,
        schedule_interval_hours=schedule_interval_hours,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    # Queue an immediate first run
    from datetime import datetime

    from src.shared.models.agent_task import AgentTask

    task = AgentTask(source_id=source.id, status="pending")
    db.add(task)
    source.last_scheduled_run_at = datetime.utcnow()
    db.commit()

    return RedirectResponse(url=f"/sources/{source.id}", status_code=303)


@web_ui_router.post("/sources", response_class=HTMLResponse)
@require_auth
async def create_source(
    request: Request,
    name: str = Form(...),
    short_code: str | None = Form(None),
    timezone: str | None = Form(None),
    agent_type: str | None = Form(None),
    agent_config: str | None = Form(None),
    agent_enabled: bool = Form(True),
    schedule_enabled: bool = Form(False),
    schedule_interval_hours: int | None = Form(None),
    db: Session = Depends(get_db),
) -> StarletteResponse:
    """Create a new source and redirect to sources page."""
    user = get_user_from_session(request, db)

    normalized_short_code = normalize_short_code(short_code)

    # Convert empty string to None for agent_type and timezone
    final_agent_type = agent_type if agent_type else None
    final_timezone = timezone if timezone else None

    # Auto-enable 3-hour schedule for preset agents
    final_schedule_enabled = schedule_enabled
    final_schedule_interval_hours = schedule_interval_hours
    if final_agent_type and not schedule_interval_hours:
        final_schedule_enabled = True
        final_schedule_interval_hours = 3

    source = Source(
        name=name,
        user_id=user.id,
        short_code=normalized_short_code,
        timezone=final_timezone,
        agent_type=final_agent_type,
        agent_config=agent_config,
        agent_enabled=agent_enabled,
        schedule_enabled=final_schedule_enabled,
        schedule_interval_hours=final_schedule_interval_hours,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    # If scheduling is enabled, queue an immediate first run
    if final_schedule_enabled and final_agent_type and agent_enabled:
        from datetime import datetime

        from src.shared.models.agent_task import AgentTask

        task = AgentTask(source_id=source.id, status="pending")
        db.add(task)
        source.last_scheduled_run_at = datetime.utcnow()
        db.commit()

    return RedirectResponse(url=f"/sources/{source.id}", status_code=303)


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

    # Get the latest agent run
    latest_run = (
        db.query(AgentTask)
        .filter(AgentTask.source_id == id)
        .order_by(AgentTask.queued_at.desc())
        .first()
    )

    # Check if there's a running or pending agent task
    has_running_agent = (
        db.query(AgentTask)
        .filter(AgentTask.source_id == id, AgentTask.status.in_(["pending", "running"]))
        .first()
    ) is not None

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
            "latest_run": latest_run,
            "schedule_enabled": source.schedule_enabled,
            "schedule_interval_hours": source.schedule_interval_hours,
            "next_run_at": source.next_run_at,
            "has_running_agent": has_running_agent,
        },
    )


@web_ui_router.get("/sources/{id}/agent", response_class=HTMLResponse)
@require_auth
async def agent_detail(
    request: Request, id: str, page: int = 1, db: Session = Depends(get_db)
) -> StarletteResponse:
    """Display agent runs for a source."""
    source = db.query(Source).filter(Source.id == id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    all_runs = (
        db.query(AgentTask)
        .filter(AgentTask.source_id == id)
        .order_by(AgentTask.queued_at.desc())
        .all()
    )

    per_page = 30
    runs, total_pages, validated_page = paginate(all_runs, page, per_page)

    runs_with_duration = []
    for run in runs:
        duration = None
        if run.started_at and run.completed_at:
            delta = run.completed_at - run.started_at
            total_seconds = int(delta.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            if minutes > 0:
                duration = f"{minutes}m {seconds}s"
            else:
                duration = f"{seconds}s"
        runs_with_duration.append({"duration": duration, **run.__dict__})

    templates = get_templates()
    return templates.TemplateResponse(
        "agent_detail.html",
        {
            "request": request,
            "source_title": source.name,
            "agent_type": source.agent_type,
            "agent_enabled": source.agent_enabled,
            "schedule_enabled": source.schedule_enabled,
            "schedule_interval_hours": source.schedule_interval_hours,
            "last_scheduled_run_at": source.last_scheduled_run_at,
            "next_run_at": source.next_run_at,
            "total_runs": len(all_runs),
            "runs": runs_with_duration,
            "source_id": id,
            "page": validated_page,
            "total_pages": total_pages,
        },
    )


@web_ui_router.post("/agents/run")
@require_auth
async def enqueue_agent_run(
    request: Request,
    source_id: str = Form(...),
    return_url: str = Form(None),
    db: Session = Depends(get_db),
) -> StarletteResponse:
    """Enqueue an agent run for a source."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if not source.agent_enabled or not source.agent_type:
        raise HTTPException(status_code=400, detail="Agent not enabled for this source")

    task = AgentTask(source_id=source_id, status="pending")
    db.add(task)
    db.commit()

    # Redirect to return_url if provided, otherwise to agent page
    redirect_url = return_url if return_url else f"/sources/{source_id}/agent"
    return RedirectResponse(url=redirect_url, status_code=303)


@web_ui_router.get("/agents/runs/{run_id}", response_class=HTMLResponse)
@require_auth
async def agent_run_detail(
    request: Request, run_id: str, db: Session = Depends(get_db)
) -> StarletteResponse:
    """Display details and logs for a specific agent run."""
    import json
    from datetime import datetime

    from src.shared.config import settings

    run = db.query(AgentTask).filter(AgentTask.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    source = db.query(Source).filter(Source.id == run.source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    log_data = None
    log_file_path = None

    if run.started_at:
        timestamp = run.started_at.strftime("%Y%m%d_%H%M%S")
        source_folder = source.short_code if source.short_code else source.id
        log_file_path = (
            settings.DATA_PATH / "agents" / source_folder / f"{timestamp}.json"
        )

        if log_file_path.exists():
            with open(log_file_path) as f:
                log_data = json.load(f)

            if log_data and "logs" in log_data:
                for log in log_data["logs"]:
                    if "timestamp" in log:
                        try:
                            log["timestamp"] = datetime.fromisoformat(log["timestamp"])
                        except (ValueError, TypeError):
                            pass

    templates = get_templates()
    return templates.TemplateResponse(
        "agent_run_detail.html",
        {
            "request": request,
            "run": run,
            "source": source,
            "log_data": log_data,
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
