"""Build a ChartQA bar-chart set in the acceptance labels.json format, and measure it.

ChartQA (Masry et al., 2022, GPL-3.0) annotates every bar with its box and hex color, so each
bar is a target region with a known reference color. Line and pie charts are skipped because
their annotations give no solid region to measure.

The set is written outside tests/data/acceptance/, which holds the team's held-out images and
must not be generated. It is an extra development measurement, not the SRS-NFR-007 result.

    python tools/chartqa_dataset.py build --limit 200
    python tools/chartqa_dataset.py evaluate

Run from src/color_engine with the engine installed (pip install -e ".[test]"). Only the
annotations and the needed PNGs are read from the 875 MB zip, using HTTP range requests.
"""

import argparse
import importlib.util
import io
import json
import sys
import time
import urllib.request
import zipfile
from itertools import combinations
from pathlib import Path

import numpy as np

from color_engine.models import CvdProfile, CvdType, DecodeError, InputLimits
from color_engine.pipeline.filter_1_decode.decode_1 import decode_1
from color_engine.rules.color_spaces import rgb_to_lab
from color_engine.rules.distance import ciede2000
from color_engine.rules.simulation import simulate

ENGINE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ENGINE_ROOT / "tests" / "data" / "chartqa"
ACCEPTANCE_TEST = ENGINE_ROOT / "tests" / "acceptance" / "test_separation_target.py"
ZIP_URL = "https://huggingface.co/datasets/ahmed-masry/ChartQA/resolve/main/ChartQA%20Dataset.zip"
ZIP_ROOT = "ChartQA Dataset"
BAR_TYPES = ("v_bar", "h_bar")

# A bar is kept only when its inset interior is a flat fill near the annotated color. The fill's
# measured color is the reference, because some sources (Our World in Data) draw bars with
# partial opacity, so the rendered color sits several units of CIEDE2000 from the annotated hex.
INSET = 2
MIN_SIDE = 4
MAX_FILL_SPREAD = 2.0
MIN_FILL_SHARE = 0.95
MAX_ANNOTATION_ERROR = 15.0


class _HttpRangeFile(io.RawIOBase):
    """A read-only, seekable view of a remote file, so zipfile fetches only what it reads."""

    def __init__(self, url: str) -> None:
        request = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(request, timeout=60) as response:
            self._url = response.url
            self._size = int(response.headers["Content-Length"])
        self._position = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self._position

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self._position, io.SEEK_END: self._size}[whence]
        self._position = base + offset
        return self._position

    def readinto(self, buffer) -> int:
        if self._position >= self._size:
            return 0
        end = min(self._size, self._position + len(buffer)) - 1
        data = self._fetch(self._position, end)
        buffer[: len(data)] = data
        self._position += len(data)
        return len(data)

    def _fetch(self, start: int, end: int) -> bytes:
        request = urllib.request.Request(self._url, headers={"Range": f"bytes={start}-{end}"})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    return response.read()
            except OSError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
        raise AssertionError("unreachable")


def _open_zip(local_zip: Path | None) -> zipfile.ZipFile:
    if local_zip is not None:
        return zipfile.ZipFile(local_zip)
    return zipfile.ZipFile(io.BufferedReader(_HttpRangeFile(ZIP_URL), buffer_size=1 << 20))


def _hex_to_rgb(value) -> tuple[int, int, int] | None:
    """Return the RGB of a #rrggbb string; named colors such as 'dark brown' give None."""
    if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
        return None
    try:
        return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))
    except ValueError:
        return None


def _bars(annotation: dict) -> list[tuple[dict, tuple[int, int, int]]]:
    """Return each annotated bar's box with its color, from per-bar or per-series colors."""
    bars = []
    for model in annotation.get("models", []):
        boxes = model.get("bboxes") or []
        colors = model.get("colors", model.get("color"))
        if not isinstance(colors, list):
            colors = [colors] * len(boxes)
        for box, color in zip(boxes, colors, strict=False):
            rgb = _hex_to_rgb(color)
            if rgb is not None:
                bars.append((box, rgb))
    return bars


def _verified_box(
    pixels: np.ndarray, box: dict, rgb: tuple[int, int, int]
) -> tuple[list[int], list[int]] | None:
    """Return the inset [x, y, width, height] and its fill color, when it is a flat fill.

    The fill must also be near the annotated color, which rejects boxes that miss their bar.
    """
    left = int(np.ceil(box["x"])) + INSET
    top = int(np.ceil(box["y"])) + INSET
    right = int(np.floor(box["x"] + box["w"])) - INSET
    bottom = int(np.floor(box["y"] + box["h"])) - INSET
    height, width = pixels.shape[:2]
    if left < 0 or top < 0 or right > width or bottom > height:
        return None
    if right - left < MIN_SIDE or bottom - top < MIN_SIDE:
        return None
    fill_rgb = pixels[top:bottom, left:right].reshape(-1, 3)
    fill = np.median(fill_rgb, axis=0).astype(np.uint8)
    lab = rgb_to_lab(np.vstack([fill_rgb, fill, np.array(rgb, dtype=np.uint8)])[None])[0]
    spread = ciede2000(lab[:-2], lab[-2])
    if float(np.mean(spread <= MAX_FILL_SPREAD)) < MIN_FILL_SHARE:
        return None
    if float(ciede2000(lab[-2], lab[-1])) > MAX_ANNOTATION_ERROR:
        return None
    return [left, top, right - left, bottom - top], fill.tolist()


def _regions(pixels: np.ndarray, annotation: dict) -> list[dict]:
    """Return one verified region per annotated bar color, using that color's largest bar."""
    largest: dict[tuple[int, int, int], tuple[list[int], list[int]]] = {}
    for box, rgb in _bars(annotation):
        verified = _verified_box(pixels, box, rgb)
        if verified is None:
            continue
        current = largest.get(rgb)
        area = verified[0][2] * verified[0][3]
        if current is None or area > current[0][2] * current[0][3]:
            largest[rgb] = verified
    return [
        {"id": f"bar-{index}", "box": box, "reference_rgb": fill}
        for index, (box, fill) in enumerate(largest.values())
    ]


def _eligible_pairs(regions: list[dict], threshold: float, severity: float) -> dict[str, int]:
    """Count region pairs that are distinct normally but confusable under each profile."""
    counts = {}
    for cvd_type in CvdType:
        profile = CvdProfile(cvd_type, severity)
        count = 0
        for first, second in combinations(regions, 2):
            rgb = np.array([[first["reference_rgb"], second["reference_rgb"]]], dtype=np.uint8)
            original = rgb_to_lab(rgb)[0]
            simulated = rgb_to_lab(simulate(rgb, profile))[0]
            count += bool(
                ciede2000(original[0], original[1]) >= threshold
                and ciede2000(simulated[0], simulated[1]) < threshold
            )
        counts[cvd_type.value] = count
    return counts


def build(args: argparse.Namespace) -> None:
    """Write the split's verified bar charts and their labels.json to the output folder."""
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    archive = _open_zip(args.zip)
    prefix = f"{ZIP_ROOT}/{args.split}/annotations/"
    names = sorted(n for n in archive.namelist() if n.startswith(prefix) and n.endswith(".json"))
    print(f"{len(names)} {args.split} annotations", file=sys.stderr)

    entries, skipped = [], {"not a bar chart": 0, "fewer than 2 regions": 0, "no eligible pair": 0}
    skipped["undecodable"] = 0
    for name in names:
        if args.limit and len(entries) >= args.limit:
            break
        annotation = json.loads(archive.read(name))
        if annotation.get("type") not in BAR_TYPES or len(_bars(annotation)) < 2:
            skipped["not a bar chart"] += 1
            continue

        stem = Path(name).stem
        image_path = out / f"{stem}.png"
        if image_path.exists():
            data = image_path.read_bytes()
        else:
            data = archive.read(f"{ZIP_ROOT}/{args.split}/png/{stem}.png")
        try:
            pixels = decode_1(data, InputLimits()).pixels
        except DecodeError:
            skipped["undecodable"] += 1
            continue

        regions = _regions(pixels, annotation)
        if len(regions) < 2:
            skipped["fewer than 2 regions"] += 1
            continue
        eligible = _eligible_pairs(regions, args.threshold, args.severity)
        if args.confusable_only and not any(eligible.values()):
            skipped["no eligible pair"] += 1
            continue

        image_path.write_bytes(data)
        entries.append(
            {
                "file": image_path.name,
                "type": "chart",
                "source": f"ChartQA {args.split} {annotation['type']}",
                "eligible_pairs": eligible,
                "regions": regions,
            }
        )
        if len(entries) % 25 == 0:
            print(f"  {len(entries)} charts kept", file=sys.stderr)

    labels = {"threshold": args.threshold, "severity": args.severity, "images": entries}
    (out / "labels.json").write_text(json.dumps(labels, indent=2) + "\n", encoding="utf-8")

    totals = {t.value: sum(e["eligible_pairs"][t.value] for e in entries) for t in CvdType}
    print(f"Wrote {len(entries)} charts to {out}", file=sys.stderr)
    print(f"Eligible pairs: {totals}", file=sys.stderr)
    print(f"Skipped: {skipped}", file=sys.stderr)


def evaluate(args: argparse.Namespace) -> None:
    """Run the acceptance test's own measurement on the built folder and print its report."""
    spec = importlib.util.spec_from_file_location("acceptance_measurement", ACCEPTANCE_TEST)
    measurement = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(measurement)
    result = measurement.evaluate(args.out)
    print(measurement.report(result))
    print(
        "\nPixels changed outside target regions include other bars and legend swatches of "
        "the same colors, because only the largest bar per color is a region."
    )


def main() -> None:
    """Parse the command line and run the build or evaluate command."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    build_parser = commands.add_parser("build", help="download and label ChartQA bar charts")
    build_parser.add_argument("--split", choices=("test", "val", "train"), default="test")
    build_parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    build_parser.add_argument("--zip", type=Path, help="local ChartQA zip instead of downloading")
    build_parser.add_argument("--limit", type=int, default=0, help="stop after this many charts")
    build_parser.add_argument("--threshold", type=float, default=10.0)
    build_parser.add_argument("--severity", type=float, default=1.0)
    build_parser.add_argument(
        "--confusable-only",
        action="store_true",
        help="keep only charts with at least one eligible pair for either profile",
    )
    build_parser.set_defaults(handler=build)

    evaluate_parser = commands.add_parser("evaluate", help="measure the built folder")
    evaluate_parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    evaluate_parser.set_defaults(handler=evaluate)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
