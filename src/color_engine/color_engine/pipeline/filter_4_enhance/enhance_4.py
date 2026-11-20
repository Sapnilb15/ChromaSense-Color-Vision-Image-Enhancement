"""Filter 4: separate confusable colors by lightness, changing only pixels in the mask.

docs/enhancement-evaluation-v0.5.md records why lightness separation was selected.
"""

import numpy as np
from numpy.typing import NDArray

from color_engine.models import ConfusionResult3, EnhancedImage4
from color_engine.rules.color_spaces import lab_to_rgb, rgb_to_lab
from color_engine.rules.distance import ciede2000

_LIGHTNESS_MIN = 15.0
_LIGHTNESS_MAX = 90.0
_LIGHTNESS_GAP = 22.0


def enhance_4(pixels: NDArray, confusion: ConfusionResult3) -> EnhancedImage4:
    """Separate confusable colors by CIELAB lightness, changing only masked pixels.

    Each group's colors are spaced 22 lightness units apart between 15 and 90, avoiding
    the lightness of the image's other colors where possible. Near-identical colors move
    together, so a noisy region is not split into bands. Pixels outside
    ``confusion.mask`` are copied unchanged.

    Args:
        pixels: sRGB uint8 array of shape (height, width, 3), the same image given to
            filters 2 and 3.
        confusion: Output of filter 3.

    Returns:
        The enhanced pixels and each palette color's CIELAB after enhancement. With no
        flagged groups, the pixels are an unchanged copy.

    Raises:
        ValueError: If ``pixels`` is not uint8 or does not match the palette labels' height
            and width.
    """
    image = np.asarray(pixels)
    if image.dtype != np.uint8 or image.shape[:2] != confusion.palette.labels.shape:
        raise ValueError("pixels must be uint8 and match the palette labels")

    palette = confusion.palette
    count = len(palette.colors_lab)
    result = image.copy()
    palette_lab_after = palette.colors_lab.copy()
    if not confusion.groups:
        return EnhancedImage4(result, palette_lab_after, np.zeros(count, dtype=bool))

    labels = palette.labels
    shifts = _lightness_shifts(image, labels, confusion)
    changed = np.abs(shifts) > 1e-9

    # Only masked pixels of colors that moved go through CIELAB; every other pixel is copied.
    moving = confusion.mask & changed[labels]
    if moving.any():
        # A pixel's new value depends only on its RGB and its palette index, so convert each
        # distinct (color, index) once. Photos have far fewer of these than pixels.
        rgb = image[moving].astype(np.int64)
        moved_labels = labels[moving].astype(np.int64)
        keys = (((rgb[:, 0] << 16) | (rgb[:, 1] << 8) | rgb[:, 2]) << 8) | moved_labels
        unique_keys, inverse, key_counts = np.unique(keys, return_inverse=True, return_counts=True)
        codes, key_labels = unique_keys >> 8, unique_keys & 255
        unique_rgb = np.stack([(codes >> 16) & 255, (codes >> 8) & 255, codes & 255], axis=-1)

        lab = rgb_to_lab(unique_rgb.astype(np.uint8)[np.newaxis])[0]
        lab[:, 0] += shifts[key_labels]
        new_rgb = lab_to_rgb(lab[np.newaxis])[0]
        result[moving] = new_rgb[inverse]

        new_lab = rgb_to_lab(new_rgb[np.newaxis])[0]
        for index in np.flatnonzero(changed):
            selected = key_labels == index
            if selected.any():
                palette_lab_after[index] = np.average(
                    new_lab[selected], axis=0, weights=key_counts[selected]
                )
    return EnhancedImage4(result, palette_lab_after, changed)


def _lightness_shifts(
    pixels: NDArray, labels: NDArray, confusion: ConfusionResult3
) -> NDArray[np.float64]:
    """Return the lightness change for each palette index.

    Grouped colors closer than the threshold in the original are near-identical (k-means can
    split one noisy color into several clusters). They form one tier and share one shift, so a
    single region is not broken into bands. Tiers, not single colors, are spaced apart.
    """
    palette = confusion.palette
    lightness = _mean_lightness(pixels, labels, len(palette.colors_lab))
    weights = palette.counts.astype(np.float64)
    groups = _merge_groups_sharing_a_tier(confusion)
    grouped = {index for group in groups for index in group}
    taken = [float(lightness[i]) for i in range(len(lightness)) if i not in grouped]

    shifts = np.zeros(len(lightness), dtype=np.float64)
    for group in groups:
        tiers = _tiers(group, confusion)
        tier_lightness = [
            float(np.average(lightness[list(t)], weights=weights[list(t)])) for t in tiers
        ]
        order = sorted(range(len(tiers)), key=lambda i: tier_lightness[i])
        current = [tier_lightness[i] for i in order]
        targets = _choose_targets(current, taken)
        for position, target in zip(order, targets, strict=True):
            for index in tiers[position]:
                shifts[index] = target - tier_lightness[position]
        taken.extend(targets)
    return shifts


def _near_identical(confusion: ConfusionResult3, a: int, b: int) -> bool:
    lab = confusion.palette.colors_lab
    return float(ciede2000(lab[a], lab[b])) < confusion.threshold


def _flagged_together(confusion: ConfusionResult3, members: set[int]) -> bool:
    return any(pair.a in members and pair.b in members for pair in confusion.pairs)


def _components(nodes: list[int], linked) -> list[list[int]]:
    parent = {node: node for node in nodes}

    def root(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for i, a in enumerate(nodes):
        for b in nodes[i + 1 :]:
            if linked(a, b):
                parent[root(a)] = root(b)
    components: dict[int, list[int]] = {}
    for node in nodes:
        components.setdefault(root(node), []).append(node)
    return sorted(sorted(component) for component in components.values())


def _merge_groups_sharing_a_tier(confusion: ConfusionResult3) -> list[list[int]]:
    """Join groups that contain near-identical colors, so those colors move together."""
    members = sorted({index for group in confusion.groups for index in group})
    group_of = {index: g for g, group in enumerate(confusion.groups) for index in group}
    return _components(
        members,
        lambda a, b: group_of[a] == group_of[b] or _near_identical(confusion, a, b),
    )


def _tiers(group: list[int], confusion: ConfusionResult3) -> list[list[int]]:
    """Split a group into tiers of near-identical colors; never keep a flagged pair in one tier."""
    tiers = []
    for tier in _components(group, lambda a, b: _near_identical(confusion, a, b)):
        if _flagged_together(confusion, set(tier)):
            tiers.extend([index] for index in tier)
        else:
            tiers.append(tier)
    return tiers


def _mean_lightness(pixels: NDArray, labels: NDArray, count: int) -> NDArray[np.float64]:
    """Return the CIELAB lightness of each palette color's mean pixel."""
    flat = labels.ravel()
    totals = np.bincount(flat, minlength=count).astype(np.float64)
    means = np.column_stack(
        [
            np.bincount(flat, weights=pixels[..., channel].ravel(), minlength=count)
            / np.maximum(totals, 1)
            for channel in range(3)
        ]
    )
    colors = np.rint(means).astype(np.uint8)[np.newaxis]
    return rgb_to_lab(colors)[0, :, 0]


def _choose_targets(current: list[float], taken: list[float]) -> list[float]:
    """Space a group evenly, avoiding other colors first, then moving as little as possible."""
    count = len(current)
    gap = min(_LIGHTNESS_GAP, (_LIGHTNESS_MAX - _LIGHTNESS_MIN) / max(count - 1, 1))
    best_key = None
    best_targets = current
    for start in np.arange(_LIGHTNESS_MIN, _LIGHTNESS_MAX + 1.0):
        targets = [float(start) + position * gap for position in range(count)]
        if targets[-1] > _LIGHTNESS_MAX:
            break
        conflicts = sum(abs(target - other) < gap for target in targets for other in taken)
        movement = sum(abs(target - now) for target, now in zip(targets, current, strict=True))
        if best_key is None or (conflicts, movement) < best_key:
            best_key = (conflicts, movement)
            best_targets = targets
    return best_targets
