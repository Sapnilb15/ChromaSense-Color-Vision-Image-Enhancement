import numpy as np
import pytest

from color_engine.models import ConfusablePair, CvdProfile, CvdType, Palette2
from color_engine.pipeline.filter_2_palette.extract_palette_2 import extract_palette_2
from color_engine.pipeline.filter_3_confusion.detect_confusion_3 import (
    _connected_groups,
    detect_confusion_3,
)
from color_engine.rules.color_spaces import rgb_to_lab

GRAY = (128, 128, 128)
# Measured with the release 0.5 Machado matrices at severity 1.0 (increment 07 table).
DEUTAN_RED, DEUTAN_GREEN = (200, 40, 40), (40, 160, 40)  # 71.4 -> 7.1
PROTAN_RED, PROTAN_GREEN = (220, 40, 40), (40, 100, 40)  # 61.7 -> 1.1
BLUE = (40, 40, 200)  # red-blue under deutan: 44.0 -> 63.8

DEUTAN = CvdProfile(CvdType.DEUTAN, 1.0)
PROTAN = CvdProfile(CvdType.PROTAN, 1.0)


def _graphic(first, second):
    """Gray background with a block of each color; returns the image and each block's mask."""
    image = np.full((40, 90, 3), GRAY, dtype=np.uint8)
    image[5:35, 5:40] = first
    image[5:35, 50:85] = second
    first_mask = np.zeros(image.shape[:2], dtype=bool)
    second_mask = np.zeros(image.shape[:2], dtype=bool)
    first_mask[5:35, 5:40] = True
    second_mask[5:35, 50:85] = True
    return image, first_mask, second_mask


def _detect(image, profile, threshold=10.0):
    return detect_confusion_3(image, extract_palette_2(image, 12), profile, threshold)


def _color_index(palette: Palette2, rgb) -> int:
    matches = np.flatnonzero(np.all(palette.colors_rgb == np.array(rgb, dtype=np.uint8), axis=1))
    assert len(matches) == 1, f"{rgb} not in palette {palette.colors_rgb.tolist()}"
    return int(matches[0])


@pytest.mark.parametrize(
    ("first", "second", "profile"),
    [(DEUTAN_RED, DEUTAN_GREEN, DEUTAN), (PROTAN_RED, PROTAN_GREEN, PROTAN)],
)
def test_red_green_pair_is_flagged_and_mask_is_exact(first, second, profile):
    image, first_mask, second_mask = _graphic(first, second)
    result = _detect(image, profile)

    a, b = _color_index(result.palette, first), _color_index(result.palette, second)
    assert [(pair.a, pair.b) for pair in result.pairs] == [tuple(sorted((a, b)))]
    np.testing.assert_array_equal(result.mask, first_mask | second_mask)
    assert result.groups == (tuple(sorted((a, b))),)


def test_flagged_pair_reports_both_distances():
    image, _, _ = _graphic(DEUTAN_RED, DEUTAN_GREEN)
    (pair,) = _detect(image, DEUTAN).pairs
    assert pair.original_distance == pytest.approx(71.4, abs=1.0)
    assert pair.simulated_distance == pytest.approx(7.1, abs=1.0)


def test_red_and_blue_are_not_flagged():
    image, _, _ = _graphic(DEUTAN_RED, BLUE)
    result = _detect(image, DEUTAN)
    assert result.pairs == ()
    assert result.groups == ()
    assert not result.mask.any()


def test_threshold_changes_the_result():
    image, _, _ = _graphic(DEUTAN_RED, DEUTAN_GREEN)
    # The simulated distance is about 7.1: above 5, below 10.
    assert _detect(image, DEUTAN, threshold=5.0).pairs == ()
    assert len(_detect(image, DEUTAN, threshold=10.0).pairs) == 1


@pytest.mark.parametrize(
    "profile", [CvdProfile(CvdType.DEUTAN, 0.0), CvdProfile(CvdType.PROTAN, 0.0)]
)
def test_severity_zero_flags_nothing(profile):
    image, _, _ = _graphic(DEUTAN_RED, DEUTAN_GREEN)
    result = _detect(image, profile)
    assert result.pairs == ()
    assert not result.mask.any()


def test_pair_is_flagged_only_for_its_own_profile():
    # The protan pair stays far apart under deutan (simulated distance about 18.7).
    image, _, _ = _graphic(PROTAN_RED, PROTAN_GREEN)
    assert len(_detect(image, PROTAN).pairs) == 1
    assert _detect(image, DEUTAN).pairs == ()


def test_result_keeps_its_inputs():
    image, _, _ = _graphic(DEUTAN_RED, DEUTAN_GREEN)
    palette = extract_palette_2(image, 12)
    result = detect_confusion_3(image, palette, DEUTAN, 10.0)
    assert result.palette is palette
    assert result.profile == DEUTAN
    assert result.threshold == 10.0
    assert result.mask.shape == image.shape[:2] and result.mask.dtype == bool


def test_pairs_are_ordered_with_a_below_b():
    image, _, _ = _graphic(DEUTAN_RED, DEUTAN_GREEN)
    for pair in _detect(image, DEUTAN).pairs:
        assert pair.a < pair.b


def test_hand_made_palette_uses_its_labels_for_the_mask():
    colors = np.array([GRAY, DEUTAN_RED, DEUTAN_GREEN], dtype=np.uint8)
    labels = np.array([[0, 1, 2], [2, 1, 0]], dtype=np.int32)
    palette = Palette2(
        colors_rgb=colors,
        colors_lab=rgb_to_lab(colors[np.newaxis])[0],
        labels=labels,
        counts=np.array([2, 2, 2], dtype=np.int64),
    )
    result = detect_confusion_3(np.zeros((2, 3, 3), dtype=np.uint8), palette, DEUTAN, 10.0)
    np.testing.assert_array_equal(result.mask, labels > 0)


def test_linked_pairs_form_one_group_and_others_stay_separate():
    pairs = (
        ConfusablePair(a=1, b=2, original_distance=30.0, simulated_distance=3.0),
        ConfusablePair(a=2, b=5, original_distance=30.0, simulated_distance=3.0),
        ConfusablePair(a=3, b=4, original_distance=30.0, simulated_distance=3.0),
    )
    assert _connected_groups(pairs) == ((1, 2, 5), (3, 4))
    assert _connected_groups(()) == ()


def test_rejects_non_positive_threshold():
    image, _, _ = _graphic(DEUTAN_RED, DEUTAN_GREEN)
    with pytest.raises(ValueError):
        _detect(image, DEUTAN, threshold=0.0)


def test_rejects_pixels_that_do_not_match_the_palette():
    image, _, _ = _graphic(DEUTAN_RED, DEUTAN_GREEN)
    palette = extract_palette_2(image, 12)
    with pytest.raises(ValueError):
        detect_confusion_3(image[:10], palette, DEUTAN, 10.0)
