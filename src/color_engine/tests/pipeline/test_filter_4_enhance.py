import numpy as np
import pytest

from color_engine.models import ConfusablePair, ConfusionResult3, CvdProfile, CvdType, Palette2
from color_engine.pipeline.filter_2_palette.extract_palette_2 import extract_palette_2
from color_engine.pipeline.filter_3_confusion.detect_confusion_3 import detect_confusion_3
from color_engine.pipeline.filter_4_enhance.enhance_4 import _tiers, enhance_4
from color_engine.rules.color_spaces import rgb_to_lab

GRAY = (128, 128, 128)
DEUTAN = CvdProfile(CvdType.DEUTAN, 1.0)
PROTAN = CvdProfile(CvdType.PROTAN, 1.0)


def _graphic(first, second, noise=0, seed=0):
    image = np.full((60, 120, 3), GRAY, dtype=np.int16)
    image[10:50, 10:55] = first
    image[10:50, 65:110] = second
    if noise:
        image += np.random.default_rng(seed).integers(-noise, noise + 1, size=image.shape)
    return np.clip(image, 0, 255).astype(np.uint8)


FIRST_BLOCK = np.s_[10:50, 10:55]
SECOND_BLOCK = np.s_[10:50, 65:110]


def _run(image, profile):
    confusion = detect_confusion_3(image, extract_palette_2(image, 12), profile, 10.0)
    return confusion, enhance_4(image, confusion)


def _mean_lightness(pixels, block) -> float:
    return float(rgb_to_lab(pixels[block])[..., 0].mean())


@pytest.mark.parametrize(
    ("first", "second", "profile"),
    [((200, 40, 40), (40, 160, 40), DEUTAN), ((220, 40, 40), (40, 100, 40), PROTAN)],
)
def test_flat_graphic_changes_only_masked_pixels_and_separates_lightness(first, second, profile):
    image = _graphic(first, second)
    confusion, enhanced = _run(image, profile)
    assert confusion.mask.any()

    mask = confusion.mask
    assert np.array_equal(enhanced.pixels[~mask], image[~mask])
    gap = abs(
        _mean_lightness(enhanced.pixels, FIRST_BLOCK)
        - _mean_lightness(enhanced.pixels, SECOND_BLOCK)
    )
    assert gap >= 20.0


def test_no_flagged_pairs_returns_input_unchanged():
    image = _graphic((200, 40, 40), (40, 40, 200))
    confusion, enhanced = _run(image, DEUTAN)
    assert confusion.pairs == ()
    np.testing.assert_array_equal(enhanced.pixels, image)
    assert not enhanced.changed.any()
    np.testing.assert_array_equal(enhanced.palette_lab_after, confusion.palette.colors_lab)
    assert enhanced.pixels is not image


def test_photo_like_noise_keeps_outside_mask_identical():
    image = _graphic((200, 40, 40), (40, 160, 40), noise=8, seed=7)
    confusion, enhanced = _run(image, DEUTAN)
    assert confusion.mask.any()
    assert np.array_equal(enhanced.pixels[~confusion.mask], image[~confusion.mask])


def test_photo_like_noise_does_not_band_a_region():
    # k-means splits each noisy color into several clusters; they must move together.
    image = _graphic((200, 40, 40), (40, 160, 40), noise=8, seed=7)
    _, enhanced = _run(image, DEUTAN)
    for block in (FIRST_BLOCK, SECOND_BLOCK):
        before = rgb_to_lab(image[block])[..., 0].std()
        after = rgb_to_lab(enhanced.pixels[block])[..., 0].std()
        assert after <= before + 1.0


def test_palette_lab_after_matches_enhanced_pixels():
    image = _graphic((200, 40, 40), (40, 160, 40))
    confusion, enhanced = _run(image, DEUTAN)
    labels = confusion.palette.labels
    for index in range(len(enhanced.changed)):
        if enhanced.changed[index]:
            expected = rgb_to_lab(enhanced.pixels[labels == index][np.newaxis])[0].mean(axis=0)
            np.testing.assert_allclose(enhanced.palette_lab_after[index], expected, atol=1e-6)
        else:
            np.testing.assert_array_equal(
                enhanced.palette_lab_after[index], confusion.palette.colors_lab[index]
            )


def _hand_made(colors, labels, pairs, groups, mask_indexes, threshold=10.0):
    colors = np.array(colors, dtype=np.uint8)
    labels = np.array(labels, dtype=np.int32)
    palette = Palette2(
        colors_rgb=colors,
        colors_lab=rgb_to_lab(colors[np.newaxis])[0],
        labels=labels,
        counts=np.bincount(labels.ravel(), minlength=len(colors)).astype(np.int64),
    )
    return ConfusionResult3(
        palette=palette,
        profile=DEUTAN,
        threshold=threshold,
        pairs=pairs,
        groups=groups,
        mask=np.isin(labels, mask_indexes),
    )


def test_isolation_hand_made_confusion_without_filters_2_and_3():
    image = _graphic((200, 40, 40), (40, 160, 40))
    labels = np.zeros(image.shape[:2], dtype=np.int32)
    labels[FIRST_BLOCK], labels[SECOND_BLOCK] = 1, 2
    pair = ConfusablePair(a=1, b=2, original_distance=71.4, simulated_distance=7.0)
    confusion = _hand_made([GRAY, (200, 40, 40), (40, 160, 40)], labels, (pair,), ((1, 2),), [1, 2])

    enhanced = enhance_4(image, confusion)

    gray = labels == 0
    assert np.array_equal(enhanced.pixels[gray], image[gray])
    assert enhanced.changed.tolist()[0] is False
    gap = abs(
        _mean_lightness(enhanced.pixels, FIRST_BLOCK)
        - _mean_lightness(enhanced.pixels, SECOND_BLOCK)
    )
    assert gap >= 20.0


def test_hue_and_chroma_are_kept_where_the_gamut_allows():
    image = _graphic((200, 40, 40), (40, 160, 40))
    confusion, enhanced = _run(image, DEUTAN)
    before = rgb_to_lab(image[confusion.mask][np.newaxis])[0]
    after = rgb_to_lab(enhanced.pixels[confusion.mask][np.newaxis])[0]
    hue_before = np.degrees(np.arctan2(before[:, 2], before[:, 1]))
    hue_after = np.degrees(np.arctan2(after[:, 2], after[:, 1]))
    difference = np.abs((hue_after - hue_before + 180) % 360 - 180)
    assert float(np.median(difference)) < 15.0


def test_flagged_pair_is_never_kept_in_one_tier():
    # 0 and 1 are near (5 apart), 1 and 2 are near, but 0 and 2 are flagged together.
    colors = [(118, 118, 118), (130, 130, 130), (142, 142, 142)]
    lab = rgb_to_lab(np.array([colors], dtype=np.uint8))[0]
    threshold = float((lab[2, 0] - lab[0, 0]) - 0.5)
    pair = ConfusablePair(a=0, b=2, original_distance=threshold + 0.5, simulated_distance=1.0)
    confusion = _hand_made(colors, [[0, 1, 2]], (pair,), ((0, 2),), [0, 2], threshold=threshold)
    assert _tiers([0, 1, 2], confusion) == [[0], [1], [2]]


def test_near_identical_colors_form_one_tier():
    colors = [(200, 40, 40), (203, 42, 41), (40, 160, 40)]
    pairs = (
        ConfusablePair(a=0, b=2, original_distance=71.0, simulated_distance=7.0),
        ConfusablePair(a=1, b=2, original_distance=71.0, simulated_distance=7.0),
    )
    confusion = _hand_made(colors, [[0, 1, 2]], pairs, ((0, 1, 2),), [0, 1, 2])
    assert _tiers([0, 1, 2], confusion) == [[0, 1], [2]]


def test_rejects_pixels_that_do_not_match_the_palette():
    image = _graphic((200, 40, 40), (40, 160, 40))
    confusion, _ = _run(image, DEUTAN)
    with pytest.raises(ValueError):
        enhance_4(image[:10], confusion)
    with pytest.raises(ValueError):
        enhance_4(image.astype(np.float64), confusion)
