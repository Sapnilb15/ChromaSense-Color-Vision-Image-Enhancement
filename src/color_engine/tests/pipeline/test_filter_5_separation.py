import numpy as np
import pytest

from color_engine.models import (
    ConfusablePair,
    ConfusionResult3,
    CvdProfile,
    CvdType,
    EnhancedImage4,
    Palette2,
)
from color_engine.pipeline.filter_2_palette.extract_palette_2 import extract_palette_2
from color_engine.pipeline.filter_3_confusion.detect_confusion_3 import detect_confusion_3
from color_engine.pipeline.filter_4_enhance.enhance_4 import enhance_4
from color_engine.pipeline.filter_5_separation.check_separation_5 import check_separation_5
from color_engine.rules.color_spaces import rgb_to_lab

GRAY = (128, 128, 128)
DEUTAN = CvdProfile(CvdType.DEUTAN, 1.0)
PROTAN = CvdProfile(CvdType.PROTAN, 1.0)


def _graphic(first, second):
    image = np.full((60, 120, 3), GRAY, dtype=np.uint8)
    image[10:50, 10:55] = first
    image[10:50, 65:110] = second
    return image


def _pipeline(image, profile, threshold=10.0):
    confusion = detect_confusion_3(image, extract_palette_2(image, 12), profile, threshold)
    enhanced = enhance_4(image, confusion)
    return confusion, enhanced, check_separation_5(confusion, enhanced, profile, threshold)


@pytest.mark.parametrize(
    ("first", "second", "profile"),
    [((200, 40, 40), (40, 160, 40), DEUTAN), ((220, 40, 40), (40, 100, 40), PROTAN)],
)
def test_red_green_pair_improves_with_no_newly_confusable_pairs(first, second, profile):
    confusion, _, report = _pipeline(_graphic(first, second), profile)
    assert report.eligible_count == 1
    assert report.improved_count == 1
    assert report.newly_confusable == ()
    (pair,) = report.pairs
    assert pair.improved and pair.after > pair.before
    assert (pair.a, pair.b) == (confusion.pairs[0].a, confusion.pairs[0].b)
    assert pair.before == confusion.pairs[0].simulated_distance


def test_colors_that_did_not_move_are_not_improved():
    confusion, _, _ = _pipeline(_graphic((200, 40, 40), (40, 160, 40)), DEUTAN)
    unmoved = EnhancedImage4(
        pixels=np.zeros((60, 120, 3), dtype=np.uint8),
        palette_lab_after=confusion.palette.colors_lab.copy(),
        changed=np.zeros(len(confusion.palette.colors_lab), dtype=bool),
    )
    report = check_separation_5(confusion, unmoved, DEUTAN, 10.0)
    assert report.eligible_count == 1
    assert report.improved_count == 0
    assert not report.pairs[0].improved
    assert report.pairs[0].after == pytest.approx(report.pairs[0].before, abs=1e-9)


def test_no_flagged_pairs_gives_zero_counts():
    _, _, report = _pipeline(_graphic((200, 40, 40), (40, 40, 200)), DEUTAN)
    assert report.pairs == ()
    assert report.eligible_count == 0
    assert report.improved_count == 0
    assert report.newly_confusable == ()


def _palette(colors):
    colors = np.array(colors, dtype=np.uint8)
    return Palette2(
        colors_rgb=colors,
        colors_lab=rgb_to_lab(colors[np.newaxis])[0],
        labels=np.arange(len(colors), dtype=np.int32)[np.newaxis],
        counts=np.ones(len(colors), dtype=np.int64),
    )


def test_pair_pushed_below_threshold_is_newly_confusable():
    # Red and blue are far apart under deutan. Moving blue onto red's color makes them collide.
    palette = _palette([(200, 40, 40), (40, 40, 200)])
    confusion = ConfusionResult3(
        palette=palette,
        profile=DEUTAN,
        threshold=10.0,
        pairs=(),
        groups=(),
        mask=np.zeros((1, 2), dtype=bool),
    )
    after = palette.colors_lab.copy()
    after[1] = after[0]
    enhanced = EnhancedImage4(
        pixels=np.zeros((1, 2, 3), dtype=np.uint8),
        palette_lab_after=after,
        changed=np.array([False, True]),
    )
    report = check_separation_5(confusion, enhanced, DEUTAN, 10.0)
    assert report.newly_confusable == ((0, 1),)
    assert report.eligible_count == 0


def test_flagged_pairs_are_never_listed_as_newly_confusable():
    palette = _palette([(200, 40, 40), (40, 160, 40)])
    pair = ConfusablePair(a=0, b=1, original_distance=71.4, simulated_distance=7.0)
    confusion = ConfusionResult3(
        palette=palette,
        profile=DEUTAN,
        threshold=10.0,
        pairs=(pair,),
        groups=((0, 1),),
        mask=np.ones((1, 2), dtype=bool),
    )
    enhanced = EnhancedImage4(
        pixels=np.zeros((1, 2, 3), dtype=np.uint8),
        palette_lab_after=palette.colors_lab.copy(),
        changed=np.zeros(2, dtype=bool),
    )
    report = check_separation_5(confusion, enhanced, DEUTAN, 10.0)
    assert report.newly_confusable == ()


def test_rejects_an_enhanced_palette_of_the_wrong_size():
    confusion, enhanced, _ = _pipeline(_graphic((200, 40, 40), (40, 160, 40)), DEUTAN)
    wrong = EnhancedImage4(
        pixels=enhanced.pixels,
        palette_lab_after=enhanced.palette_lab_after[:1],
        changed=enhanced.changed[:1],
    )
    with pytest.raises(ValueError):
        check_separation_5(confusion, wrong, DEUTAN, 10.0)
