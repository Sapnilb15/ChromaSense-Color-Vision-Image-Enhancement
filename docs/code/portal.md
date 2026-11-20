# Portal

`src/portal/` is the `chromasense` package: the web portal around the Color Engine. Its parts follow [`dev/architecture.md`](../../dev/architecture.md), and import rules keep dependencies pointing inward (checked by `lint-imports`).

| Part | Folder | Job |
| --- | --- | --- |
| Web UI | `chromasense/web_ui/` | One server-rendered page with plain JavaScript. Does no pixel work. |
| Web API | `chromasense/web_api/` | HTTP routes, the session cookie, the 10 MB body cap, and error mapping. No business rules. |
| Application Core | `chromasense/core/` | Use cases, models, ports, and the outcome policy. Imports no web or filesystem code. |
| Storage Adapter | `chromasense/storage/` | One folder per session on disk. |
| Server Main | `chromasense/main/` | Settings, wiring, startup cleanup, the idle purge, and the entry point. |

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

## Tests

From the repository root:

```bash
docker compose run --rm dev pytest src/portal/tests                 # everything
docker compose run --rm dev pytest src/portal/tests/core            # use cases, with fakes
docker compose run --rm dev pytest src/portal/tests/browser         # Playwright and axe in Chromium
docker compose run --rm dev pytest src/portal/tests/performance -s  # timing on 4 CPUs and 8 GB
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

The core tests use the fakes in `tests/core/conftest.py`. The browser tests start a live portal on a free port with a temporary data folder. The accessibility tests check keyboard use, axe (WCAG 2.2 AA) in every page state, phone and desktop widths, and interface wording.
