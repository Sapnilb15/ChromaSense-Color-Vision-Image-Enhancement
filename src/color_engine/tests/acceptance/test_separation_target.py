"""Acceptance evaluation for SRS-NFR-007: at least 80 percent of eligible pairs improve per profile.

The held-out images and labels.json in tests/data/acceptance/ are supplied by the team and set
aside before tuning. Never create, generate, or alter them. Run with -s to see the report:

    pytest src/color_engine/tests/acceptance -s
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from color_engine.models import CvdProfile, CvdType, InputLimits
from color_engine.pipeline.filter_1_decode.decode_1 import decode_1
from color_engine.pipeline.filter_2_palette.extract_palette_2 import extract_palette_2
from color_engine.pipeline.filter_3_confusion.detect_confusion_3 import detect_confusion_3
from color_engine.pipeline.filter_4_enhance.enhance_4 import enhance_4
from color_engine.pipeline.filter_5_separation.check_separation_5 import check_separation_5
from color_engine.rules.color_spaces import lab_to_rgb, rgb_to_lab
from color_engine.rules.distance import ciede2000
from color_engine.rules.simulation import simulate

HELD_OUT = Path(__file__).resolve().parents[1] / "data" / "acceptance"
PALETTE_COLORS = 12
TARGET = 0.80


@dataclass
class Tally:
    eligible: int = 0
    improved: int = 0
    above_threshold: int = 0
    newly_confusable: int = 0
    changed_outside: int = 0
    images: set = field(default_factory=set)


def _simulated_distance(lab_a, lab_b, profile: CvdProfile) -> float:
    rgb = lab_to_rgb(np.array([[lab_a, lab_b]]))
    simulated = rgb_to_lab(simulate(rgb, profile))[0]
    return float(ciede2000(simulated[0], simulated[1]))


def _region_mean_lab(pixels: np.ndarray, box) -> np.ndarray:
    x, y, width, height = box
    return rgb_to_lab(pixels[y : y + height, x : x + width]).reshape(-1, 3).mean(axis=0)


def evaluate(folder: Path) -> dict:
    """Measure every labeled image under protan and deutan; return tallies and settings."""
    labels = json.loads((folder / "labels.json").read_text(encoding="utf-8"))
    threshold, severity = float(labels["threshold"]), float(labels["severity"])
    tallies: dict[tuple[str, str], Tally] = defaultdict(Tally)

    for entry in labels["images"]:
        pixels = decode_1((folder / entry["file"]).read_bytes(), InputLimits()).pixels
        regions = entry["regions"]
        inside = np.zeros(pixels.shape[:2], dtype=bool)
        for region in regions:
            x, y, width, height = region["box"]
            inside[y : y + height, x : x + width] = True

        for cvd_type in CvdType:
            profile = CvdProfile(cvd_type, severity)
            palette = extract_palette_2(pixels, PALETTE_COLORS)
            confusion = detect_confusion_3(pixels, palette, profile, threshold)
            enhanced = enhance_4(pixels, confusion)
            check_separation_5(confusion, enhanced, profile, threshold)

            tally = tallies[(cvd_type.value, entry["type"])]
            tally.images.add(entry["file"])
            changed = np.any(enhanced.pixels != pixels, axis=-1)
            tally.changed_outside += int((changed & ~inside).sum())

            for first, second in combinations(regions, 2):
                reference = rgb_to_lab(
                    np.array([[first["reference_rgb"], second["reference_rgb"]]], dtype=np.uint8)
                )[0]
                original = float(ciede2000(reference[0], reference[1]))
                reference_simulated = _simulated_distance(reference[0], reference[1], profile)
                before = _simulated_distance(
                    _region_mean_lab(pixels, first["box"]),
                    _region_mean_lab(pixels, second["box"]),
                    profile,
                )
                after = _simulated_distance(
                    _region_mean_lab(enhanced.pixels, first["box"]),
                    _region_mean_lab(enhanced.pixels, second["box"]),
                    profile,
                )
                eligible = original >= threshold and reference_simulated < threshold
                if eligible:
                    tally.eligible += 1
                    tally.improved += after > before
                    tally.above_threshold += after >= threshold
                elif before >= threshold and after < threshold:
                    tally.newly_confusable += 1

    return {"threshold": threshold, "severity": severity, "tallies": dict(tallies)}


def report(result: dict) -> str:
    lines = [
        f"Threshold {result['threshold']:g}, severity {result['severity']:g}, "
        f"palette colors {PALETTE_COLORS}",
        "",
        "| Profile | Image type | Images | Improved | Eligible | Percent | Above threshold after "
        "| Newly confusable | Pixels changed outside target regions |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for (profile, image_type), tally in sorted(result["tallies"].items()):
        percent = f"{100 * tally.improved / tally.eligible:.1f}" if tally.eligible else "n/a"
        lines.append(
            f"| {profile} | {image_type} | {len(tally.images)} | {tally.improved} | "
            f"{tally.eligible} | {percent} | {tally.above_threshold} | "
            f"{tally.newly_confusable} | {tally.changed_outside} |"
        )
    for profile, (improved, eligible) in sorted(_by_profile(result).items()):
        percent = f"{100 * improved / eligible:.1f}" if eligible else "n/a"
        lines.append(f"| {profile} | all | | {improved} | {eligible} | {percent} | | | |")
    return "\n".join(lines)


def _by_profile(result: dict) -> dict[str, tuple[int, int]]:
    totals: dict[str, list[int]] = {cvd_type.value: [0, 0] for cvd_type in CvdType}
    for (profile, _), tally in result["tallies"].items():
        totals[profile][0] += tally.improved
        totals[profile][1] += tally.eligible
    return {profile: (improved, eligible) for profile, (improved, eligible) in totals.items()}


def test_held_out_set_meets_the_80_percent_target():
    labels = json.loads((HELD_OUT / "labels.json").read_text(encoding="utf-8"))
    if not labels["images"]:
        pytest.skip("held-out set not supplied")

    result = evaluate(HELD_OUT)
    print("\n" + report(result))
    for profile, (improved, eligible) in _by_profile(result).items():
        assert eligible > 0, f"no eligible pairs for {profile}"
        assert improved / eligible >= TARGET, (
            f"{profile}: {improved} of {eligible} eligible pairs improved, below 80 percent"
        )


def test_measurement_on_development_graphics(tmp_path):
    """Isolation test: the same measurement on synthetic images, never the held-out set."""
    images = [
        ("deutan-pair.png", "chart", (200, 40, 40), (40, 160, 40)),
        ("protan-pair.png", "map", (220, 40, 40), (40, 100, 40)),
        ("distinct-pair.png", "chart", (200, 40, 40), (40, 40, 200)),
    ]
    entries = []
    for name, image_type, first, second in images:
        pixels = np.full((60, 120, 3), 128, dtype=np.uint8)
        pixels[10:50, 10:55] = first
        pixels[10:50, 65:110] = second
        Image.fromarray(pixels).save(tmp_path / name)
        entries.append(
            {
                "file": name,
                "type": image_type,
                "regions": [
                    {"id": "a", "box": [10, 10, 45, 40], "reference_rgb": list(first)},
                    {"id": "b", "box": [65, 10, 45, 40], "reference_rgb": list(second)},
                ],
            }
        )
    labels = {"threshold": 10, "severity": 1.0, "images": entries}
    (tmp_path / "labels.json").write_text(json.dumps(labels), encoding="utf-8")

    result = evaluate(tmp_path)
    print("\n" + report(result))

    tallies = result["tallies"]
    deutan_chart, protan_map = tallies[("deutan", "chart")], tallies[("protan", "map")]
    assert (deutan_chart.eligible, deutan_chart.improved) == (1, 1)
    assert (protan_map.eligible, protan_map.improved) == (1, 1)
    # The red-green pairs are each eligible only for their own profile.
    assert tallies[("protan", "chart")].eligible == 0
    assert all(tally.changed_outside == 0 for tally in tallies.values())
    assert all(tally.newly_confusable == 0 for tally in tallies.values())
    assert _by_profile(result) == {"deutan": (1, 1), "protan": (1, 1)}
    assert "| deutan | all | | 1 | 1 | 100.0 |" in report(result)
