"""Web API tests with fake use cases: routing, cookie, body cap, and error mapping."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from chromasense.core.errors import NoImageInSession, UploadRejected
from chromasense.core.models import Outcome, PairOutcome, UploadRejection, View
from chromasense.core.use_cases.process_upload import REJECTION_MESSAGES
from chromasense.web_api.app import UseCases, create_app
from chromasense.web_api.session_cookie import COOKIE_NAME
from color_engine.models import CvdType

TEMPLATES = Path(__file__).resolve().parents[2] / "chromasense" / "web_ui" / "templates"
MAX_BYTES = 10 * 1024 * 1024
SESSION = "known-session-id-0123456789"


class FakeUseCase:
    def __init__(self, result=None, error=None):
        self.result, self.error, self.requests = result, error, []

    def execute(self, request):
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.result


def _use_cases(**overrides):
    defaults = {
        "process_upload": FakeUseCase(SimpleNamespace(image_id="i", width=60, height=40)),
        "enhance_image": FakeUseCase(
            SimpleNamespace(
                outcome=Outcome.ENHANCED,
                message="Adjusted 1 of 1 color pairs likely to be confused.",
                eligible_count=1,
                improved_count=1,
                pairs=(PairOutcome("#c82828", "#28a028", 7.0, 13.6, True),),
            )
        ),
        "render_view": FakeUseCase(SimpleNamespace(png=b"\x89PNG-view", image_id="i")),
        "export_image": FakeUseCase(
            SimpleNamespace(png=b"\x89PNG-export", filename="chromasense-enhanced.png")
        ),
        "end_session": FakeUseCase(None),
    }
    defaults.update(overrides)
    return UseCases(**defaults)


def _client(use_cases, session=SESSION):
    client = TestClient(create_app(use_cases, MAX_BYTES, TEMPLATES))
    if session:
        client.cookies.set(COOKIE_NAME, session)
    return client


def test_new_browser_gets_a_session_cookie():
    client = _client(_use_cases(), session=None)
    response = client.get("/")
    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{COOKIE_NAME}=")
    assert "httponly" in cookie.lower() and "samesite=lax" in cookie.lower()


def test_known_session_keeps_its_cookie_and_is_passed_to_use_cases():
    use_cases = _use_cases()
    response = _client(use_cases).post("/api/image", files={"file": ("a.png", b"data")})
    assert "set-cookie" not in response.headers
    assert use_cases.process_upload.requests[0].session_id == SESSION


def test_invalid_cookie_is_replaced():
    use_cases = _use_cases()
    response = _client(use_cases, session="../bad").post(
        "/api/image", files={"file": ("a.png", b"data")}
    )
    assert response.headers["set-cookie"].startswith(f"{COOKIE_NAME}=")
    assert use_cases.process_upload.requests[0].session_id != "../bad"


def test_index_page_renders():
    response = _client(_use_cases()).get("/")
    assert response.status_code == 200
    assert "ChromaSense" in response.text


def test_upload_returns_201_with_size():
    use_cases = _use_cases()
    response = _client(use_cases).post("/api/image", files={"file": ("a.png", b"image bytes")})
    assert response.status_code == 201
    assert response.json() == {"width": 60, "height": 40}
    assert use_cases.process_upload.requests[0].data == b"image bytes"


def test_body_over_ten_megabytes_gets_413_without_calling_the_use_case():
    use_cases = _use_cases()
    data = b"\0" * (MAX_BYTES + 1024 * 1024)
    response = _client(use_cases).post("/api/image", files={"file": ("big.png", data)})
    assert response.status_code == 413
    assert response.json() == {
        "reason": "too_large",
        "message": REJECTION_MESSAGES[UploadRejection.TOO_LARGE],
    }
    assert use_cases.process_upload.requests == []


@pytest.mark.parametrize(
    ("reason", "status"),
    [
        (UploadRejection.UNSUPPORTED_TYPE, 415),
        (UploadRejection.CORRUPT, 422),
        (UploadRejection.TOO_MANY_PIXELS, 422),
        (UploadRejection.TOO_LARGE, 413),
    ],
)
def test_upload_rejections_map_to_status_and_message(reason, status):
    error = UploadRejected(reason, REJECTION_MESSAGES[reason])
    use_cases = _use_cases(process_upload=FakeUseCase(error=error))
    response = _client(use_cases).post("/api/image", files={"file": ("a.png", b"x")})
    assert response.status_code == status
    assert response.json() == {"reason": reason.value, "message": REJECTION_MESSAGES[reason]}


def test_upload_without_a_file_is_invalid():
    response = _client(_use_cases()).post("/api/image")
    assert response.status_code == 422
    assert response.json()["reason"] == "invalid_request"


def test_enhance_returns_the_outcome():
    use_cases = _use_cases()
    response = _client(use_cases).post(
        "/api/image/enhance", json={"type": "deutan", "severity": 0.8}
    )
    assert response.status_code == 200
    assert response.json() == {
        "outcome": "enhanced",
        "message": "Adjusted 1 of 1 color pairs likely to be confused.",
        "eligible_count": 1,
        "improved_count": 1,
        "pairs": [
            {
                "color_a_hex": "#c82828",
                "color_b_hex": "#28a028",
                "before": 7.0,
                "after": 13.6,
                "improved": True,
            }
        ],
    }
    profile = use_cases.enhance_image.requests[0].profile
    assert (profile.type, profile.severity) == (CvdType.DEUTAN, 0.8)


@pytest.mark.parametrize(
    "body",
    [
        {"type": "tritan", "severity": 0.5},
        {"type": "deutan", "severity": 1.5},
        {"type": "deutan", "severity": -0.1},
        {"type": "protan"},
        {},
    ],
)
def test_enhance_rejects_an_invalid_body(body):
    use_cases = _use_cases()
    response = _client(use_cases).post("/api/image/enhance", json=body)
    assert response.status_code == 422
    assert response.json() == {"reason": "invalid_request", "message": "The request is not valid."}
    assert use_cases.enhance_image.requests == []


def test_enhance_with_no_image_is_404():
    use_cases = _use_cases(
        enhance_image=FakeUseCase(error=NoImageInSession("Upload an image first."))
    )
    response = _client(use_cases).post("/api/image/enhance", json={"type": "protan", "severity": 1})
    assert response.status_code == 404
    assert response.json() == {"reason": "no_image", "message": "Upload an image first."}


@pytest.mark.parametrize("view", ["original", "enhanced"])
def test_view_returns_png_that_is_not_cached(view):
    use_cases = _use_cases()
    response = _client(use_cases).get(f"/api/image/view/{view}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "no-store"
    assert response.content == b"\x89PNG-view"
    assert use_cases.render_view.requests[0].view is View(view)


def test_unknown_view_is_invalid():
    use_cases = _use_cases()
    response = _client(use_cases).get("/api/image/view/simulated")
    assert response.status_code == 422
    assert use_cases.render_view.requests == []


def test_view_with_nothing_to_show_is_404():
    error = NoImageInSession("There is no enhanced image yet.")
    response = _client(_use_cases(render_view=FakeUseCase(error=error))).get(
        "/api/image/view/enhanced"
    )
    assert response.status_code == 404
    assert response.json()["message"] == "There is no enhanced image yet."


def test_export_is_a_png_attachment():
    response = _client(_use_cases()).get("/api/image/export")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert (
        response.headers["content-disposition"] == 'attachment; filename="chromasense-enhanced.png"'
    )
    assert response.content == b"\x89PNG-export"


def test_export_with_nothing_to_download_is_404():
    error = NoImageInSession("There is no enhanced image to download.")
    response = _client(_use_cases(export_image=FakeUseCase(error=error))).get("/api/image/export")
    assert response.status_code == 404
    assert response.json()["message"] == "There is no enhanced image to download."


def test_end_session_returns_204_for_this_session():
    use_cases = _use_cases()
    response = _client(use_cases).post("/api/session/end")
    assert response.status_code == 204
    assert use_cases.end_session.requests[0].session_id == SESSION


def test_no_other_routes_exist():
    from chromasense.web_api.routers import images, pages, session

    paths = sorted(
        (route.path, sorted(route.methods))
        for router in (pages.router, images.router, session.router)
        for route in router.routes
    )
    assert paths == [
        ("/", ["GET"]),
        ("/api/image", ["POST"]),
        ("/api/image/enhance", ["POST"]),
        ("/api/image/export", ["GET"]),
        ("/api/image/view/{view}", ["GET"]),
        ("/api/session/end", ["POST"]),
    ]


@pytest.mark.parametrize("path", ["/openapi.json", "/docs", "/redoc"])
def test_framework_documentation_routes_are_off(path):
    assert _client(_use_cases()).get(path).status_code == 404
