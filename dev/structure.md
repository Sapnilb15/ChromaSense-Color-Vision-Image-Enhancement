# Structure

You fill this file in stage 3 (see `README.md`). Do not add a part here.

## Required: Directory tree

The tree that the finished project must match. Include the files that the build tool needs.

Folders that already exist and are not listed here stay as they are. Numbered names follow the naming rule in `architecture.md`: only pipeline filters are numbered.

```
ChromaSense-Color-Vision-Image-Enhancement/
├── .devcontainer/
│   └── devcontainer.json
├── .github/
│   └── workflows/
│       └── ci.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── Dockerfile
├── README.md
├── TEAM_ROLES.md
├── docker-compose.yml
├── dev/                          (existing)
├── docs/
│   ├── ChromaSense_SRS.docx
│   ├── acceptance-results.md
│   ├── enhancement-evaluation-v0.5.md
│   ├── code/
│   │   ├── color-engine.md
│   │   └── portal.md
│   ├── diagrams/
│   │   ├── README.md
│   │   ├── context.mmd
│   │   ├── context.svg
│   │   ├── containers.mmd
│   │   ├── containers.svg
│   │   ├── pipeline.mmd
│   │   └── pipeline.svg
│   └── user-guides/
│       └── user-guide.md
└── src/
    ├── color_engine/
    │   ├── pyproject.toml
    │   ├── color_engine/
    │   │   ├── __init__.py
    │   │   ├── models.py
    │   │   ├── data/
    │   │   │   └── machado_2009.json
    │   │   ├── rules/
    │   │   │   ├── __init__.py
    │   │   │   ├── color_spaces.py
    │   │   │   ├── distance.py
    │   │   │   ├── encode.py
    │   │   │   └── simulation.py
    │   │   └── pipeline/
    │   │       ├── __init__.py
    │   │       ├── filter_1_decode/
    │   │       │   ├── __init__.py
    │   │       │   └── decode_1.py
    │   │       ├── filter_2_palette/
    │   │       │   ├── __init__.py
    │   │       │   └── extract_palette_2.py
    │   │       ├── filter_3_confusion/
    │   │       │   ├── __init__.py
    │   │       │   └── detect_confusion_3.py
    │   │       ├── filter_4_enhance/
    │   │       │   ├── __init__.py
    │   │       │   └── enhance_4.py
    │   │       └── filter_5_separation/
    │   │           ├── __init__.py
    │   │           └── check_separation_5.py
    │   └── tests/
    │       ├── data/
    │       │   ├── samples/
    │       │   └── acceptance/
    │       │       └── labels.json
    │       ├── rules/
    │       │   ├── test_color_spaces.py
    │       │   ├── test_distance.py
    │       │   ├── test_encode.py
    │       │   └── test_simulation.py
    │       ├── pipeline/
    │       │   ├── test_filter_1_decode.py
    │       │   ├── test_filter_2_palette.py
    │       │   ├── test_filter_3_confusion.py
    │       │   ├── test_filter_4_enhance.py
    │       │   └── test_filter_5_separation.py
    │       └── acceptance/
    │           └── test_separation_target.py
    └── portal/
        ├── pyproject.toml
        ├── chromasense/
        │   ├── __init__.py
        │   ├── core/
        │   │   ├── __init__.py
        │   │   ├── errors.py
        │   │   ├── models.py
        │   │   ├── ports.py
        │   │   ├── policy/
        │   │   │   ├── __init__.py
        │   │   │   └── outcome.py
        │   │   └── use_cases/
        │   │       ├── __init__.py
        │   │       ├── end_session.py
        │   │       ├── enhance_image.py
        │   │       ├── export_image.py
        │   │       ├── process_upload.py
        │   │       ├── purge_idle_sessions.py
        │   │       └── render_view.py
        │   ├── storage/
        │   │   ├── __init__.py
        │   │   └── filesystem_session_image_store.py
        │   ├── web_api/
        │   │   ├── __init__.py
        │   │   ├── app.py
        │   │   ├── schemas.py
        │   │   ├── session_cookie.py
        │   │   └── routers/
        │   │       ├── __init__.py
        │   │       ├── images.py
        │   │       ├── pages.py
        │   │       └── session.py
        │   ├── web_ui/
        │   │   ├── templates/
        │   │   │   ├── base.html
        │   │   │   └── index.html
        │   │   └── static/
        │   │       ├── css/
        │   │       │   └── app.css
        │   │       └── js/
        │   │           ├── compare.js
        │   │           ├── profile.js
        │   │           ├── session.js
        │   │           ├── status.js
        │   │           └── upload.js
        │   └── main/
        │       ├── __init__.py
        │       ├── __main__.py
        │       ├── settings.py
        │       └── wiring.py
        └── tests/
            ├── core/
            ├── storage/
            ├── web_api/
            ├── browser/
            │   └── intents/
            │       ├── catalog.py
            │       ├── oracles.py
            │       └── test_intents.py
            └── performance/
                └── test_processing_time.py
```

## Required: Ownership

One row for each top-level folder or important file. The part must be a name from `architecture.md`.

| Path | Architecture part | What it holds |
| --- | --- | --- |
| `.devcontainer/` | Server Main | Team dev container, using the `dev` target |
| `.github/workflows/ci.yml` | Server Main | Pull request checks: lint, format, dependency rules, engine tests without FastAPI, portal tests, and the intent suite |
| `.dockerignore` | Server Main | Keeps `dev/`, `docs/`, and `.git/` out of the build context |
| `.env.example` | Server Main | Configuration names with defaults and no secrets: data folder, confusion threshold (10), palette color count, and idle session minutes (30) |
| `.gitignore` | Server Main | Ignores `.env`, caches, coverage output, Playwright `test-results/`, and local session data |
| `Dockerfile` | Server Main | Multi-stage build with `engine-test`, `dev`, and `runtime` targets on Python 3.11; the `dev` target installs the Chromium, Firefox, and WebKit browsers for Playwright |
| `docker-compose.yml` | Server Main | `portal` service on port 9090 with 4 CPUs and 8 GB, `dev` service for checks, `diagrams` service that renders `docs/diagrams/*.mmd` to SVG, and the session data volume |
| `CHANGELOG.md` | Server Main | Changes between releases, starting with 1.0 against 0.5 |
| `README.md` | Server Main | What the app does, how to start it, and how to reach it from another device on the local network |
| `docs/ChromaSense_SRS.docx` | Server Main | The source SRS. Do not edit |
| `docs/enhancement-evaluation-v0.5.md` | Color Engine | The release 0.5 comparison of enhancement methods that Decision 2 relies on. Do not edit |
| `docs/acceptance-results.md` | Color Engine | Improved and eligible pair counts by profile and image type, newly confusable pairs, changes outside target regions, and the threshold and severity used |
| `docs/code/` | Color Engine, Application Core | Developer notes for each Python package: public functions, filter order, and how to run its tests |
| `docs/diagrams/*.mmd` | Server Main | Mermaid sources for the context, container, and pipeline diagrams, kept in step with `dev/architecture.md` |
| `docs/diagrams/*.svg` | Server Main | SVG renders of each `.mmd` file, generated by the `diagrams` service. Do not edit them by hand |
| `docs/diagrams/README.md` | Server Main | Lists each diagram with its SVG embedded and a text description of what it shows, and the command that regenerates the SVGs |
| `docs/user-guides/user-guide.md` | Web UI | Step-by-step guide to upload, profile, compare, and download, with the limits and the no-diagnosis statement |
| `src/color_engine/pyproject.toml` | Color Engine | Package definition with no web framework dependency, package data, coverage settings, and Ruff settings, including the pydocstyle `D` rules with the Google convention |
| `src/color_engine/color_engine/models.py` | Color Engine | `CvdType`, `CvdProfile`, `InputLimits`, `DecodeError` with its reason, and the numbered filter output classes |
| `src/color_engine/color_engine/data/machado_2009.json` | Color Engine | Machado (2009) protan and deutan matrices at severity steps of 0.1 |
| `src/color_engine/color_engine/rules/` | Color Engine | Unnumbered color rules: color spaces, CIEDE2000, simulation, and PNG encoding |
| `src/color_engine/color_engine/pipeline/` | Color Engine | The five numbered filters, one directory each |
| `src/color_engine/tests/data/samples/` | Color Engine | Small fixtures: valid PNG and JPEG, a truncated JPEG, a text file renamed as PNG, an over-12-megapixel PNG header, a Display P3 JPEG, an EXIF-rotated JPEG, and red–green flat graphics |
| `src/color_engine/tests/data/acceptance/` | Color Engine | Held-out PNG and JPEG photos, charts, and maps, set aside before tuning, with target regions and reference colors in `labels.json` |
| `src/color_engine/tests/acceptance/test_separation_target.py` | Color Engine | Runs filters 2 to 5 on the held-out set and fails if fewer than 80 percent of eligible pairs improve for either profile |
| `src/color_engine/tests/` | Color Engine | All other engine tests, which run without the portal or FastAPI |
| `src/portal/pyproject.toml` | Server Main | Portal dependencies, the import-linter contracts, and Ruff settings, including the pydocstyle `D` rules with the Google convention |
| `src/portal/chromasense/core/ports.py` | Application Core | `SessionImageStore` and `Clock` protocols |
| `src/portal/chromasense/core/models.py` | Application Core | `SessionImage`, `EnhancementResult`, `PairOutcome`, `Outcome`, `UploadRejection`, and `ProcessingSettings` |
| `src/portal/chromasense/core/errors.py` | Application Core | `UploadRejected` and `NoImageInSession`, each carrying a user-facing reason |
| `src/portal/chromasense/core/policy/outcome.py` | Application Core | `outcome_for`, which turns a separation report into an outcome and its message |
| `src/portal/chromasense/core/use_cases/` | Application Core | One file for each use case; `enhance_image.py` sets the filter order |
| `src/portal/chromasense/storage/` | Storage Adapter | `FilesystemSessionImageStore`, with one folder for each session |
| `src/portal/chromasense/web_api/` | Web API | App factory, routers, Pydantic schemas, and the session cookie |
| `src/portal/chromasense/web_ui/` | Web UI | Jinja2 templates, CSS, and browser scripts |
| `src/portal/chromasense/main/` | Server Main | Settings, wiring, startup cleanup, the idle purge task, and the entry point |
| `src/portal/tests/core/` | Application Core | Use case and policy tests with fakes for every port |
| `src/portal/tests/storage/` | Storage Adapter | Store tests on a temporary folder, including session deletion and idle purge |
| `src/portal/tests/web_api/` | Web API | Endpoint tests with fake use cases, including the upload size cap and error reasons |
| `src/portal/tests/browser/` | Web UI | Playwright and axe tests: the full workflow by keyboard, desktop and phone viewports, contrast, and text status messages |
| `src/portal/tests/browser/intents/catalog.py` | Web UI | The intent catalog as plain dataclasses: each intent's goal in plain words, its steps (accessible role and name, action, expected status text), and its SRS IDs |
| `src/portal/tests/browser/intents/oracles.py` | Web UI | Usability checks run after every step: found once, visible, inside the viewport, not covered, large enough to press, enabled, images loaded, status updated, focus kept, no console errors or failed requests, no horizontal scroll |
| `src/portal/tests/browser/intents/test_intents.py` | Web UI | Runs each intent by pointer and by keyboard at 375 × 812 and 1280 × 800 in Chromium, Firefox, and WebKit, and saves a screenshot and trace on failure |
| `src/portal/tests/performance/` | Application Core | Timing of upload plus enhancement on a 12 megapixel image in the reference container |

## Optional: Libraries and functions

Use these where a requirement or decision already depends on them. The agent must not swap them for an equivalent without a recorded decision.

### Color Engine

| Library | Use these | In | SRS IDs |
| --- | --- | --- | --- |
| `Pillow` | `PIL.Image.open(io.BytesIO(data), formats=["PNG", "JPEG"])`, then check `width * height` against the megapixel limit before `Image.load()` | `filter_1_decode` | SRS-FR-001, SRS-FR-002, SRS-NFR-004 |
| `Pillow` | `PIL.ImageOps.exif_transpose`, `PIL.ImageCms.profileToProfile`, `PIL.ImageCms.createProfile("sRGB")` | `filter_1_decode` | SRS-FR-007 |
| `scikit-learn` | `sklearn.cluster.KMeans` with a fixed `random_state`, on a pixel sample | `filter_2_palette` | SRS-FR-005, SRS-NFR-001 |
| `scikit-image` | `skimage.color.rgb2lab`, `skimage.color.lab2rgb` | `filter_2_palette`, `filter_4_enhance`, `rules/color_spaces.py` | SRS-FR-005, SRS-FR-006 |
| `scikit-image` | `skimage.color.deltaE_ciede2000` | `rules/distance.py` | SRS-FR-005, SRS-NFR-007 |
| `numpy` | Array math, boolean masks, and matrix multiplication | Filters and `rules/` | SRS-FR-006, SRS-FR-007 |
| `Pillow` | `Image.fromarray(...).save(buffer, format="PNG")` | `rules/encode.py` | SRS-FR-010 |
| Standard library | `importlib.resources`, `json` | `rules/simulation.py` | SRS-FR-005 |

### Portal

| Library | Use these | In | SRS IDs |
| --- | --- | --- | --- |
| Standard library | `dataclasses.dataclass`, `typing.Protocol`, `enum.Enum` | `core/` | SRS-FR-009 |
| Standard library | `pathlib.Path`, `shutil.rmtree`, `os.utime` for last-used time | `storage/filesystem_session_image_store.py` | SRS-NFR-005 |
| `fastapi` | `FastAPI` with `lifespan`, `APIRouter`, `UploadFile`, `Depends`, `Response.set_cookie` | `web_api/`, `main/wiring.py` | SRS-FR-001, SRS-FR-011 |
| `fastapi` | `UploadFile.read(max_bytes + 1)` to cap the body before decoding | `web_api/routers/images.py` | SRS-NFR-004 |
| `fastapi` | `fastapi.staticfiles.StaticFiles`, `fastapi.templating.Jinja2Templates` | `web_api/routers/pages.py` | SRS-NFR-002 |
| `python-multipart` | Required by `UploadFile` | `web_api/routers/images.py` | SRS-FR-001 |
| Standard library | `secrets.token_urlsafe` for the anonymous session ID | `web_api/session_cookie.py` | SRS-NFR-005 |
| Standard library | `asyncio.create_task` and `asyncio.sleep(60)` for the idle purge loop | `main/wiring.py` | SRS-NFR-005 |
| `uvicorn` | `uvicorn.run(app, host="0.0.0.0", port=9090)` | `main/__main__.py` | SRS-NFR-001 |
| Standard library | `os.environ` | `main/settings.py` only | SRS-NFR-005 |

### Web UI browser APIs

| API | Use these | In | SRS IDs |
| --- | --- | --- | --- |
| HTML | `<input type="file" accept="image/png,image/jpeg">` | `index.html`, `upload.js` | SRS-FR-001 |
| HTML | `<input type="range" min="0" max="1" step="0.05">` for severity and for the comparison slider, each with a visible label and value | `index.html`, `profile.js`, `compare.js` | SRS-FR-003, SRS-FR-008, SRS-NFR-002 |
| Fetch | `fetch` with `FormData` | `upload.js`, `profile.js` | SRS-FR-001, SRS-FR-011 |
| DOM | One shared `aria-live="polite"` status region with text for every state | `status.js` | SRS-FR-002, SRS-FR-009, SRS-NFR-003 |
| HTML | `<a download="chromasense-enhanced.png">` | `index.html` | SRS-FR-010 |
| Beacon | `navigator.sendBeacon("/api/session/end")` on `pagehide` | `session.js` | SRS-NFR-005 |
| CSS | `:focus-visible`, and media queries for phone and desktop widths | `app.css` | SRS-NFR-002, SRS-NFR-003 |

### Development and tests

| Library | Use these | SRS IDs |
| --- | --- | --- |
| `pytest`, `pytest-cov` | Test runs and the coverage report for `color_engine` | SRS-NFR-007 |
| `daltonlens` | `daltonlens.simulate.Simulator_Machado2009` as a test-only reference | SRS-NFR-007 |
| `ruff` | `ruff check` (including the pydocstyle `D` rules) and `ruff format --check` | SRS-NFR-008 |
| `import-linter` | `lint-imports` | none |
| `playwright`, `axe-playwright-python` | Browser, viewport, keyboard, and accessibility tests | SRS-NFR-002, SRS-NFR-003 |
| `playwright` | `get_by_role`, `get_by_label`, `get_by_text`, `page.expect_file_chooser`, `page.expect_download`, `page.on("console")`, `page.on("requestfailed")`, `document.elementFromPoint`, and `context.tracing` for the intent suite | SRS-FR-012 |
| `minlag/mermaid-cli:11.4.2` image | `mmdc -i <name>.mmd -o <name>.svg` for each diagram, run by the `diagrams` compose service. It is a documentation tool and is not part of any image target | none |

## Required: Build and run

The commands to run after the last increment. The first command must succeed.

1. `docker compose build`
2. `docker compose up portal`, then open `http://localhost:9090`, or `http://<host-ip>:9090` from another device on the local network
3. Extra checks:
   - `docker build --target engine-test .` (runs the Color Engine tests with no web framework installed)
   - `docker compose run --rm dev ruff check .`
   - `docker compose run --rm dev ruff format --check .`
   - `docker compose run --rm dev lint-imports --config src/portal/pyproject.toml`
   - `docker compose run --rm dev pytest src/color_engine/tests --cov=color_engine --cov-fail-under=70`
   - `docker compose run --rm dev pytest src/portal/tests`
   - `docker compose run --rm dev pytest src/portal/tests/browser/intents` (the intent suite; run it before every user-testing session)
   - `docker compose run --rm diagrams` (regenerates every SVG in `docs/diagrams/`; `git diff --exit-code docs/diagrams` then shows no change if the SVGs were current)

## Required: If the build fails

Checks for this stack. The implementation agent uses this list before it invents a fix.

1. Docker: confirm that the Docker daemon is running, that the base image is Python 3.11, and that the `Dockerfile` target names match `docker-compose.yml`.
2. Build context: confirm that `.dockerignore` excludes `dev/` and `docs/`. Release 0.5 code is reached only through the `v0.5` git tag. Do not add a copy of it to the working tree.
3. Install order: confirm that the image installs `src/color_engine` before `src/portal`, and that `src/color_engine/pyproject.toml` lists `data/*` as package data.
4. Imports: if `lint-imports` fails, fix the import that points outward. Do not edit the contract. Numbered directories must keep the `filter_<N>_<name>` form, because names such as `1-decode` cannot be imported.
5. Decode: if a truncated JPEG decodes without error, confirm that `PIL.ImageFile.LOAD_TRUNCATED_IMAGES` is `False` and that `Image.load()` runs inside `decode_1`. If a large image is slow to reject, check the pixel count before `Image.load()`.
6. Port: if the portal does not open, confirm that port 9090 is free, that the server binds `0.0.0.0`, and that the host firewall allows it.
7. Line endings: if a file copied into the image fails with a bad interpreter or `\r` error, convert that file to LF.
8. Diagrams: if `docker compose run --rm diagrams` fails, confirm that the image tag is pinned, that `docs/diagrams` is mounted at `/data`, and that each `.mmd` file renders on its own with `mmdc -i`. A diagram failure must not block the portal build.
9. Intent suite: if a browser fails to launch, confirm that the `dev` image ran `playwright install --with-deps chromium firefox webkit`. If an intent fails, open its trace with `playwright show-trace test-results/<intent>/trace.zip` and fix the Web UI, not the intent or its checks.
