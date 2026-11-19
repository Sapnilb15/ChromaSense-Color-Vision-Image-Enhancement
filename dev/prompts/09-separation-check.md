# Increment 09: Separation check (filter 5)

**Status:** Standard
**Depends on:** 08
**SRS IDs:** SRS-FR-009, SRS-NFR-007

### Main rules

- Add filter 5 only: `check_separation_5(confusion: ConfusionResult3, enhanced: EnhancedImage4, profile: CvdProfile, threshold: float) -> SeparationReport5`.
- A pair is improved when its simulated CIEDE2000 distance after enhancement is greater than before (Decision 2).

### Capability

The engine reports, for each flagged pair, whether enhancement increased its simulated separation, and which pairs became newly confusable.

### What may change

- `models.py`: add `PairSeparation` and `SeparationReport5`.
- New files: `src/color_engine/color_engine/pipeline/filter_5_separation/check_separation_5.py`, `src/color_engine/tests/pipeline/test_filter_5_separation.py`.

### What must stay

- Filters 1 to 4 and the color rules.

### Implementation notes

1. Models (`derived`):
   - `@dataclass(frozen=True) class PairSeparation`: `a: int`, `b: int`, `before: float`, `after: float`, `improved: bool`.
   - `@dataclass(frozen=True) class SeparationReport5`: `pairs: tuple[PairSeparation, ...]`, `newly_confusable: tuple[tuple[int, int], ...]`, `eligible_count: int`, `improved_count: int`.
2. `before` is the flagged pair's `simulated_distance`. `after` is the CIEDE2000 distance between the simulated colors of `enhanced.palette_lab_after` for the same indexes.
3. A pair is newly confusable when it was not flagged, its simulated distance was at least the threshold before, and is below it after.
4. `eligible_count` is the number of flagged pairs. `improved_count` counts pairs with `improved` true.

### Verification

- For the deutan and protan red–green flat graphics from increment 07, after filter 4 the report has `eligible_count == 1`, `improved_count == 1`, and no newly confusable pairs.
- With a hand-made `EnhancedImage4` whose colors did not move, every pair has `improved` false.
- With no flagged pairs, both counts are 0.
- `docker compose run --rm dev pytest src/color_engine/tests --cov=color_engine --cov-fail-under=70` passes.

### Main rules (repeated)

- Add filter 5 only.
- A pair is improved when its simulated CIEDE2000 distance after enhancement is greater than before.
