"""Session route: the page sends this with navigator.sendBeacon when it closes."""

from fastapi import APIRouter, Request, Response

from chromasense.core.use_cases.end_session import EndSessionRequest

router = APIRouter(prefix="/api/session")


@router.post("/end", status_code=204)
def end(request: Request):
    """End the session and delete its images (``EndSession``)."""
    request.app.state.use_cases.end_session.execute(
        EndSessionRequest(session_id=request.state.session_id)
    )
    return Response(status_code=204)
