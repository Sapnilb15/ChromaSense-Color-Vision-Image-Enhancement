import numpy as np
import pytest

from color_engine.pipeline.filter_2_palette.extract_palette_2 import extract_palette_2
from color_engine.rules.color_spaces import rgb_to_lab
from color_engine.rules.distance import ciede2000

KNOWN_COLORS = [
    (200, 40, 40),
    (40, 160, 40),
    (40, 40, 200),
    (240, 220, 60),
    (128, 128, 128),
]


def _flat_graphic() -> np.ndarray:
    """Five vertical bands of known colors, with different widths so counts differ."""
    widths = [50, 40, 30, 20, 60]
    image = np.zeros((40, sum(widths), 3), dtype=np.uint8)
    left = 0
    for color, width in zip(KNOWN_COLORS, widths, strict=True):
        image[:, left : left + width] = color
        left += width
    return image


def _band_slices():
    widths = [50, 40, 30, 20, 60]
    left = 0
    for width in widths:
        yield slice(left, left + width)
        left += width


def test_each_known_color_is_within_two_ciede2000():
    palette = extract_palette_2(_flat_graphic(), 12)
    known_lab = rgb_to_lab(np.array([KNOWN_COLORS], dtype=np.uint8))[0]
    for lab in known_lab:
        assert float(np.min(ciede2000(lab, palette.colors_lab))) < 2.0


def test_labels_assign_each_band_to_its_matching_color():
    image = _flat_graphic()
    palette = extract_palette_2(image, 12)
    assert len(palette.colors_lab) == 5
    for color, columns in zip(KNOWN_COLORS, _band_slices(), strict=True):
        band_labels = np.unique(palette.labels[:, columns])
        assert len(band_labels) == 1
        assert tuple(palette.colors_rgb[band_labels[0]]) == color


def test_palette_is_ordered_by_pixel_count_and_counts_cover_the_image():
    image = _flat_graphic()
    palette = extract_palette_2(image, 12)
    assert palette.counts.sum() == image.shape[0] * image.shape[1]
    assert list(palette.counts) == sorted(palette.counts, reverse=True)
    # The widest band (gray, 60 columns) comes first.
    assert tuple(palette.colors_rgb[0]) == (128, 128, 128)


def test_output_types_and_shapes():
    image = _flat_graphic()
    palette = extract_palette_2(image, 12)
    count = len(palette.counts)
    assert palette.colors_rgb.shape == (count, 3) and palette.colors_rgb.dtype == np.uint8
    assert palette.colors_lab.shape == (count, 3)
    assert palette.labels.shape == image.shape[:2]
    assert palette.labels.min() == 0 and palette.labels.max() == count - 1


def test_two_runs_give_identical_palettes():
    image = np.random.default_rng(3).integers(0, 256, size=(120, 160, 3), dtype=np.uint8)
    first, second = extract_palette_2(image, 12), extract_palette_2(image, 12)
    np.testing.assert_array_equal(first.colors_rgb, second.colors_rgb)
    np.testing.assert_array_equal(first.colors_lab, second.colors_lab)
    np.testing.assert_array_equal(first.labels, second.labels)
    np.testing.assert_array_equal(first.counts, second.counts)


def test_never_more_colors_than_requested():
    image = np.random.default_rng(4).integers(0, 256, size=(100, 100, 3), dtype=np.uint8)
    palette = extract_palette_2(image, 6)
    assert 1 <= len(palette.counts) <= 6


def test_fewer_distinct_colors_than_requested():
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    image[:, 5:] = (255, 255, 255)
    palette = extract_palette_2(image, 12)
    assert len(palette.counts) == 2


def test_single_color_image():
    image = np.full((8, 8, 3), (12, 200, 90), dtype=np.uint8)
    palette = extract_palette_2(image, 12)
    assert len(palette.counts) == 1
    assert tuple(palette.colors_rgb[0]) == (12, 200, 90)
    assert np.all(palette.labels == 0)


def test_colors_closer_than_merge_distance_become_one():
    image = np.zeros((10, 20, 3), dtype=np.uint8)
    image[:, :10] = (120, 120, 120)
    image[:, 10:] = (121, 121, 121)  # about 0.4 CIEDE2000 away
    palette = extract_palette_2(image, 12)
    assert len(palette.counts) == 1


def test_noisy_regions_map_only_to_colors_near_their_own():
    # With more clusters than colors, k-means may split a noisy band into a few nearby
    # clusters. Each of them must still be close to the band's true color.
    rng = np.random.default_rng(5)
    image = _flat_graphic().astype(np.int16) + rng.integers(-4, 5, size=(40, 200, 3))
    image = np.clip(image, 0, 255).astype(np.uint8)
    palette = extract_palette_2(image, 12)
    known_lab = rgb_to_lab(np.array([KNOWN_COLORS], dtype=np.uint8))[0]
    for lab, columns in zip(known_lab, _band_slices(), strict=True):
        for index in np.unique(palette.labels[:, columns]):
            assert float(ciede2000(lab, palette.colors_lab[index])) < 5.0


@pytest.mark.parametrize(
    "pixels",
    [np.zeros((4, 4), dtype=np.uint8), np.zeros((4, 4, 3), dtype=np.float64)],
)
def test_rejects_wrong_input(pixels):
    with pytest.raises(ValueError):
        extract_palette_2(pixels, 12)


def test_rejects_color_count_below_one():
    with pytest.raises(ValueError):
        extract_palette_2(_flat_graphic(), 0)
