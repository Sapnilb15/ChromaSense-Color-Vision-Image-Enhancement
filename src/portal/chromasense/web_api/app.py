"""Web API: a humble HTTP adapter. It caps the body, checks request shape, calls one use case,
and maps the result or error to a response. It holds no business rules."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from chromasense.core.errors import NoImageInSession, UploadRejected
from chromasense.core.models import UploadRejection
from chromasense.web_api.routers import images, pages, session
from chromasense.web_api.session_cookie import session_id_from, set_session_cookie

_STATUS_FOR_REJECTION = {
    UploadRejection.TOO_LARGE: 413,
    UploadRejection.UNSUPPORTED_TYPE: 415,
    UploadRejection.CORRUPT: 422,
    UploadRejection.TOO_MANY_PIXELS: 422,
}


@dataclass(frozen=True)
class UseCases:
    process_upload: Any
    enhance_image: Any
    render_view: Any
    export_image: Any
    end_session: Any


def create_app(
    use_cases: UseCases,
    max_upload_bytes: int,
    templates_dir: Path,
    lifespan: Callable | None = None,
) -> FastAPI:
    app = FastAPI(
        title="ChromaSense", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None
    )
    app.state.use_cases = use_cases
    app.state.max_upload_bytes = max_upload_bytes
    app.state.templates_dir = templates_dir

    @app.middleware("http")
    async def session_cookie(request: Request, call_next):
        session_id, is_new = session_id_from(request)
        request.state.session_id = session_id
        response = await call_next(request)
        if is_new:
            set_session_cookie(response, session_id)
        return response

    @app.exception_handler(UploadRejected)
    async def upload_rejected(request: Request, error: UploadRejected):
        return _error(_STATUS_FOR_REJECTION[error.reason], error.reason.value, error.message)

    @app.exception_handler(NoImageInSession)
    async def no_image(request: Request, error: NoImageInSession):
        return _error(404, "no_image", error.message)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError):
        return _error(422, "invalid_request", "The request is not valid.")

    app.include_router(pages.router)
    app.include_router(images.router)
    app.include_router(session.router)
    return app


def _error(status: int, reason: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"reason": reason, "message": message})
