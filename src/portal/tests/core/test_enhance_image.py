from datetime import UTC, datetime

import numpy as np
import pytest

from chromasense.core.errors import NoImageInSession
from chromasense.core.models import Outcome, ProcessingSettings, SessionImage
from chromasense.core.use_cases import enhance_image as enhance_module
from chromasense.core.use_cases.enhance_image import EnhanceImage, EnhanceImageRequest
from color_engine.models import CvdProfile, CvdType, SeparationReport5

SESSION = "session-abcdefghijklmnop"
DEUTAN = CvdProfile(CvdType.DEUTAN, 1.0)
PROTAN = CvdProfile(CvdType.PROTAN, 1.0)


def _store_image(store, first, second, image_id="image-1"):
    pixels = np.full((60, 120, 3), 128, dtype=np.uint8)
    pixels[10:50, 10:55] = first
    pixels[10:50, 65:110] = second
    store.save_original(
        SESSION,
        SessionImage(
            image_id=image_id,
            pixels=pixels,
            width=120,
            height=60,
            source_format="PNG",
            uploaded_at=datetime(2026, 11, 19, tzinfo=UTC),
        ),
    )
    return pixels


def _enhance(store, clock, profile=DEUTAN):
    use_case = EnhanceImage(store, clock, ProcessingSettings())
    return use_case.execute(EnhanceImageRequest(session_id=SESSION, profile=profile))


def test_red_green_image_is_enhanced(store, clock):
    pixels = _store_image(store, (200, 40, 40), (40, 160, 40))

    response = _enhance(store, clock)

    assert response.outcome is Outcome.ENHANCED
    assert (response.eligible_count, response.improved_count) == (1, 1)
    assert response.message == "Adjusted 1 of 1 color pairs likely to be confused."
    (pair,) = response.pairs
    assert pair.improved and pair.after > pair.before
    assert pair.color_a_hex.startswith("#") and len(pair.color_a_hex) == 7

    result = store.load_result(SESSION)
    assert result.image_id == "image-1"
    assert result.profile == DEUTAN
    assert result.enhanced_pixels is not None
    assert np.array_equal(result.enhanced_pixels[~result.mask], pixels[~result.mask])
    assert not np.array_equal(result.enhanced_pixels, pixels)
    assert store.touched[SESSION] == clock.now()


def test_red_and_blue_image_has_no_confusable_pairs(store, clock):
    _store_image(store, (200, 40, 40), (40, 40, 200))

    response = _enhance(store, clock)

    assert response.outcome is Outcome.NO_CONFUSABLE_PAIRS
    assert response.message == (
        "No colors likely to be confused were found for the deutan profile at severity 1. "
        "The original image is unchanged."
    )
    assert response.pairs == ()
    assert store.load_result(SESSION).enhanced_pixels is None


def test_no_improvement_gives_not_improved(store, clock, monkeypatch):
    _store_image(store, (200, 40, 40), (40, 160, 40))

    def no_improvement(confusion, enhanced, profile, threshold):
        return SeparationReport5(pairs=(), newly_confusable=(), eligible_count=1, improved_count=0)

    monkeypatch.setattr(enhance_module, "check_separation_5", no_improvement)
    response = _enhance(store, clock)

    assert response.outcome is Outcome.NOT_IMPROVED
    assert response.message == (
        "Colors likely to be confused were found, but the adjustment could not increase their "
        "separation. The original image is still available."
    )
    assert store.load_result(SESSION).enhanced_pixels is None


def test_profile_change_reuses_the_palette(store, clock, monkeypatch):
    _store_image(store, (220, 40, 40), (40, 100, 40))
    calls = []
    real = enhance_module.extract_palette_2

    def spy(pixels, color_count):
        calls.append(color_count)
        return real(pixels, color_count)

    monkeypatch.setattr(enhance_module, "extract_palette_2", spy)

    deutan = _enhance(store, clock, DEUTAN)
    protan = _enhance(store, clock, PROTAN)

    assert calls == [12]
    assert deutan.outcome is Outcome.NO_CONFUSABLE_PAIRS
    assert protan.outcome is Outcome.ENHANCED
    assert store.load_result(SESSION).profile == PROTAN


def test_new_image_gets_a_new_palette(store, clock, monkeypatch):
    calls = []
    real = enhance_module.extract_palette_2
    monkeypatch.setattr(
        enhance_module,
        "extract_palette_2",
        lambda pixels, color_count: calls.append(1) or real(pixels, color_count),
    )
    _store_image(store, (200, 40, 40), (40, 160, 40), image_id="image-1")
    _enhance(store, clock)
    # A result from a different image must not supply the palette.
    result = store.load_result(SESSION)
    _store_image(store, (200, 40, 40), (40, 40, 200), image_id="image-2")
    store.save_result(SESSION, result)
    response = _enhance(store, clock)

    assert len(calls) == 2
    assert response.outcome is Outcome.NO_CONFUSABLE_PAIRS


def test_severity_changes_the_result(store, clock):
    _store_image(store, (200, 40, 40), (40, 160, 40))
    assert _enhance(store, clock, CvdProfile(CvdType.DEUTAN, 1.0)).outcome is Outcome.ENHANCED
    assert (
        _enhance(store, clock, CvdProfile(CvdType.DEUTAN, 0.0)).outcome
        is Outcome.NO_CONFUSABLE_PAIRS
    )


def test_no_image_raises(store, clock):
    with pytest.raises(NoImageInSession) as caught:
        _enhance(store, clock)
    assert caught.value.message == "Upload an image first."
    assert store.calls == []
