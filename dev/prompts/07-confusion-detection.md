# Increment 07: Confusion detection (filter 3)

**Status:** Standard
**Depends on:** 06
**SRS IDs:** SRS-FR-005

### Main rules

- Add filter 3 only: `detect_confusion_3(pixels: NDArray, palette: Palette2, profile: CvdProfile, threshold: float) -> ConfusionResult3`.
- A pair is confusable only when its CIEDE2000 distance is at least the threshold in the original and below the threshold after simulation (Decision 2).

### Capability

The engine finds which palette color pairs become hard to tell apart under the selected profile, and which pixels belong to them.

### What may change

- `models.py`: add `ConfusablePair` and `ConfusionResult3`.
- New files: `src/color_engine/color_engine/pipeline/filter_3_confusion/detect_confusion_3.py`, `src/color_engine/tests/pipeline/test_filter_3_confusion.py`.

### What must stay

- Filters 1 and 2 and the color rules. Filter 3 calls rules, never another filter.

### Implementation notes

1. Models (`derived`):
   - `@dataclass(frozen=True) class ConfusablePair`: `a: int`, `b: int` (palette indexes, `a < b`), `original_distance: float`, `simulated_distance: float`.
   - `@dataclass(frozen=True) class ConfusionResult3`: `palette: Palette2`, `profile: CvdProfile`, `threshold: float`, `pairs: tuple[ConfusablePair, ...]`, `groups: tuple[tuple[int, ...], ...]` (connected sets of palette indexes linked by flagged pairs), `mask: NDArray` (height × width `bool`, true where the pixel's palette index is in a flagged pair).
2. Simulate the palette colors (not the whole image) with `simulate`, convert to CIELAB, and compare every pair with `ciede2000`.
3. The `pixels` argument is kept for the contract; the mask comes from `palette.labels`.

### Verification

These test colors were measured with the release 0.5 Machado matrices at severity 1.0:

| Pair | Original CIEDE2000 | Simulated CIEDE2000 |
| --- | --- | --- |
| Red `(200, 40, 40)` and green `(40, 160, 40)` under deutan | 71.4 | 7.1 |
| Red `(220, 40, 40)` and green `(40, 100, 40)` under protan | 61.7 | 1.1 |
| Red `(200, 40, 40)` and blue `(40, 40, 200)` under deutan | 44.0 | 63.8 |

- At threshold 10, the deutan red–green flat graphic flags its pair and the mask covers exactly those two regions. The protan pair is flagged under protan in the same way.
- The red and blue pair is not flagged.
- The deutan red–green pair is not flagged at threshold 5 and is flagged at threshold 10, which shows that the threshold changes the result.
- Severity 0 flags no pairs.
- `docker compose run --rm dev pytest src/color_engine/tests` passes.

### Main rules (repeated)

- Add filter 3 only.
- A pair is confusable only when its CIEDE2000 distance is at least the threshold in the original and below the threshold after simulation.
