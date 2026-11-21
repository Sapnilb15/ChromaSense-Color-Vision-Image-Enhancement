"""build_app with the real engine and store on a temporary data folder."""

import io
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from chromasense.main.settings import Settings
from chromasense.main.wiring import build_app

SAMPLES = Path(__file__).resolve().parents[3] / "color_engine" / "tests" / "data" / "samples"


def _red_green_png() -> bytes:
    pixels = np.full((60, 120, 3), 128, dtype=np.uint8)
    pixels[10:50, 10:55] = (200, 40, 40)
    pixels[10:50, 65:110] = (40, 160, 40)
    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG")
    return buffer.getvalue()


def _sessions(data_dir: Path) -> list[str]:
    folder = data_dir / "sessions"
    return sorted(path.name for path in folder.iterdir()) if folder.exists() else []


def test_full_workflow_and_session_end(tmp_path):
    with TestClient(build_app(Settings(data_dir=str(tmp_path)))) as client:
        upload = client.post("/api/image", files={"file": ("chart.png", _red_green_png())})
        assert upload.status_code == 201
        assert upload.json() == {"width": 120, "height": 60}

        original = client.get("/api/image/view/original")
        assert original.status_code == 200 and original.content[:4] == b"\x89PNG"

        enhanced = client.post("/api/image/enhance", json={"type": "deutan", "severity": 1.0})
        assert enhanced.status_code == 200
        assert enhanced.json()["outcome"] == "enhanced"

        export = client.get("/api/image/export")
        assert export.status_code == 200
        with Image.open(io.BytesIO(export.content)) as image:
            assert image.format == "PNG" and image.size == (120, 60)

        assert len(_sessions(tmp_path)) == 1
        assert client.post("/api/session/end").status_code == 204
        assert _sessions(tmp_path) == []


def test_renamed_text_file_is_415(tmp_path):
    data = (SAMPLES / "not_an_image.png").read_bytes()
    with TestClient(build_app(Settings(data_dir=str(tmp_path)))) as client:
        response = client.post("/api/image", files={"file": ("not.png", data)})
    assert response.status_code == 415
    assert response.json() == {
        "reason": "unsupported_type",
        "message": "This file is not a PNG or JPEG image.",
    }


def test_startup_deletes_every_leftover_session(tmp_path):
    leftover = tmp_path / "sessions" / "leftover-session-000000"
    leftover.mkdir(parents=True)
    (leftover / "original.json").write_text("{}")
    with TestClient(build_app(Settings(data_dir=str(tmp_path)))):
        assert _sessions(tmp_path) == []


def test_purge_task_runs_in_the_background(tmp_path):
    import time

    settings = Settings(data_dir=str(tmp_path), idle_minutes=1e-6)
    with TestClient(build_app(settings, purge_interval_seconds=0.05)) as client:
        client.post("/api/image", files={"file": ("chart.png", _red_green_png())})
        deadline = time.monotonic() + 5
        while _sessions(tmp_path) and time.monotonic() < deadline:
            time.sleep(0.05)
        assert _sessions(tmp_path) == []
