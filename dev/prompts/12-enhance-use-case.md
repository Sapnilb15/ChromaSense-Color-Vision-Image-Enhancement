# Increment 12: Enhance use case and outcome policy

**Status:** Standard
**Depends on:** 11
**SRS IDs:** SRS-FR-003, SRS-FR-005, SRS-FR-006, SRS-FR-009, SRS-FR-011

### Main rules

- Add `EnhanceImage`, `EnhancementResult`, `PairOutcome`, `Outcome`, and `core/policy/outcome.py` only.
- Run filters 2, 3, 4, and 5 in that order on the stored original. Reuse the stored palette when only the profile changed.
- Accept protan and deutan only, with severity from 0 to 1.

### Capability

For the session's image and a chosen profile, Application Core produces an enhanced result, or says why there is none.

### What may change

- `core/models.py`: add `Outcome`, `PairOutcome`, and `EnhancementResult`.
- New files: `core/policy/outcome.py`, `core/use_cases/enhance_image.py`, and tests in `src/portal/tests/core/`.

### What must stay

- `ProcessUpload` behavior and the port signatures from increment 11.

### Implementation notes

1. Models (`derived` fields):
   - `class Outcome(Enum)`: `ENHANCED`, `NO_CONFUSABLE_PAIRS`, `NOT_IMPROVED`.
   - `@dataclass(frozen=True) class PairOutcome`: `color_a_hex: str`, `color_b_hex: str`, `before: float`, `after: float`, `improved: bool`.
   - `@dataclass(frozen=True) class EnhancementResult`: `image_id: str`, `profile: CvdProfile`, `outcome: Outcome`, `message: str`, `palette: Palette2`, `mask: NDArray`, `enhanced_pixels: NDArray | None` (set only when the outcome is `ENHANCED`), `pairs: tuple[PairOutcome, ...]`, `eligible_count: int`, `improved_count: int`, `newly_confusable_count: int`.
2. `policy/outcome.py`:
   - `outcome_for(report: SeparationReport5) -> Outcome`: `NO_CONFUSABLE_PAIRS` when `eligible_count == 0`; `NOT_IMPROVED` when `improved_count == 0`; otherwise `ENHANCED`.
   - `message_for(outcome, report, profile) -> str` (`derived`). Name the profile as "protan" or "deutan" and give severity as a number. Make no claim about diagnosis or about exactly what typical color vision sees:
     - `NO_CONFUSABLE_PAIRS`: "No colors likely to be confused were found for the {profile} profile at severity {severity}. The original image is unchanged."
     - `NOT_IMPROVED`: "Colors likely to be confused were found, but the adjustment could not increase their separation. The original image is still available."
     - `ENHANCED`: "Adjusted {improved} of {eligible} color pairs likely to be confused." If some pairs were not improved, add " {n} pairs could not be improved."
3. `EnhanceImage(store, clock, settings)`. `execute(EnhanceImageRequest(session_id: str, profile: CvdProfile)) -> EnhanceImageResponse(outcome, message, eligible_count, improved_count, pairs)`.
   - No stored original → `NoImageInSession("Upload an image first.")`.
   - If a stored result has the same `image_id`, reuse its `palette` and skip filter 2.
   - Store the new result and touch the session.

### Verification

- With a fake store and the deutan red–green flat graphic: outcome `ENHANCED`, `eligible_count == 1`, `improved_count == 1`, and the enhanced pixels outside the mask equal the original.
- A flat graphic of red and blue: outcome `NO_CONFUSABLE_PAIRS` with its message and no enhanced pixels.
- A test with filter 5 replaced by a stub that reports no improvement gives `NOT_IMPROVED` and its message.
- Changing deutan to protan on the same image calls filter 2 once in total, measured with a spy, and gives a new result.
- With no image: `NoImageInSession`.
- `docker compose run --rm dev pytest src/portal/tests/core` passes.

### Main rules (repeated)

- Add `EnhanceImage`, its models, and the outcome policy only.
- Run filters 2 to 5 in order on the stored original. Reuse the stored palette when only the profile changed.
- Accept protan and deutan only, with severity from 0 to 1.
