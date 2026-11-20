"""Page routes."""

from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

router = APIRouter()


class _RevalidatedStaticFiles(StaticFiles):
    """Static files that the browser must check with the server before each reuse.

    Without a Cache-Control header, browsers guess how long to keep a file and can keep
    running scripts from an earlier build after the portal is rebuilt. ``no-cache`` keeps
    the cached copy but asks the server first, which answers 304 when the file is unchanged.
    """

    def file_response(self, *args, **kwargs):
        """Return the file response with ``Cache-Control: no-cache``."""
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache"
        return response


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Render the single workflow page."""
    templates = Jinja2Templates(directory=request.app.state.templates_dir)
    return templates.TemplateResponse(request, "index.html")


def mount_static(app: FastAPI, directory: Path) -> None:
    """Serve web_ui/static at /static. A router cannot hold a mount, so the app calls this."""
    app.mount("/static", _RevalidatedStaticFiles(directory=directory), name="static")
