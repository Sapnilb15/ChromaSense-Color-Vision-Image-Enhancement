"""Page routes."""

from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Render the single workflow page."""
    templates = Jinja2Templates(directory=request.app.state.templates_dir)
    return templates.TemplateResponse(request, "index.html")


def mount_static(app: FastAPI, directory: Path) -> None:
    """Serve web_ui/static at /static. A router cannot hold a mount, so the app calls this."""
    app.mount("/static", StaticFiles(directory=directory), name="static")
