# Tracking

The implementation agent updates this file after each increment: the increment's row in the summary, and in its section the **Status** line, the **Result**, and any **Notes** (changes from the increment file that its verification needed, and risks for later increments).

Status values: ⚪ not started, 🟢 green, 🟡 yellow, 🔴 red, ↩️ rolled back.

## Summary

| #  | Increment                                 | Type     | Status         | Result                                                                             |
| -- | ----------------------------------------- | -------- | -------------- | ---------------------------------------------------------------------------------- |
| 01 | Project skeleton                          | Standard | 🟢 green       | Installs and imports on Python 3.11.18; 46 of 46 folders                           |
| 02 | Docker and dependencies                   | Standard | 🟢 green       | Images build; 9090, 4 CPUs, 8 GB; no FastAPI in engine-test                        |
| 03 | Quality gates                             | Standard | 🟢 green       | 4 contracts kept; test import caught                                               |
| 04 | Color rules                               | CRITICAL | 🟢 green       | DaltonLens 0.18–0.19 %, at most 1 unit off; 34 of 34 Sharma pairs; coverage 98.7 % |
| 05 | Image decode and validation (filter 1)    | Standard | 🟢 green       | All fixtures right; P3 within 2 units                                              |
| 06 | Palette extraction (filter 2)             | Standard | 🟢 green       | Known colors within 2; runs identical; 12 MP in 2.4 s                              |
| 07 | Confusion detection (filter 3)            | Standard | 🟢 green       | Red–green flagged (deutan 7.0, protan 1.2); red–blue not; mask exact               |
| 08 | Targeted enhancement (filter 4)           | CRITICAL | 🟢 green       | 0 pixels changed outside mask; L gap 20.5 deutan, 21.9 protan; no banding          |
| 09 | Separation check (filter 5)               | Standard | 🟢 green       | Both pairs improved (deutan 7.0 → 13.6, protan 1.2 → 8.4); coverage 98.2 %         |
| 10 | Acceptance evaluation                     | CRITICAL | 🟡 yellow      | Held-out set not supplied (test skips); measurement verified on dev images         |
| 11 | Application Core and the upload use case  | CRITICAL | ⚪ not started |                                                                                    |
| 12 | Enhance use case and outcome policy       | Standard | ⚪ not started |                                                                                    |
| 13 | View and export use cases                 | Standard | ⚪ not started |                                                                                    |
| 14 | Session storage and cleanup               | Standard | ⚪ not started |                                                                                    |
| 15 | Server and HTTP API                       | CRITICAL | ⚪ not started |                                                                                    |
| 16 | Page, upload, and status messages         | Standard | ⚪ not started |                                                                                    |
| 17 | Profile, comparison, and download         | Standard | ⚪ not started |                                                                                    |
| 18 | Accessibility, layout, and interface copy | CRITICAL | ⚪ not started |                                                                                    |
| 19 | Processing time                           | Standard | ⚪ not started |                                                                                    |
| 20 | Documentation and diagrams                | Standard | ⚪ not started |                                                                                    |

## Increments

### 01 · Project skeleton

**File:** `01-project-skeleton.md`  
**SRS IDs:** structure, stack, SRS-NFR-005  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | Package install and import |
| Green  | Both packages install with `[test]` extras and import; every tree folder exists |
| Yellow | Packages install but some tree folders are missing |
| Red    | Install or import fails |

**Result:** Installs and imports on Python 3.11.18; 46 of 46 folders

### 02 · Docker and dependencies

**File:** `02-docker-and-dependencies.md`  
**SRS IDs:** stack, SRS-NFR-001  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | `docker compose build` result |
| Green  | Build succeeds; `engine-test` has no FastAPI; `portal` and `dev` have 4 CPUs, 8 GB, and `portal` maps 9090 |
| Yellow | Build succeeds but a limit or port is wrong |
| Red    | Build fails, or `dev/` or `docs/` enters the build context |

**Result:** Images build; 9090, 4 CPUs, 8 GB; no FastAPI in engine-test

**Notes:**

- The `dev` stage installs `libatomic1` before `playwright install`. *Why:* Playwright's bundled Node needs it on arm64 slim images; without it the build exits 127.

### 03 · Quality gates

**File:** `03-quality-gates.md`  
**SRS IDs:** structure, hard constraints  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | Ruff and import-linter results |
| Green  | Ruff passes; four contracts kept; a test outward import is caught |
| Yellow | Checks pass but CI workflow is incomplete |
| Red    | A contract is missing or does not catch the test import |

**Result:** 4 contracts kept; test import caught

**Notes:**

- `src/color_engine/pyproject.toml` also has the `[tool.ruff]` settings. *Why:* Ruff reads only the nearest `pyproject.toml` with `[tool.ruff]`, so engine files would otherwise be linted with defaults.
- In `ci.yml`, lint and dependency-rule steps run before the `engine-test` build. *Why:* `engine-test` fails with "no tests ran" until increment 04; this order keeps the lint and dependency checks reporting meanwhile.

### 04 · Color rules  ⚠ CRITICAL

**File:** `04-color-rules.md`  
**SRS IDs:** SRS-FR-005, SRS-NFR-007  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | Mean per pixel difference from DaltonLens; Sharma pairs |
| Green  | Under 1 percent at every tested severity; Sharma pairs within 0.0001; `engine-test` builds |
| Yellow | Under 2 percent, or exact only at severity 1.0 |
| Red    | 2 percent or more, a Sharma pair fails, or gray changes color |

**Result:** DaltonLens 0.18–0.19 %, at most 1 unit off; 34 of 34 Sharma pairs; coverage 98.7 %

**Notes:**

- The interpolation check compares severity 0.45 with the mean of the 0.4 and 0.5 matrices, and 0.5 with its table entry. *Why:* The increment's isolation test compared 0.5 with the mean of 0.4 and 0.6, but 0.5 is itself a table step, so linear interpolation does not make those equal.
- `encode_png` calls `Image.fromarray(pixels)` without the `"RGB"` mode argument. *Why:* Pillow deprecated the mode argument; a uint8 (H, W, 3) array is read as RGB.

### 05 · Image decode and validation (filter 1)

**File:** `05-image-decode.md`  
**SRS IDs:** SRS-FR-001, SRS-FR-002, SRS-NFR-004, SRS-FR-007  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | Fixture results |
| Green  | Every fixture gives the expected pixels or reason; P3 within 2 units |
| Yellow | One edge fixture (P3 or EXIF) wrong; all rejections right |
| Red    | A renamed, truncated, oversized, or over-12-megapixel file is accepted |

**Result:** All fixtures right; P3 within 2 units

**Notes:**

- `decode_1` does not change `Image.MAX_IMAGE_PIXELS`. It ignores Pillow's `DecompressionBombWarning` while opening and maps `DecompressionBombError` to `TOO_MANY_PIXELS`. *Why:* Setting the module-wide limit would affect every other Pillow caller; the 12-megapixel check runs on the header before `load()` either way.
- Fixtures are committed in `tests/data/samples/` with `make_samples.py`, which builds the Display P3 ICC profile byte by byte. *Why:* Pillow cannot create a P3 profile; committed files let increment 11 reuse the same fixtures. Display P3 `(180, 120, 60)` decodes to sRGB `(190, 117, 45)`, within 2 units of the expected value.
- `lint-imports --config` prints a deprecation warning (import-linter 2.17); the positional form is preferred. *Why:* Still works; the commands in `structure.md` and `ci.yml` are unchanged.

### 06 · Palette extraction (filter 2)

**File:** `06-palette-extraction.md`  
**SRS IDs:** SRS-FR-005  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | CIEDE2000 from known colors |
| Green  | Every known color within 2; runs identical |
| Yellow | Every known color within 5 |
| Red    | A known color missing, or runs differ |

**Result:** Known colors within 2; runs identical; 12 MP in 2.4 s

**Notes:**

- Pixels are assigned through their distinct colors: each pixel's RGB is packed into one integer, `np.unique` finds the distinct colors, and only those are matched to the nearest center in chunks. After assignment, each center is recomputed as the mean CIELAB of its pixels. *Why:* Meets the chunking note while keeping 12 megapixels fast: a noisy 12 megapixel image (about 207,000 distinct colors) takes 2.4 s on 4 CPUs.
- Risk for increment 08: with more clusters than real colors, k-means can split one noisy color into several clusters about 3 CIEDE2000 apart, above the 2.3 merge distance. *Why:* If such near-identical clusters land in one confusable group, lightness separation could push them apart and add visible banding. Check this in increment 08's photo-like test.

### 07 · Confusion detection (filter 3)

**File:** `07-confusion-detection.md`  
**SRS IDs:** SRS-FR-005  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | Flagged pairs on test images |
| Green  | Deutan and protan red–green flagged; red–blue not; threshold 5 vs 10 differs; mask exact |
| Yellow | Flags right, mask off by under 1 percent of pixels |
| Red    | A wrong flag, or the threshold has no effect |

**Result:** Red–green flagged (deutan 7.0, protan 1.2); red–blue not; mask exact. Engine distances at severity 1.0: deutan red–green 71.4 → 7.0, protan red–green 61.7 → 1.2, deutan red–blue 44.0 → 63.8. Engine tests 130, coverage 97.2 %.

### 08 · Targeted enhancement (filter 4)  ⚠ CRITICAL

**File:** `08-targeted-enhancement.md`  
**SRS IDs:** SRS-FR-006, SRS-FR-007  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | Changed pixels outside mask; lightness gap |
| Green  | 0 changed pixels outside the mask; gap at least 20 |
| Yellow | 0 outside the mask; gap 10 to 20 |
| Red    | Any pixel changed outside the mask, or the gap shrinks |

**Result:** 0 pixels changed outside the mask on flat and noisy images. CIELAB lightness gap on the flat graphics: deutan red–green 13.6 → 20.5, protan red–green 10.8 → 21.9. On a noisy image, lightness spread inside each region is unchanged (red 1.1 → 1.0, green 1.6 → 1.6). Noisy 12 megapixel image: filters 2 to 4 take about 6.4 s. Engine tests 141, coverage 98.0 %.

**Notes:**

- Grouped colors closer than the threshold in the original form one tier and share one shift; tiers are spaced 22 apart instead of single colors, and groups that share near-identical colors are joined first. If chaining ever puts both colors of a flagged pair into one tier, that tier falls back to single colors. *Why:* the risk recorded under 06 occurred. Without tiers, k-means sub-clusters of one noisy red were pushed apart and the lightness spread inside the red region rose from 1.1 to 8.0 (green 1.6 to 11.1), which is visible banding.
- Moved pixels are converted through their distinct (color, palette index) combinations, and `palette_lab_after` is the count-weighted mean of those. *Why:* converting every masked pixel took 17.2 s on a noisy 12 megapixel image, most of the 30 s budget; this takes 3.8 s with identical output.

### 09 · Separation check (filter 5)

**File:** `09-separation-check.md`  
**SRS IDs:** SRS-FR-009, SRS-NFR-007  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | Report counts on test images; coverage |
| Green  | Counts as specified; engine coverage at least 70 percent |
| Yellow | Counts right; coverage 60 to 70 percent |
| Red    | A count wrong, or coverage under 60 percent |

**Result:** On the flat graphics each report has `eligible_count == 1`, `improved_count == 1`, and no newly confusable pairs. Simulated distance before → after: deutan red–green 7.0 → 13.6, protan red–green 1.2 → 8.4. Engine tests 148, coverage 98.2 %.

**Notes:**

- Risk for increment 10: "improved" means the simulated distance grew (Decision 2), not that the pair is no longer confusable. The protan test pair improves from 1.2 to 8.4 but stays below the threshold of 10, so re-running detection would still flag it. *Why:* the 80 percent target counts improved pairs, so it can pass while some pairs stay confusable. Report pairs that end above the threshold alongside the improved count.

### 10 · Acceptance evaluation  ⚠ CRITICAL

**File:** `10-acceptance-evaluation.md`  
**SRS IDs:** SRS-NFR-007  
**Status:** 🟡 yellow

| Zone   | Criterion |
| ------ | --------- |
| Metric | Percent of eligible pairs improved, per profile |
| Green  | At least 80 percent for protan and for deutan; results in `docs/acceptance-results.md` |
| Yellow | Held-out set not supplied (test skipped), or 70 to 80 percent |
| Red    | Under 70 percent for a profile, or held-out images were created or altered |

**Result:** Yellow until the team adds the held-out set to `src/color_engine/tests/data/acceptance/`; `labels.json` has the schema and an empty `images` list, and the target test skips with `held-out set not supplied`. The isolation test runs the same measurement on three synthetic graphics in a temporary folder: deutan and protan red–green pairs each 1 of 1 improved, red–blue not eligible, 0 pixels changed outside target regions, 0 newly confusable. Engine tests 149 passed, 1 skipped. To turn this row green, add the images and labels, run `docker compose run --rm dev pytest src/color_engine/tests/acceptance -s`, and record the table in `docs/acceptance-results.md`.

**Notes:**

- The report adds an "Above threshold after" column: improved pairs whose simulated distance after enhancement reaches the threshold. *Why:* the risk recorded under 09. In the isolation test, deutan ends above the threshold (1 of 1) but protan does not (0 of 1), although both count as improved.
- The isolation test always runs, on synthetic images built in `tmp_path`. *Why:* it proves the measurement code before the held-out set exists, without creating or touching held-out images.

### 11 · Application Core and the upload use case  ⚠ CRITICAL

**File:** `11-core-and-upload.md`  
**SRS IDs:** SRS-FR-001, SRS-FR-002, SRS-FR-004, SRS-FR-011, SRS-NFR-004  
**Status:** ⚪ not started

| Zone   | Criterion |
| ------ | --------- |
| Metric | Core tests with fakes; `lint-imports` |
| Green  | All pass; each rejection has its reason and message; replacement works |
| Yellow | Tests pass but a message differs from the increment |
| Red    | Core imports an outer part, or a rejected file is stored |

### 12 · Enhance use case and outcome policy

**File:** `12-enhance-use-case.md`  
**SRS IDs:** SRS-FR-003, SRS-FR-005, SRS-FR-006, SRS-FR-009, SRS-FR-011  
**Status:** ⚪ not started

| Zone   | Criterion |
| ------ | --------- |
| Metric | Outcomes on test images; palette reuse |
| Green  | All three outcomes and messages right; filter 2 runs once across a profile change |
| Yellow | Outcomes right; palette recomputed on profile change |
| Red    | A wrong outcome, or enhanced pixels stored for a non-`ENHANCED` outcome |

### 13 · View and export use cases

**File:** `13-view-and-export.md`  
**SRS IDs:** SRS-FR-004, SRS-FR-008, SRS-FR-010, SRS-FR-007  
**Status:** ⚪ not started

| Zone   | Criterion |
| ------ | --------- |
| Metric | PNG round trip; outside-mask equality |
| Green  | Original and export decode to stored pixels; 0 pixels changed outside mask |
| Yellow | Correct, but a missing-image message differs |
| Red    | Export not PNG, or a pixel changed outside the mask |

### 14 · Session storage and cleanup

**File:** `14-session-storage-and-cleanup.md`  
**SRS IDs:** SRS-NFR-005, SRS-FR-011  
**Status:** ⚪ not started

| Zone   | Criterion |
| ------ | --------- |
| Metric | Files left after end or purge |
| Green  | 0 files left for an ended or idle session; bad IDs rejected |
| Yellow | Files removed, but timing of idle purge off by more than a minute |
| Red    | Any file left, or a path-forming ID accepted |

### 15 · Server and HTTP API  ⚠ CRITICAL

**File:** `15-server-and-api.md`  
**SRS IDs:** SRS-FR-001, SRS-FR-002, SRS-FR-010, SRS-FR-011, SRS-NFR-004, SRS-NFR-005  
**Status:** ⚪ not started

| Zone   | Criterion |
| ------ | --------- |
| Metric | API tests; live upload on port 9090 |
| Green  | Every table row passes; 413 before decode; no folders after restart |
| Yellow | Works on localhost but not tested from another device |
| Red    | `lint-imports` fails, a router holds a rule, or session files survive restart |

### 16 · Page, upload, and status messages

**File:** `16-page-upload-and-status.md`  
**SRS IDs:** SRS-FR-001, SRS-FR-002, SRS-FR-004, SRS-NFR-005, SRS-NFR-003  
**Status:** ⚪ not started

| Zone   | Criterion |
| ------ | --------- |
| Metric | Browser upload results |
| Green  | Valid files show the original; invalid files show `Error:` and reason; tab close clears the session |
| Yellow | Works, but an earlier original disappears on error |
| Red    | Invalid file shows an image, or an error has no text |

### 17 · Profile, comparison, and download

**File:** `17-profile-compare-download.md`  
**SRS IDs:** SRS-FR-003, SRS-FR-008, SRS-FR-009, SRS-FR-010, SRS-FR-011  
**Status:** ⚪ not started

| Zone   | Criterion |
| ------ | --------- |
| Metric | Workflow on test images |
| Green  | Both profiles and limits work; slider compares the same area; PNG download matches; no-pair message shown |
| Yellow | Works, but the download is offered for a non-`ENHANCED` outcome |
| Red    | A profile or limit missing, or the download does not match the display |

### 18 · Accessibility, layout, and interface copy  ⚠ CRITICAL

**File:** `18-accessibility-and-copy.md`  
**SRS IDs:** SRS-NFR-002, SRS-NFR-003, SRS-NFR-006  
**Status:** ⚪ not started

| Zone   | Criterion |
| ------ | --------- |
| Metric | axe violations; keyboard run; scroll width; copy check |
| Green  | 0 axe violations; full keyboard run; no horizontal scroll at 375 and 1280 px; copy check passes |
| Yellow | Only minor axe issues outside contrast and labels |
| Red    | A contrast or label violation, a keyboard trap, or a banned claim |

### 19 · Processing time

**File:** `19-processing-time.md`  
**SRS IDs:** SRS-NFR-001  
**Status:** ⚪ not started

| Zone   | Criterion |
| ------ | --------- |
| Metric | Seconds for a 12 megapixel image on the reference host |
| Green  | Under 30 s; rejection under 2 s |
| Yellow | 30 to 45 s |
| Red    | Over 45 s, or a speed fix changed a result |

### 20 · Documentation and diagrams

**File:** `20-documentation-and-diagrams.md`  
**SRS IDs:** SRS-NFR-006, structure  
**Status:** ⚪ not started

| Zone   | Criterion |
| ------ | --------- |
| Metric | Diagram renders; link check; guide walkthrough |
| Green  | All SVGs regenerate with no diff; all links resolve; walkthrough succeeds |
| Yellow | A link or description is missing |
| Red    | An SVG edited by hand or missing, or the guide makes a medical claim |
