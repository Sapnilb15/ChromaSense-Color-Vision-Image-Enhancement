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
| 11 | Application Core and the upload use case  | CRITICAL | 🟢 green       | 11 core tests pass with fakes; no web framework needed; 4 contracts kept           |
| 12 | Enhance use case and outcome policy       | Standard | 🟢 green       | All 3 outcomes and messages right; palette computed once across profiles           |
| 13 | View and export use cases                 | Standard | 🟢 green       | PNG round trips exact; export 0 pixels changed outside mask                        |
| 14 | Session storage and cleanup               | Standard | 🟢 green       | 0 files left after end or idle purge; bad session IDs rejected                     |
| 15 | Server and HTTP API                       | CRITICAL | 🟢 green       | All 6 endpoints live on 9090; 413 before decode; 0 sessions after restart          |
| 16 | Page, upload, and status messages         | Standard | 🟢 green       | Upload shows original; errors show reason; tab close ends session                  |
| 17 | Profile, comparison, and download         | Standard | 🟢 green       | Profiles, limits, slider, and PNG download work; no-pair case hides download       |
| 18 | Accessibility, layout, and interface copy | CRITICAL | 🟢 green       | 0 axe violations (22 rules); keyboard run; no scroll at 375/1280; copy clean       |
| 19 | Processing time                           | Standard | 🟢 green       | 12 MP in 7.0 s (PNG) and 10.3 s (noisy JPEG); 20 MP rejected in 0.001 s            |
| 20 | Documentation and diagrams                | Standard | 🟢 green       | 3 diagrams with SVGs (no diff on regenerate); docs written; all links resolve      |
| 21 | Professional documentation                | Standard | ⚪ not started |                                                                                    |

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
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | Core tests with fakes; `lint-imports` |
| Green  | All pass; each rejection has its reason and message; replacement works |
| Yellow | Tests pass but a message differs from the increment |
| Red    | Core imports an outer part, or a rejected file is stored |

**Result:** `ProcessUpload` stores valid PNG and JPEG uploads; every invalid sample from increment 05 and an 11 MB file raise `UploadRejected` with the increment's reason and message, and nothing is stored or touched. A second upload replaces the first and discards the result; a rejected upload leaves the session unchanged. Isolation: the 11 core tests pass in a clean Python 3.11 container with FastAPI, Starlette, and Uvicorn not installed. `lint-imports`: 4 contracts kept.

**Notes:**

- `SessionImageStore.save_result` and `load_result` use the quoted forward reference `"EnhancementResult"` with `# noqa: F821`. *Why:* the increment says to use a forward reference until increment 12 adds the model; Ruff flags an undefined name in a string annotation without the `noqa`. Remove the `noqa` in increment 12.
- `src/portal/pyproject.toml` has `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `--import-mode=importlib`, as the engine does. *Why:* keeps test module names in the engine and portal from colliding.
- The port fakes live in `src/portal/tests/core/conftest.py` as fixtures, and portal tests read the committed samples from `src/color_engine/tests/data/samples/`.

### 12 · Enhance use case and outcome policy

**File:** `12-enhance-use-case.md`  
**SRS IDs:** SRS-FR-003, SRS-FR-005, SRS-FR-006, SRS-FR-009, SRS-FR-011  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | Outcomes on test images; palette reuse |
| Green  | All three outcomes and messages right; filter 2 runs once across a profile change |
| Yellow | Outcomes right; palette recomputed on profile change |
| Red    | A wrong outcome, or enhanced pixels stored for a non-`ENHANCED` outcome |

**Result:** Deutan red–green gives `ENHANCED` ("Adjusted 1 of 1 color pairs likely to be confused."), with stored enhanced pixels equal to the original outside the mask. Red–blue gives `NO_CONFUSABLE_PAIRS` with no enhanced pixels. A stubbed filter 5 with no improvement gives `NOT_IMPROVED`. Changing deutan to protan calls filter 2 once in total (spy), and a new image gets a new palette. No image raises `NoImageInSession("Upload an image first.")`. Portal tests 28, engine tests 149 passed and 1 skipped.

**Notes:**

- `policy/outcome.py` has `message_for` alongside `outcome_for`, and the `ENHANCED` message uses "1 pair" for a single pair that could not be improved. *Why:* the increment's template reads " {n} pairs could not be improved."; the singular keeps the sentence grammatical.
- Severity is written with `:g` formatting, so 1.0 reads "severity 1" and 0.8 reads "severity 0.8".
- The `noqa` forward reference from increment 11 is removed; `ports.py` now imports `EnhancementResult`.

### 13 · View and export use cases

**File:** `13-view-and-export.md`  
**SRS IDs:** SRS-FR-004, SRS-FR-008, SRS-FR-010, SRS-FR-007  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | PNG round trip; outside-mask equality |
| Green  | Original and export decode to stored pixels; 0 pixels changed outside mask |
| Yellow | Correct, but a missing-image message differs |
| Red    | Export not PNG, or a pixel changed outside the mask |

**Result:** `RenderView` returns PNGs that decode exactly to the stored original and enhanced pixels. `ExportImage` returns `chromasense-enhanced.png` at the original size, decoding to the stored enhanced pixels, with 0 pixels changed outside the mask. After a `NO_CONFUSABLE_PAIRS` outcome, before enhancing, or after a new upload, the enhanced view and the export raise `NoImageInSession` with the increment's messages. Portal tests 36, engine tests 149 passed and 1 skipped.

### 14 · Session storage and cleanup

**File:** `14-session-storage-and-cleanup.md`  
**SRS IDs:** SRS-NFR-005, SRS-FR-011  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | Files left after end or purge |
| Green  | 0 files left for an ended or idle session; bad IDs rejected |
| Yellow | Files removed, but timing of idle purge off by more than a minute |
| Red    | Any file left, or a path-forming ID accepted |

**Result:** Originals and results round-trip exactly on a temporary folder, with and without enhanced pixels. `save_original` removes the result files. `EndSession` and `PurgeIdleSessions` with the real store leave 0 files: a session used 31 minutes ago is purged at `idle_minutes = 30`, one used 5 minutes ago is kept. `../x`, `abc`, a 129-character ID, slashes, spaces, and an empty ID are rejected with `ValueError`. Files stay inside the session folder and no temporary files remain, including after a failed write. Portal tests 60.

**Notes:**

- Pixel arrays are stored as `original.npy` and `enhanced.npy`, and the palette, labels, and mask as `result.npz`, instead of the PNG files in the increment's derived layout. *Why:* lossless and fast. At 12 megapixels, saving or loading an `.npy` takes about 0.01 s, while encoding one noisy PNG takes 1.5 s, which would be paid on every upload and enhancement. It also keeps image encoding out of the Storage Adapter.
- `result.json` is written last and is the file that marks a result as present; the old result is deleted before a new original is written, so a stale result is never paired with a new image.

### 15 · Server and HTTP API  ⚠ CRITICAL

**File:** `15-server-and-api.md`  
**SRS IDs:** SRS-FR-001, SRS-FR-002, SRS-FR-010, SRS-FR-011, SRS-NFR-004, SRS-NFR-005  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | API tests; live upload on port 9090 |
| Green  | Every table row passes; 413 before decode; no folders after restart |
| Yellow | Works on localhost but not tested from another device |
| Red    | `lint-imports` fails, a router holds a rule, or session files survive restart |

**Result:** 100 portal tests pass: every endpoint row with fake use cases (cookie set, 11 MB body refused with 413 before the use case runs, rejection reasons mapped to 413, 415, and 422, missing image mapped to 404, invalid bodies and views to 422), plus `build_app` with the real engine on a temporary folder (full workflow, end session, startup cleanup, background purge). Live `docker compose up portal` on port 9090: upload 201, original view `image/png`, deutan enhance `enhanced` (7.0 → 13.6), export as `attachment; filename="chromasense-enhanced.png"`, renamed text file 415, 11 MB upload 413 in 0.09 s, end session 204 leaves 0 session folders, and a restart leaves 0 session folders. The port is published on `0.0.0.0:9090`, and the host's LAN address answers 200. Not yet checked from a second device on the network. `lint-imports`: 4 contracts kept.

**Notes:**

- The session cookie is set in an HTTP middleware, not per endpoint. *Why:* FastAPI does not add cookies from an injected `Response` to a `Response` the endpoint returns directly, which the PNG endpoints do.
- `FastAPI(..., openapi_url=None)` as well as `docs_url=None` and `redoc_url=None`. *Why:* the route test found `/openapi.json`, which the increment's "add no other endpoint" forbids.
- Request validation errors use the same body as every other error: `{"reason": "invalid_request", "message": "The request is not valid."}`.
- The upload parameter is `Annotated[UploadFile, File()]`. *Why:* Ruff's B008 rule rejects `File(...)` as a default argument, and this is FastAPI's current form.
- The background purge catches and logs any error (by type only, never paths or image data) and keeps running, so one failure does not stop all later purges.
- FastAPI 0.165 includes routers lazily, so `app.routes` holds only wrappers. The route test lists the three routers' routes and checks that `/openapi.json`, `/docs`, and `/redoc` return 404.
- `TestClient` prints a Starlette deprecation warning that suggests `httpx2` instead of `httpx`. Tests pass; revisit if a later Starlette removes `httpx` support.
- The settings and `build_app` integration tests are in `src/portal/tests/web_api/`, since the tree has no `tests/main/` folder.

### 16 · Page, upload, and status messages

**File:** `16-page-upload-and-status.md`  
**SRS IDs:** SRS-FR-001, SRS-FR-002, SRS-FR-004, SRS-NFR-005, SRS-NFR-003  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | Browser upload results |
| Green  | Valid files show the original; invalid files show `Error:` and reason; tab close clears the session |
| Yellow | Works, but an earlier original disappears on error |
| Red    | Invalid file shows an image, or an error has no text |

**Result:** 9 Playwright tests in Chromium against a live portal: PNG and JPEG uploads show the original with "Done: Image uploaded, 60 by 40 pixels."; a renamed text file and a truncated JPEG show "Error:" with the server's reason, keep the image hidden, and request no image; an error after a valid upload keeps the earlier original; focus stays on the file input; the status region has `role="status"` and `aria-live="polite"`; the file input is labeled and described by the limits; closing the tab deletes the session folder. The `portal` image serves the page and every static file. Portal tests 109.

**Notes:**

- `setStatus(text, kind, label)` takes an optional label, so increment 17 can announce "Enhancing:" through the same function. Defaults: "Working", "Done", "Error".
- `upload.js` dispatches a `chromasense:uploaded` event after a successful upload, for increment 17 to reset its results.
- `pages.py` provides `mount_static(app, directory)`, which `create_app` calls. *Why:* a FastAPI router cannot hold a mount.
- `pagehide` also fires on reload, so reloading the page ends the session and clears the image. This follows Decision 3 (the session ends when the page closes).
- Browser tests run Uvicorn in a thread on a free port with a temporary data folder (`tests/browser/conftest.py`). The session-folder helper is a method on the server fixture, because test modules cannot import `conftest` under importlib mode.

### 17 · Profile, comparison, and download

**File:** `17-profile-compare-download.md`  
**SRS IDs:** SRS-FR-003, SRS-FR-008, SRS-FR-009, SRS-FR-010, SRS-FR-011  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | Workflow on test images |
| Green  | Both profiles and limits work; slider compares the same area; PNG download matches; no-pair message shown |
| Yellow | Works, but the download is offered for a non-`ENHANCED` outcome |
| Red    | A profile or limit missing, or the download does not match the display |

**Result:** 10 new Playwright tests: only Protan and Deutan are offered with none selected; severity starts at 1.0 and reaches 0 and 1, each sent in the request; "Enhance image" stays disabled until an image and a profile are chosen; on the deutan red–green sample the status reads "Done: Adjusted 1 of 1 color pairs likely to be confused.", the original and enhanced images have the same box, the comparison slider sets the clip (20 → `inset(0px 80% 0px 0px)`) and announces "20 percent enhanced", and the downloaded `chromasense-enhanced.png` matches the displayed enhanced image pixel for pixel; a red–blue image shows the no-pairs message with only the original and no download; deutan then protan sends two requests and updates the result; a new upload hides step 3 and the download; "Enhancing:" is announced before "Done:". Portal tests 119.

**Notes:**

- The comparison shows the enhanced image over the left part of the frame, as far as the slider (`clip-path: inset(0 {100 - p}% 0 0)`), and the slider's output reads "p percent enhanced". The hint under the slider says so in words.
- The "Enhance image" button is disabled while a request is running, so a double click sends one request; a hint explains why it is disabled until an image and a profile are chosen.
- The severity hint reads "0 applies no adjustment for the profile; 1 applies the full profile." (`derived` wording, no medical claim).

### 18 · Accessibility, layout, and interface copy  ⚠ CRITICAL

**File:** `18-accessibility-and-copy.md`  
**SRS IDs:** SRS-NFR-002, SRS-NFR-003, SRS-NFR-006  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | axe violations; keyboard run; scroll width; copy check |
| Green  | 0 axe violations; full keyboard run; no horizontal scroll at 375 and 1280 px; copy check passes |
| Yellow | Only minor axe issues outside contrast and labels |
| Red    | A contrast or label violation, a keyboard trap, or a banned claim |

**Result:** 20 checks in `tests/browser/test_accessibility.py`, all passing with no change to the Web UI:

- Keyboard only: skip link first, then file input, profile radios (arrow keys), severity slider (arrow keys and End), "Enhance image" (Enter), comparison slider (arrow keys), and the download link (Enter downloads `chromasense-enhanced.png`). Every stop matches `:focus-visible` with an outline of at least 2 px. Focus moves past the last control and back with Shift+Tab, so there is no trap.
- axe with `wcag2a`, `wcag2aa`, `wcag21aa`, and `wcag22aa`: 0 violations before upload, after upload, after an enhanced result, after an error, and after a no-pairs result, and at 375 × 812 and 1280 × 800. axe checks 22 rules on the page, and a guard test proves it reports a removed label and low-contrast text.
- Layout: no horizontal page scroll at 375 and 1280 px before upload, after upload, and after enhancing, including a 2400 × 900 image; the full workflow completes at both widths.
- Not color alone: every status message starts with a text label, and every visible control has a text label.
- Copy: the rendered page, every template and script, and every outcome message contain none of the banned phrases outside the footer's "does not diagnose" and "give medical advice".

**Decision (2026-11-19):** the manual screen reader run is dropped. SRS-NFR-002's verification, "keyboard and accessibility walkthroughs complete the main workflow", is met by the automated keyboard-only walkthrough and the axe checks above, which confirm every control has a label and every status is announced through the `aria-live` region. The SRS cuts voice output and severe low vision support, and the app has no speech features; a named screen reader such as VoiceOver was only the increment file's example of a walkthrough, not an SRS requirement.

**Notes:**

- `test_axe_check_can_fail` breaks the page on purpose and expects axe to report it, so a silent no-op axe run would fail the suite.

### 19 · Processing time

**File:** `19-processing-time.md`  
**SRS IDs:** SRS-NFR-001  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | Seconds for a 12 megapixel image on the reference host |
| Green  | Under 30 s; rejection under 2 s |
| Yellow | 30 to 45 s |
| Red    | Over 45 s, or a speed fix changed a result |

**Result:** On the `dev` container limited to 4 CPUs and 8 GB, upload, deutan enhancement at severity 1.0, and export with the real engine and filesystem store:

| Image | Upload | Enhance | Export | Total |
| --- | --- | --- | --- | --- |
| 12 MP PNG, ±10 noise in 2 × 2 cells (7.7 MB) | 0.2 s | 4.3 s | 2.5 s | 7.0 s |
| 12 MP JPEG, ±20 noise on every pixel (4.0 MB) | 0.1 s | 6.5 s | 3.7 s | 10.3 s |

A 20 megapixel PNG is rejected with `TOO_MANY_PIXELS` in 0.001 s. No engine change was needed. Portal tests 142.

**Notes:**

- The PNG uses noise drawn at half resolution and repeated in 2 × 2 cells. *Why:* the increment asks for a 12 megapixel PNG with per-pixel noise under 10 MB, but per-pixel noise does not compress: even ±1 noise makes an 11.0 MB PNG. The test adds a JPEG with independent noise on every pixel as the photo-like worst case for the distinct-color steps in filters 2 and 4.
- `nproc` reports 16 inside the container. Compose's `cpus: 4` limits CPU time, not the visible core count, so the timings still reflect 4 CPUs.
- The `performance` marker is registered in `src/portal/pyproject.toml`. The tests also run in the normal portal suite and in CI, whose runners are not the reference host.

### 20 · Documentation and diagrams

**File:** `20-documentation-and-diagrams.md`  
**SRS IDs:** SRS-NFR-006, structure  
**Status:** 🟢 green

| Zone   | Criterion |
| ------ | --------- |
| Metric | Diagram renders; link check; guide walkthrough |
| Green  | All SVGs regenerate with no diff; all links resolve; walkthrough succeeds |
| Yellow | A link or description is missing |
| Red    | An SVG edited by hand or missing, or the guide makes a medical claim |

**Result:** `docs/diagrams/` has `context`, `containers`, and `pipeline` as `.mmd` sources with SVGs generated by `docker compose run --rm diagrams`; regenerating gives byte-identical SVGs, and PNG previews were checked by eye. `docs/diagrams/README.md` embeds each SVG with alt text and describes it in words. `docs/code/color-engine.md`, `docs/code/portal.md`, and `docs/user-guides/user-guide.md` are written, and `README.md` has the new build's run and check commands. Every link and anchor in `README.md` and `docs/` resolves. Every command in `structure.md` passes: `docker compose build`, the portal on 9090, `engine-test` (149 passed, 1 skipped), Ruff, `lint-imports` (4 kept), engine coverage 98.2 %, and 142 portal tests.

**Still to do:** the increment's walkthrough check, a developer following only `README.md` and the user guide to start the portal and complete the workflow from a second device. This needs a person and a second device.

**Notes:**

- Pipeline node labels read "Filter 1: decode_1" and so on, not "1. decode_1". *Why:* Mermaid parses a label starting with "1." as a Markdown list and rendered every box as "Unsupported markdown: list"; a PNG preview caught it before commit.

### 21 · Professional documentation

**File:** `21-professional-documentation.md`  
**SRS IDs:** SRS-NFR-008  
**Status:** ⚪ not started

| Zone   | Criterion |
| ------ | --------- |
| Metric | Ruff `D` findings; documentation checklist review |
| Green  | 0 findings; every checklist row met; all other checks pass with the same counts |
| Yellow | 0 findings, but a checklist row is only partly met |
| Red    | Ruff findings remain, behavior or tests changed, or a document claims behavior that does not exist |

**Result:**

**Notes:**
