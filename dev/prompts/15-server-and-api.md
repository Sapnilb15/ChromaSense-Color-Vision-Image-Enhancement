# Increment 15: Server and HTTP API

**Status:** CRITICAL
**Depends on:** 14
**SRS IDs:** SRS-FR-001, SRS-FR-002, SRS-FR-010, SRS-FR-011, SRS-NFR-004, SRS-NFR-005

### Main rules

- Add the Web API and Server Main only, with the six endpoints in `dev/architecture.md`. Add no other endpoint.
- Web API holds no business rules: it caps the body, checks request shape, calls one use case, and maps the result or error.
- Server Main is the only place that reads the environment and the only place that constructs the store.

### Capability

The portal starts on port 9090 and serves the API that the Web UI will call.

### What may change

- New files: `web_api/app.py`, `schemas.py`, `session_cookie.py`, `routers/pages.py`, `routers/images.py`, `routers/session.py`, `main/settings.py`, `main/wiring.py`, `main/__main__.py`, and tests in `src/portal/tests/web_api/`.
- A placeholder `web_ui/templates/index.html` with only a heading, so `GET /` renders. Increment 16 replaces it.

### What must stay

- All use cases and the store.

### Implementation notes

1. **Session cookie** (`session_cookie.py`): name `chromasense_session`, value from `secrets.token_urlsafe(32)`, `httponly`, `samesite="lax"`, not `secure` (plain HTTP on the local network). Any request without a valid cookie gets a new ID, set on the response.
2. **Endpoints and responses** (status codes and JSON shapes `derived`):

   | Method and path | Use case | Success | Errors |
   | --- | --- | --- | --- |
   | `GET /` | none | `index.html` | none |
   | `POST /api/image` (multipart field `file`) | `ProcessUpload` | 201 `{"width", "height"}` | 413 `TOO_LARGE`, 415 `UNSUPPORTED_TYPE`, 422 `CORRUPT` or `TOO_MANY_PIXELS` |
   | `POST /api/image/enhance` (JSON `{"type": "protan" or "deutan", "severity": 0 to 1}`) | `EnhanceImage` | 200 `{"outcome", "message", "eligible_count", "improved_count", "pairs"}` | 404 no image, 422 invalid body |
   | `GET /api/image/view/{original or enhanced}` | `RenderView` | 200 `image/png`, `Cache-Control: no-store` | 404 |
   | `GET /api/image/export` | `ExportImage` | 200 `image/png`, `Content-Disposition: attachment; filename="chromasense-enhanced.png"` | 404 |
   | `POST /api/session/end` | `EndSession` | 204 | none |

   Every error body is `{"reason": "...", "message": "..."}`, using the messages from increments 11 to 13.
3. **Upload cap**: in `routers/images.py`, read `UploadFile.read(max_bytes + 1)`. If the result is longer than `max_bytes`, return 413 before calling the use case.
4. **`main/settings.py`**: `Settings.from_env()` reads `CHROMASENSE_DATA_DIR` (default `/data`), `CHROMASENSE_CONFUSION_THRESHOLD` (10), `CHROMASENSE_PALETTE_COLORS` (12), and `CHROMASENSE_IDLE_MINUTES` (30). This is the only module that reads `os.environ`.
5. **`main/wiring.py`**: `build_app(settings)` constructs `SystemClock`, `FilesystemSessionImageStore`, every use case, and `create_app(...)`. FastAPI `lifespan`: on startup, delete every existing session; then start an `asyncio` task that runs `PurgeIdleSessions` every 60 seconds; cancel it on shutdown. Run the blocking use cases in the thread pool (`run_in_threadpool`) so one large image does not block other requests.
6. **`main/__main__.py`**: `uvicorn.run(build_app(Settings.from_env()), host="0.0.0.0", port=9090)`.

### Verification

- Web API tests with fake use cases cover each row of the table, including the cookie being set and an 11 MB body getting 413 without the use case being called.
- `docker compose up portal`, then from the host: `curl -c jar -F file=@sample.png http://localhost:9090/api/image` returns 201, and `GET /api/image/view/original` with the same cookie returns the PNG.
- Uploading a text file renamed `.png` returns 415 with its message.
- `POST /api/session/end` removes that session's folder from the data volume.
- Restarting the `portal` container leaves no session folders.
- `docker compose run --rm dev lint-imports --config src/portal/pyproject.toml` and `pytest src/portal/tests` pass.

### Risk

This is the first time every server part runs together, and the first place where the architectural boundary can be broken in practice, for example by business rules drifting into routers or by the store being built outside Server Main.

### Failure indicators

- A router decides a limit, a message, or an outcome.
- `lint-imports` fails, or a router imports `chromasense.storage`.
- The portal is not reachable from another device, because it bound to `127.0.0.1`.
- Session folders remain after a restart or an end-session call.

### Isolation test

Run `create_app` with fake use cases and `fastapi.testclient.TestClient`, with no real store, to check routing and error mapping. Then run `build_app` with a temporary data folder and the real engine for one upload.

### Rollback

Delete the files this increment added under `web_api/`, `main/`, and `tests/web_api/`, and the placeholder template. Return to the state after `14-session-storage-and-cleanup.md` and set this row to `rolled back`.

### Main rules (repeated)

- Add the Web API and Server Main only, with the six endpoints. Add no other endpoint.
- Web API holds no business rules.
- Server Main is the only place that reads the environment and constructs the store.
