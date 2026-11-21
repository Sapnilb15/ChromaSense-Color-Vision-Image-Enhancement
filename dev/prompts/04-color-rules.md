# Increment 04: Color rules

**Status:** CRITICAL
**Depends on:** 03
**SRS IDs:** SRS-FR-005, SRS-NFR-007 (the simulation and distance that detection and the 80 percent measure rely on)

### Main rules

- Add the unnumbered color rules and shared engine models only. Add no pipeline filter.
- Simulate with Machado (2009) in linear RGB, interpolated by severity (Decision 2). Support protan and deutan only.
- Color Engine imports only NumPy, Pillow, scikit-image, scikit-learn, and the standard library.

### Capability

Color Engine can convert color spaces, simulate a protan or deutan profile at any severity from 0 to 1, measure CIEDE2000 distance, and encode pixels as PNG.

### What may change

- New files: `src/color_engine/color_engine/models.py` (first part), `src/color_engine/color_engine/data/machado_2009.json`, `src/color_engine/color_engine/rules/color_spaces.py`, `distance.py`, `simulation.py`, `encode.py`, and `src/color_engine/tests/rules/test_*.py` for each.

### What must stay

- Configuration from increments 01 to 03. Do not edit the import-linter contracts.

### Implementation notes

1. **`models.py`** (contracts from `dev/architecture.md`; field details `derived`):
   - `class CvdType(Enum)`: `PROTAN = "protan"`, `DEUTAN = "deutan"`.
   - `@dataclass(frozen=True) class CvdProfile`: `type: CvdType`, `severity: float`. Raise `ValueError` if severity is outside 0 to 1.
   - `@dataclass(frozen=True) class InputLimits`: `max_bytes: int = 10 * 1024 * 1024`, `max_megapixels: float = 12.0`.
2. **`data/machado_2009.json`**: copy it from release 0.5: `git show v0.5:BlindSpot_ChromaSense-main/src/color_engine/color_engine/data/machado_2009.json > src/color_engine/color_engine/data/machado_2009.json`. It holds the `protan` and `deutan` 3×3 matrices at severity 0.0 to 1.0 in steps of 0.1. Load it with `importlib.resources`.
3. **`rules/color_spaces.py`**: `srgb_to_linear(pixels)` and `linear_to_srgb(pixels)` on floats from 0 to 1, with the standard sRGB transfer function. Also `rgb_to_lab(pixels_uint8)` and `lab_to_rgb(lab)`, using `skimage.color.rgb2lab` and `lab2rgb`, returning `uint8` for `lab_to_rgb` with rounding and clipping.
4. **`rules/simulation.py`**: `simulate(pixels: NDArray, profile: CvdProfile) -> NDArray`. Input and output are `uint8` sRGB of the same shape. Linearize, apply the matrix interpolated linearly between the two nearest 0.1 steps, clip to 0 to 1, and re-encode. Severity 0 returns the input unchanged.
5. **`rules/distance.py`**: `ciede2000(lab_a, lab_b) -> NDArray | float` using `skimage.color.deltaE_ciede2000`, accepting single colors or arrays of colors.
6. **`rules/encode.py`**: `encode_png(pixels: NDArray) -> bytes` using `Image.fromarray(pixels, "RGB").save(buffer, format="PNG")`.
7. You may read the release 0.5 rules with `git show v0.5:BlindSpot_ChromaSense-main/src/color_engine/color_engine/rules/<file>.py` and port them. Remove tritan, achromatopsia, naming, and overlay code.

### Verification

- `test_distance.py` reproduces the Sharma (2005) CIEDE2000 test pairs within 0.0001. Pair 1, `(50, 2.6772, -79.7751)` against `(50, 0, -82.7485)`, gives 2.0425.
- `test_simulation.py` compares `simulate` with `daltonlens.simulate.Simulator_Machado2009` for protan and deutan at severities 0.3, 0.7, and 1.0 on a random 64×64 image and a red–green test image. The mean per pixel difference is under 1 percent.
- `test_color_spaces.py` shows that `linear_to_srgb(srgb_to_linear(x))` returns `x` within 1e-6.
- `test_encode.py` shows that decoding the output of `encode_png` with Pillow gives the same pixels.
- `docker build --target engine-test .` now succeeds.

### Risk

This is the first complex color operation, and every later measure depends on it. A gamma, matrix orientation, or interpolation mistake makes detection and the 80 percent measure wrong without any crash.

### Failure indicators

- DaltonLens comparison above 1 percent, or exact only at severity 1.0.
- A gray pixel changes color after simulation.
- Severity 0 output differs from the input.

### Isolation test

Simulate single colors with no image: pure gray `(128, 128, 128)` must stay gray at every severity, and the sRGB primaries at severity 1.0 must match DaltonLens to within 1 unit per channel. Then check the matrix for severity 0.5 against the mean of the 0.4 and 0.6 matrices.

### Rollback

Delete the files this increment added and return to the state after `03-quality-gates.md`. Set this row to `rolled back`.

### Main rules (repeated)

- Add the unnumbered color rules and shared engine models only. Add no pipeline filter.
- Simulate with Machado (2009) in linear RGB, interpolated by severity. Support protan and deutan only.
- Color Engine imports only NumPy, Pillow, scikit-image, scikit-learn, and the standard library.
