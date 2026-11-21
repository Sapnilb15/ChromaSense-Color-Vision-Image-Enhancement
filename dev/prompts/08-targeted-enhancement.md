# Increment 08: Targeted enhancement (filter 4)

**Status:** CRITICAL
**Depends on:** 07
**SRS IDs:** SRS-FR-006, SRS-FR-007

### Main rules

- Add filter 4 only: `enhance_4(pixels: NDArray, confusion: ConfusionResult3) -> EnhancedImage4`.
- Use lightness separation (Decision 2). Do not add daltonization, hue rotation, a strength control, or a global filter.
- Change only pixels where `confusion.mask` is true. Every pixel outside the mask must be byte-identical to the input.

### Capability

The engine moves the CIELAB lightness of each confusable color group apart, inside the mask only.

### What may change

- `models.py`: add `EnhancedImage4`.
- New files: `src/color_engine/color_engine/pipeline/filter_4_enhance/enhance_4.py`, `src/color_engine/tests/pipeline/test_filter_4_enhance.py`.

### What must stay

- Filters 1 to 3 and the color rules.

### Implementation notes

1. `@dataclass(frozen=True) class EnhancedImage4` (`derived`): `pixels: NDArray` (`uint8`, same shape as the input), `palette_lab_after: NDArray` (K × 3; for each palette index, the mean CIELAB of its enhanced pixels if the color moved, otherwise its original palette color), `changed: NDArray` (K `bool`, true for palette indexes that moved).
2. Method, from `docs/enhancement-evaluation-v0.5.md`: within each group in `confusion.groups`, space the colors 22 CIELAB lightness units apart, between 15 and 90. Avoid the lightness of colors outside the group first, then move each color as little as possible. Add the shift to the `L` channel of each masked pixel of that color and keep its `a` and `b`.
3. You may port release 0.5's code with `git show v0.5:BlindSpot_ChromaSense-main/src/color_engine/color_engine/pipeline/filter_9_enhance/enhance_9.py`. Remove its `strength` argument, and use a fixed strength of 1.0.
4. Convert only the masked pixels of colors that moved back to sRGB. Copy every other pixel from the input unchanged, including masked pixels whose shift is zero, so color conversion round-off cannot alter them.
5. With no flagged pairs, return the input pixels unchanged and `changed` all false.

### Verification

- For the deutan red–green flat graphic from increment 07, `np.array_equal(enhanced.pixels[~mask], pixels[~mask])` is true.
- The CIELAB lightness difference between the two flagged colors grows to at least 20 after enhancement.
- With no flagged pairs, the output equals the input exactly.
- On a photo-like image with noise inside each region, the unchanged-outside-mask check still holds.
- `docker compose run --rm dev pytest src/color_engine/tests` passes.

### Risk

This is where requirements conflict: separation must grow, and every pixel outside the targeted regions must stay identical. Gamut clipping can also undo part of a lightness shift for saturated colors.

### Failure indicators

- Any changed pixel outside the mask, often from converting the whole image through CIELAB and back.
- Lightness shifts that clip to white or black and reduce the CIEDE2000 distance.
- Masked pixels of an unmoved color that differ by 1 unit.

### Isolation test

Use a synthetic 3-color image (red, green, and a gray background) with a hand-made `ConfusionResult3` whose mask and groups are set directly, without filters 2 and 3. Check the gray pixels byte for byte and the lightness of the two colors.

### Rollback

Delete `filter_4_enhance/enhance_4.py`, its test, and `EnhancedImage4`. Return to the state after `07-confusion-detection.md` and set this row to `rolled back`.

### Main rules (repeated)

- Add filter 4 only.
- Use lightness separation. Do not add daltonization, hue rotation, a strength control, or a global filter.
- Change only pixels where `confusion.mask` is true.
