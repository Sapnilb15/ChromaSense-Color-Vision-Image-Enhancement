# Increment 06: Palette extraction (filter 2)

**Status:** Standard
**Depends on:** 05
**SRS IDs:** SRS-FR-005

### Main rules

- Add filter 2 only: `extract_palette_2(pixels: NDArray, color_count: int) -> Palette2`.
- Cluster in CIELAB with `sklearn.cluster.KMeans` and a fixed `random_state`, so the same image always gives the same palette.

### Capability

An image becomes a small set of dominant colors, with each pixel assigned to one of them.

### What may change

- `models.py`: add `Palette2`.
- New files: `src/color_engine/color_engine/pipeline/filter_2_palette/extract_palette_2.py`, `src/color_engine/tests/pipeline/test_filter_2_palette.py`.

### What must stay

- Filter 1 and the color rules.

### Implementation notes

1. `@dataclass(frozen=True) class Palette2` (`derived`): `colors_rgb: NDArray` (K × 3 `uint8`), `colors_lab: NDArray` (K × 3 float), `labels: NDArray` (height × width `int`, the palette index of each pixel), `counts: NDArray` (K pixel counts).
2. Fit k-means on a fixed random sample of at most 50,000 pixels in CIELAB. Then assign every pixel to its nearest center in CIELAB. Merge centers closer than CIEDE2000 2.3, since they are the same color to a viewer. Use fewer clusters when the image has fewer distinct colors than `color_count`.
3. You may port release 0.5's code with `git show v0.5:BlindSpot_ChromaSense-main/src/color_engine/color_engine/pipeline/filter_3_palette/extract_palette_3.py`, renamed to the new contract.
4. Assigning every pixel of a 12 megapixel image must stay inside the 30-second budget of SRS-NFR-001. Process the assignment in chunks rather than one full distance matrix.

### Verification

- For a flat graphic with 5 known colors, the palette has a color within CIEDE2000 2 of each known color, and `labels` assigns each region to the matching index.
- Two runs on the same image give identical palettes.
- `docker compose run --rm dev pytest src/color_engine/tests` passes.

### Main rules (repeated)

- Add filter 2 only: `extract_palette_2(pixels: NDArray, color_count: int) -> Palette2`.
- Cluster in CIELAB with `sklearn.cluster.KMeans` and a fixed `random_state`.
