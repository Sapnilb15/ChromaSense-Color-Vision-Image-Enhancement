"""Filter 5: check whether enhancement increased the simulated separation of flagged pairs."""

import numpy as np
from numpy.typing import NDArray

from color_engine.models import (
    ConfusionResult3,
    CvdProfile,
    EnhancedImage4,
    PairSeparation,
    SeparationReport5,
)
from color_engine.rules.color_spaces import lab_to_rgb, rgb_to_lab
from color_engine.rules.distance import ciede2000
from color_engine.rules.simulation import simulate


def check_separation_5(
    confusion: ConfusionResult3,
    enhanced: EnhancedImage4,
    profile: CvdProfile,
    threshold: float,
) -> SeparationReport5:
    palette = confusion.palette
    if enhanced.palette_lab_after.shape != palette.colors_lab.shape:
        raise ValueError("enhanced palette does not match the confusion result's palette")

    before_lab = _simulated_lab(palette.colors_rgb, profile)
    after_lab = _simulated_lab(lab_to_rgb(enhanced.palette_lab_after[np.newaxis])[0], profile)

    pairs = []
    for pair in confusion.pairs:
        distance_after = float(ciede2000(after_lab[pair.a], after_lab[pair.b]))
        pairs.append(
            PairSeparation(
                a=pair.a,
                b=pair.b,
                before=pair.simulated_distance,
                after=distance_after,
                improved=distance_after > pair.simulated_distance,
            )
        )

    flagged = {(pair.a, pair.b) for pair in confusion.pairs}
    first, second = np.triu_indices(len(palette.colors_lab), k=1)
    before = ciede2000(before_lab[first], before_lab[second])
    after = ciede2000(after_lab[first], after_lab[second])
    newly_confusable = tuple(
        (int(a), int(b))
        for a, b, was, now in zip(first, second, before, after, strict=True)
        if (int(a), int(b)) not in flagged and was >= threshold and now < threshold
    )
    return SeparationReport5(
        pairs=tuple(pairs),
        newly_confusable=newly_confusable,
        eligible_count=len(pairs),
        improved_count=sum(pair.improved for pair in pairs),
    )


def _simulated_lab(colors_rgb: NDArray[np.uint8], profile: CvdProfile) -> NDArray[np.float64]:
    return rgb_to_lab(simulate(colors_rgb, profile)[np.newaxis])[0]
