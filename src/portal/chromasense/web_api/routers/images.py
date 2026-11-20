"""Image routes: upload, enhance, view, and export."""

from typing import Annotated, Literal

from fastapi import APIRouter, File, Request, Response, UploadFile
from fastapi.concurrency import run_in_threadpool

from chromasense.core.errors import UploadRejected
from chromasense.core.models import UploadRejection, View
from chromasense.core.use_cases.enhance_image import EnhanceImageRequest
from chromasense.core.use_cases.export_image import ExportImageRequest
from chromasense.core.use_cases.process_upload import REJECTION_MESSAGES, ProcessUploadRequest
from chromasense.core.use_cases.render_view import RenderViewRequest
from chromasense.web_api.schemas import (
    EnhanceRequestBody,
    EnhanceResponseBody,
    PairBody,
    UploadResponseBody,
)
from color_engine.models import CvdProfile, CvdType

router = APIRouter(prefix="/api/image")


@router.post("", status_code=201, response_model=UploadResponseBody)
async def upload(request: Request, file: Annotated[UploadFile, File()]):
    max_bytes = request.app.state.max_upload_bytes
    # Read one byte past the limit, so an oversized body is refused before any decoding.
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        rejection = UploadRejection.TOO_LARGE
        raise UploadRejected(rejection, REJECTION_MESSAGES[rejection])
    use_case = request.app.state.use_cases.process_upload
    result = await run_in_threadpool(
        use_case.execute, ProcessUploadRequest(session_id=request.state.session_id, data=data)
    )
    return UploadResponseBody(width=result.width, height=result.height)


@router.post("/enhance", response_model=EnhanceResponseBody)
def enhance(request: Request, body: EnhanceRequestBody):
    profile = CvdProfile(CvdType(body.type), body.severity)
    result = request.app.state.use_cases.enhance_image.execute(
        EnhanceImageRequest(session_id=request.state.session_id, profile=profile)
    )
    return EnhanceResponseBody(
        outcome=result.outcome.value,
        message=result.message,
        eligible_count=result.eligible_count,
        improved_count=result.improved_count,
        pairs=[PairBody(**vars(pair)) for pair in result.pairs],
    )


@router.get("/view/{view}")
def view(request: Request, view: Literal["original", "enhanced"]):
    result = request.app.state.use_cases.render_view.execute(
        RenderViewRequest(session_id=request.state.session_id, view=View(view))
    )
    return Response(result.png, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.get("/export")
def export(request: Request):
    result = request.app.state.use_cases.export_image.execute(
        ExportImageRequest(session_id=request.state.session_id)
    )
    return Response(
        result.png,
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
            "Cache-Control": "no-store",
        },
    )
