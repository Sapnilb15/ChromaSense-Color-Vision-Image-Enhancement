"""Filter 2: find the dominant colors of an image with k-means in CIELAB."""

import numpy as np
from numpy.typing import NDArray
from sklearn.cluster import KMeans

from color_engine.models import Palette2
from color_engine.rules.color_spaces import lab_to_rgb, rgb_to_lab
from color_engine.rules.distance import ciede2000

_MAX_SAMPLE = 50_000
_MERGE_DISTANCE = 2.3
_RANDOM_STATE = 0
_ASSIGN_CHUNK = 262_144


def extract_palette_2(pixels: NDArray, color_count: int) -> Palette2:
    """Find an image's dominant colors with k-means in CIELAB.

    k-means runs with a fixed seed on at most 50,000 distinct colors, weighted by pixel
    count, so the same image always gives the same palette. Centers closer than CIEDE2000
    2.3 are merged, and every pixel is assigned to its nearest remaining color.

    Args:
        pixels: sRGB uint8 array of shape (height, width, 3).
        color_count: The most colors to return. Fewer come back when the image has fewer
            distinct colors or centers merge.

    Returns:
        The palette, ordered by pixel count from most to least.

    Raises:
        ValueError: If ``pixels`` is not a uint8 array of shape (height, width, 3), or
            ``color_count`` is less than 1.
    """
    image = np.asarray(pixels)
    if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("pixels must be a uint8 array of shape (H, W, 3)")
    if color_count < 1:
        raise ValueError("color_count must be at least 1")

    # Work on the distinct colors once; a photo has far fewer of them than pixels.
    codes = _pack(image.reshape(-1, 3))
    unique_codes, inverse, unique_counts = np.unique(codes, return_inverse=True, return_counts=True)
    unique_lab = rgb_to_lab(_unpack(unique_codes)[np.newaxis])[0]

    centers = _cluster(unique_lab, unique_counts, color_count)
    centers = _merge_close_centers(centers, unique_counts, unique_lab)

    assignment = _nearest_center(unique_lab, centers)
    counts = np.bincount(assignment, weights=unique_counts, minlength=len(centers))
    used = np.flatnonzero(counts > 0)
    centers = np.array(
        [
            np.average(
                unique_lab[assignment == index], axis=0, weights=unique_counts[assignment == index]
            )
            for index in used
        ]
    )
    counts = counts[used].astype(np.int64)

    # Order by pixel count, then by color, so ties come out the same on every run.
    order = sorted(range(len(used)), key=lambda i: (-counts[i], *np.round(centers[i], 6).tolist()))
    position = np.empty(len(used), dtype=np.int32)
    position[order] = np.arange(len(used), dtype=np.int32)
    # Map each merged center's index to its final palette position.
    remap = np.full(int(assignment.max()) + 1, -1, dtype=np.int32)
    remap[used] = position

    labels = remap[assignment][inverse].reshape(image.shape[:2])
    ordered_lab = centers[order]
    return Palette2(
        colors_rgb=lab_to_rgb(ordered_lab[np.newaxis])[0],
        colors_lab=ordered_lab,
        labels=labels,
        counts=counts[order],
    )


def _pack(rgb: NDArray[np.uint8]) -> NDArray[np.int32]:
    channels = rgb.astype(np.int32)
    return (channels[:, 0] << 16) | (channels[:, 1] << 8) | channels[:, 2]


def _unpack(codes: NDArray[np.int32]) -> NDArray[np.uint8]:
    return np.stack([(codes >> 16) & 255, (codes >> 8) & 255, codes & 255], axis=-1).astype(
        np.uint8
    )


def _cluster(unique_lab: NDArray, unique_counts: NDArray, color_count: int) -> NDArray:
    """Run k-means on at most _MAX_SAMPLE distinct colors, weighted by their pixel counts."""
    if len(unique_lab) > _MAX_SAMPLE:
        rng = np.random.default_rng(_RANDOM_STATE)
        chosen = rng.choice(
            len(unique_lab),
            _MAX_SAMPLE,
            replace=False,
            p=unique_counts / unique_counts.sum(),
        )
        unique_lab, unique_counts = unique_lab[chosen], unique_counts[chosen]
    clusters = min(color_count, len(unique_lab))
    model = KMeans(n_clusters=clusters, n_init=4, random_state=_RANDOM_STATE)
    model.fit(unique_lab, sample_weight=unique_counts)
    return model.cluster_centers_


def _merge_close_centers(centers: NDArray, unique_counts: NDArray, unique_lab: NDArray) -> NDArray:
    """Merge centers closer than CIEDE2000 2.3, weighting each by the pixels nearest to it."""
    weights = np.bincount(
        _nearest_center(unique_lab, centers), weights=unique_counts, minlength=len(centers)
    )
    centers, weights = centers.copy(), weights.astype(np.float64)
    while len(centers) > 1:
        first, second = np.triu_indices(len(centers), k=1)
        distances = ciede2000(centers[first], centers[second])
        closest = int(np.argmin(distances))
        if distances[closest] >= _MERGE_DISTANCE:
            break
        keep, drop = int(first[closest]), int(second[closest])
        total = weights[keep] + weights[drop]
        if total > 0:
            centers[keep] = (centers[keep] * weights[keep] + centers[drop] * weights[drop]) / total
        weights[keep] = total
        centers = np.delete(centers, drop, axis=0)
        weights = np.delete(weights, drop)
    return centers


def _nearest_center(lab: NDArray, centers: NDArray) -> NDArray[np.int64]:
    """Index of the nearest center in CIELAB for each color, computed in chunks."""
    result = np.empty(len(lab), dtype=np.int64)
    for start in range(0, len(lab), _ASSIGN_CHUNK):
        block = lab[start : start + _ASSIGN_CHUNK]
        distances = ((block[:, np.newaxis, :] - centers[np.newaxis, :, :]) ** 2).sum(axis=2)
        result[start : start + _ASSIGN_CHUNK] = np.argmin(distances, axis=1)
    return result
