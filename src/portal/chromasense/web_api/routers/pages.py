"""Page routes."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    templates = Jinja2Templates(directory=request.app.state.templates_dir)
    return templates.TemplateResponse(request, "index.html")
