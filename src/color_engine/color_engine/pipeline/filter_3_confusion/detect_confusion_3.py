"""Filter 3: find palette pairs that become confusable under the selected profile."""

import numpy as np
from numpy.typing import NDArray

from color_engine.models import ConfusablePair, ConfusionResult3, CvdProfile, Palette2
from color_engine.rules.color_spaces import rgb_to_lab
from color_engine.rules.distance import ciede2000
from color_engine.rules.simulation import simulate


def detect_confusion_3(
    pixels: NDArray, palette: Palette2, profile: CvdProfile, threshold: float
) -> ConfusionResult3:
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    if np.asarray(pixels).shape[:2] != palette.labels.shape:
        raise ValueError("pixels and palette labels must have the same height and width")

    count = len(palette.colors_lab)
    simulated_lab = rgb_to_lab(simulate(palette.colors_rgb, profile)[np.newaxis])[0]
    first, second = np.triu_indices(count, k=1)
    original = ciede2000(palette.colors_lab[first], palette.colors_lab[second])
    simulated = ciede2000(simulated_lab[first], simulated_lab[second])

    flagged = (original >= threshold) & (simulated < threshold)
    pairs = tuple(
        ConfusablePair(
            a=int(first[i]),
            b=int(second[i]),
            original_distance=float(original[i]),
            simulated_distance=float(simulated[i]),
        )
        for i in np.flatnonzero(flagged)
    )
    groups = _connected_groups(pairs)
    members = np.array(sorted({index for group in groups for index in group}), dtype=np.int32)
    mask = np.isin(palette.labels, members)
    return ConfusionResult3(
        palette=palette,
        profile=profile,
        threshold=threshold,
        pairs=pairs,
        groups=groups,
        mask=mask,
    )


def _connected_groups(pairs: tuple[ConfusablePair, ...]) -> tuple[tuple[int, ...], ...]:
    """Join palette indexes linked by flagged pairs into sorted groups."""
    parent: dict[int, int] = {}

    def root(index: int) -> int:
        parent.setdefault(index, index)
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for pair in pairs:
        parent[root(pair.a)] = root(pair.b)
    groups: dict[int, list[int]] = {}
    for index in parent:
        groups.setdefault(root(index), []).append(index)
    return tuple(sorted(tuple(sorted(members)) for members in groups.values()))
