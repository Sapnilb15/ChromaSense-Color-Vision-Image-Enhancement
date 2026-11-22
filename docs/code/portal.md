# Portal

**Who this is for:** developers who change or test the web portal. It is a reference for the parts, use cases, HTTP API, session lifecycle, settings, and tests.

`src/portal/` is the `chromasense` package: the web portal around the Color Engine. Its parts follow [`dev/architecture.md`](../../dev/architecture.md), and import rules keep dependencies pointing inward (checked by `lint-imports`).

| Part | Folder | Job |
| --- | --- | --- |
| Web UI | `chromasense/web_ui/` | One server-rendered page with plain JavaScript. Does no pixel work. |
| Web API | `chromasense/web_api/` | HTTP routes, the session cookie, the 10 MB body cap, and error mapping. No business rules. |
| Application Core | `chromasense/core/` | Use cases, models, ports, and the outcome policy. Imports no web or filesystem code. |
| Storage Adapter | `chromasense/storage/` | One folder per session on disk. |
| Server Main | `chromasense/main/` | Settings, wiring, startup cleanup, the idle purge, and the entry point. |

## Browser workspace

Jinja renders the workspace and native help dialogs. Local CSS tokens define the dark and light themes. Only the theme preference is saved in browser storage. The file picker and drop target share one multipart upload path. The controller serializes uploads, enhancement requests, and exports for the page, converts percentage severity to the API range, and waits for previews to decode. The comparison module displays server-rendered PNGs using a draggable clip or two complete views. The export uses the filename from Content-Disposition.

## Use cases

Each is a class with `execute(request) -> response` in `core/use_cases/`.

| Use case | What it does |
| --- | --- |
| `ProcessUpload` | Decodes the upload with filter 1 and stores it as the session's original, replacing any earlier image and result. Rejections carry a reason and a message. |
| `EnhanceImage` | Runs filters 2 to 5 on the stored original for a profile, reusing the palette when only the profile changes, and stores the result. |
| `RenderView` | Returns the original or enhanced image as PNG bytes. |
| `ExportImage` | Returns the enhanced image as `chromasense-enhanced.png`. |
| `EndSession` | Deletes a session. |
| `PurgeIdleSessions` | Deletes every session idle longer than the configured minutes. |

The outcome policy (`core/policy/outcome.py`) turns filter 5's report into `ENHANCED`, `NO_CONFUSABLE_PAIRS`, or `NOT_IMPROVED`, with the message the user reads. Enhanced pixels are stored only for `ENHANCED`.

## HTTP API

| Method and path | Success | Errors |
| --- | --- | --- |
| `GET /` | the page | none |
| `POST /api/image` (multipart field `file`) | 201 `{"width", "height"}` | 413 `too_large`, 415 `unsupported_type`, 422 `corrupt` or `too_many_pixels` |
| `POST /api/image/enhance` (JSON `{"type": "protan" or "deutan", "severity": 0 to 1}`) | 200 `{"outcome", "message", "eligible_count", "improved_count", "pairs"}` | 404 no image, 422 invalid body |
| `GET /api/image/view/{original or enhanced}` | 200 `image/png`, not cached | 404 |
| `GET /api/image/export` | 200 `image/png` attachment named `chromasense-enhanced.png` | 404 |
| `POST /api/session/end` | 204 | none |

Every error body is `{"reason": "...", "message": "..."}`. Static files are served from `/static`. There are no other routes, including no generated API documentation.

## Sessions

A session is an anonymous ID in the `chromasense_session` cookie (HTTP only, `SameSite=Lax`). It ends at the first of these:

- the page closes and sends `POST /api/session/end` with `navigator.sendBeacon` (this also happens on reload)
- the session is idle for the configured minutes; Server Main purges idle sessions every 60 seconds
- the server restarts; Server Main deletes every session folder at startup

Ending a session deletes its folder, `{data dir}/sessions/{session ID}/`, which holds the original and enhanced pixels (`.npy`), the result, and a `last_used` marker. A new upload replaces the session's previous image and result.

## Settings

Server Main reads these environment variables (`chromasense/main/settings.py` is the only module that reads the environment). Invalid values stop startup.

| Variable | Default | Meaning |
| --- | --- | --- |
| `CHROMASENSE_DATA_DIR` | `/data` | Where session folders are stored |
| `CHROMASENSE_CONFUSION_THRESHOLD` | `10` | CIEDE2000 threshold for a confusable pair |
| `CHROMASENSE_PALETTE_COLORS` | `12` | Maximum palette colors |
| `CHROMASENSE_IDLE_MINUTES` | `30` | Minutes before an idle session is deleted |

## Code documentation

Every public module, class, and function has a [PEP 257](https://peps.python.org/pep-0257/) docstring in Google style. Each use case `execute` also documents `Args`, `Returns`, and `Raises`. Ruff's pydocstyle rules check this, and tests are exempt:

```bash
docker compose run --rm dev ruff check .
```

## Tests

From the repository root:

```bash
docker compose run --rm dev pytest src/portal/tests                 # everything
docker compose run --rm dev pytest src/portal/tests/core            # use cases, with fakes
docker compose run --rm dev pytest src/portal/tests/browser         # Playwright and axe, and the intent suite
docker compose run --rm dev pytest src/portal/tests/browser/intents # intent suite only: run before user testing
docker compose run --rm dev pytest src/portal/tests/performance -s  # timing on 4 CPUs and 8 GB
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

The core tests use the fakes in `tests/core/conftest.py`. The browser tests start a live portal on a free port with a temporary data folder. The accessibility tests check keyboard use, axe (WCAG 2.2 AA) in every page state, phone and desktop widths, and interface wording.

### Intent suite (SRS-FR-012)

Run the intent suite before every user-testing session. It answers one question: can a person actually complete each task on the page?

- `tests/browser/intents/catalog.py` lists each intent: a goal in plain words, such as "Enhance a photo and download it", and its steps. Steps name controls only by accessible role and name or by label, never by ID or CSS selector.
- `tests/browser/intents/test_intents.py` runs every intent by pointer and by keyboard, at 375 × 812 and 1280 × 800, in Chromium, Firefox, and WebKit (96 runs, about 5 minutes). It opens the file chooser from the visible control, drags sliders with the mouse or moves them with the arrow keys, and checks that the downloaded PNG matches the enhanced picture on screen.
- `tests/browser/intents/oracles.py` runs after every step. It checks that the control is found once, visible, not covered, at least 24 × 24 pixels, and enabled. It also checks that the status region answered within 2 seconds and ended with the expected text within 30, that every shown picture loaded, that keyboard focus was kept, that the console and network show no errors, and that the page does not scroll sideways.

A failure reads like this:

> Intent "Enhance a photo and download it", step 6 "Download the enhanced picture from near the comparison": the link "Download enhanced PNG" is 1078 pixels below "Step 3: Compare", more than one screen (800 pixels) of scrolling (pointer, 1280 × 800, chromium)

Each failed run saves `test-results/<intent>-<mode>-<viewport>-<browser>/screenshot.png` and `trace.zip`. Open the trace with `playwright show-trace <path>/trace.zip` to step through what happened.

When an intent fails, fix the Web UI. Do not weaken a check. When user testing finds a new UI problem, add an intent that fails on the current code before fixing it. In Firefox only, if the file chooser does not open after the checks have passed, the runner sets the file directly and logs a `UserWarning`. This works around a Playwright–Firefox quirk that a person does not meet.
