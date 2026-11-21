"""SRS-NFR-001: a valid image within the limits is processed, or rejected, within 30 seconds.

Run on the reference host, the dev container limited to 4 CPU cores and 8 GB:

    docker compose run --rm dev pytest src/portal/tests/performance -s
"""

import io
import time

import numpy as np
import pytest
from PIL import Image

from chromasense.core.errors import UploadRejected
from chromasense.core.models import Outcome, ProcessingSettings, UploadRejection
from chromasense.core.use_cases.enhance_image import EnhanceImage, EnhanceImageRequest
from chromasense.core.use_cases.export_image import ExportImage, ExportImageRequest
from chromasense.core.use_cases.process_upload import ProcessUpload, ProcessUploadRequest
from chromasense.main.wiring import SystemClock
from chromasense.storage.filesystem_session_image_store import FilesystemSessionImageStore
from color_engine.models import CvdProfile, CvdType

pytestmark = pytest.mark.performance

SESSION = "performance-session-0000"
LIMIT_SECONDS = 30.0
REJECTION_LIMIT_SECONDS = 2.0
MAX_BYTES = 10 * 1024 * 1024


def _red_green_base() -> np.ndarray:
    base = np.full((3000, 4000, 3), 128, dtype=np.int16)
    base[:, :2000] = (200, 40, 40)
    base[1500:, 2000:] = (40, 160, 40)
    return base


def _encode(pixels: np.ndarray, image_format: str, **options) -> bytes:
    buffer = io.BytesIO()
    Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8)).save(buffer, image_format, **options)
    return buffer.getvalue()


def _png_with_cell_noise() -> bytes:
    """12 MP PNG with noise in 2 x 2 cells; per-pixel noise would push a PNG past 10 MB."""
    noise = np.random.default_rng(0).integers(-10, 11, size=(1500, 2000, 3))
    return _encode(_red_green_base() + noise.repeat(2, axis=0).repeat(2, axis=1), "PNG")


def _jpeg_with_pixel_noise() -> bytes:
    """12 MP JPEG with independent noise on every pixel, like a photo."""
    noise = np.random.default_rng(1).integers(-20, 21, size=(3000, 4000, 3))
    return _encode(_red_green_base() + noise, "JPEG", quality=90)


def _run_workflow(tmp_path, data: bytes) -> dict:
    store = FilesystemSessionImageStore(tmp_path)
    clock = SystemClock()
    settings = ProcessingSettings()
    timings = {}

    start = time.perf_counter()
    upload = ProcessUpload(store, clock, settings).execute(
        ProcessUploadRequest(session_id=SESSION, data=data)
    )
    timings["upload"] = time.perf_counter() - start

    mark = time.perf_counter()
    enhanced = EnhanceImage(store, clock, settings).execute(
        EnhanceImageRequest(session_id=SESSION, profile=CvdProfile(CvdType.DEUTAN, 1.0))
    )
    timings["enhance"] = time.perf_counter() - mark

    mark = time.perf_counter()
    exported = ExportImage(store, clock).execute(ExportImageRequest(session_id=SESSION))
    timings["export"] = time.perf_counter() - mark

    timings["total"] = time.perf_counter() - start
    assert (upload.width, upload.height) == (4000, 3000)
    assert enhanced.outcome is Outcome.ENHANCED
    assert exported.png[:8] == b"\x89PNG\r\n\x1a\n"
    return timings


@pytest.mark.parametrize(
    ("name", "make"),
    [
        ("PNG, noise in 2x2 cells", _png_with_cell_noise),
        ("JPEG, per-pixel noise", _jpeg_with_pixel_noise),
    ],
)
def test_12_megapixel_image_finishes_within_30_seconds(tmp_path, name, make):
    data = make()
    assert len(data) <= MAX_BYTES
    timings = _run_workflow(tmp_path, data)
    print(
        f"\n12 MP {name} ({len(data) / 1048576:.1f} MB): "
        + ", ".join(f"{step} {seconds:.1f} s" for step, seconds in timings.items())
    )
    assert timings["total"] < LIMIT_SECONDS


def test_20_megapixel_image_is_rejected_within_2_seconds(tmp_path):
    data = _encode(np.full((4000, 5000, 3), 90, dtype=np.int16), "PNG")
    use_case = ProcessUpload(
        FilesystemSessionImageStore(tmp_path), SystemClock(), ProcessingSettings()
    )

    start = time.perf_counter()
    with pytest.raises(UploadRejected) as caught:
        use_case.execute(ProcessUploadRequest(session_id=SESSION, data=data))
    elapsed = time.perf_counter() - start

    print(f"\n20 MP rejection: {elapsed:.3f} s")
    assert caught.value.reason is UploadRejection.TOO_MANY_PIXELS
    assert elapsed < REJECTION_LIMIT_SECONDS
