import io
from datetime import UTC, datetime

import numpy as np
import pytest
from PIL import Image

from chromasense.core.errors import NoImageInSession
from chromasense.core.models import ProcessingSettings, SessionImage, View
from chromasense.core.use_cases.enhance_image import EnhanceImage, EnhanceImageRequest
from chromasense.core.use_cases.export_image import ExportImage, ExportImageRequest
from chromasense.core.use_cases.render_view import RenderView, RenderViewRequest
from color_engine.models import CvdProfile, CvdType

SESSION = "session-abcdefghijklmnop"


def _decode(png: bytes) -> np.ndarray:
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    with Image.open(io.BytesIO(png)) as image:
        assert image.format == "PNG"
        return np.asarray(image.convert("RGB"))


def _store_image(store, second=(40, 160, 40)):
    pixels = np.full((60, 120, 3), 128, dtype=np.uint8)
    pixels[10:50, 10:55] = (200, 40, 40)
    pixels[10:50, 65:110] = second
    store.save_original(
        SESSION,
        SessionImage(
            image_id="image-1",
            pixels=pixels,
            width=120,
            height=60,
            source_format="JPEG",
            uploaded_at=datetime(2026, 11, 19, tzinfo=UTC),
        ),
    )
    return pixels


def _enhance(store, clock):
    EnhanceImage(store, clock, ProcessingSettings()).execute(
        EnhanceImageRequest(session_id=SESSION, profile=CvdProfile(CvdType.DEUTAN, 1.0))
    )


def _render(store, clock, view):
    return RenderView(store, clock).execute(RenderViewRequest(session_id=SESSION, view=view))


def _export(store, clock):
    return ExportImage(store, clock).execute(ExportImageRequest(session_id=SESSION))


def test_original_view_is_a_png_of_the_stored_pixels(store, clock):
    pixels = _store_image(store)
    response = _render(store, clock, View.ORIGINAL)
    np.testing.assert_array_equal(_decode(response.png), pixels)
    assert response.image_id == "image-1"
    assert store.touched[SESSION] == clock.now()


def test_enhanced_view_and_export_match_the_stored_enhanced_pixels(store, clock):
    pixels = _store_image(store)
    _enhance(store, clock)
    result = store.load_result(SESSION)

    shown = _decode(_render(store, clock, View.ENHANCED).png)
    exported = _export(store, clock)
    downloaded = _decode(exported.png)

    np.testing.assert_array_equal(shown, result.enhanced_pixels)
    np.testing.assert_array_equal(downloaded, result.enhanced_pixels)
    assert exported.filename == "chromasense-enhanced.png"
    # Export is at the original resolution, and nothing outside the mask changed.
    assert downloaded.shape == pixels.shape
    assert np.array_equal(downloaded[~result.mask], pixels[~result.mask])
    assert not np.array_equal(downloaded, pixels)


def test_no_confusable_pairs_has_no_enhanced_view_or_download(store, clock):
    _store_image(store, second=(40, 40, 200))
    _enhance(store, clock)

    with pytest.raises(NoImageInSession) as view_error:
        _render(store, clock, View.ENHANCED)
    with pytest.raises(NoImageInSession) as export_error:
        _export(store, clock)

    assert view_error.value.message == "There is no enhanced image yet."
    assert export_error.value.message == "There is no enhanced image to download."


def test_enhanced_view_before_enhancing_raises(store, clock):
    _store_image(store)
    with pytest.raises(NoImageInSession) as caught:
        _render(store, clock, View.ENHANCED)
    assert caught.value.message == "There is no enhanced image yet."


@pytest.mark.parametrize("view", list(View))
def test_no_image_raises_for_every_view(store, clock, view):
    with pytest.raises(NoImageInSession) as caught:
        _render(store, clock, view)
    assert caught.value.message == "Upload an image first."
    assert store.touched == {}


def test_export_with_no_image_raises(store, clock):
    with pytest.raises(NoImageInSession) as caught:
        _export(store, clock)
    assert caught.value.message == "There is no enhanced image to download."


def test_new_upload_removes_the_old_enhanced_view(store, clock):
    _store_image(store)
    _enhance(store, clock)
    _store_image(store)  # save_original discards the stored result
    with pytest.raises(NoImageInSession):
        _render(store, clock, View.ENHANCED)
