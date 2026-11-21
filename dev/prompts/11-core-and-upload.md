# Increment 11: Application Core and the upload use case

**Status:** CRITICAL
**Depends on:** 10
**SRS IDs:** SRS-FR-001, SRS-FR-002, SRS-FR-004, SRS-FR-011, SRS-NFR-004

### Main rules

- Add the core models, ports, errors, and `ProcessUpload` only.
- Application Core imports Color Engine and the standard library only. Test it with fakes for every port.
- A new upload replaces the session's previous image and result.

### Capability

Application Core accepts upload bytes for a session, decodes them with filter 1, stores the original, and turns a decode failure into a clear rejection.

### What may change

- New files: `src/portal/chromasense/core/models.py`, `ports.py`, `errors.py`, `use_cases/process_upload.py`, and tests in `src/portal/tests/core/`, including a fake store and a fake clock.

### What must stay

- Color Engine. Core calls `decode_1` and does not reimplement any check from it.

### Implementation notes

1. Models (names from `dev/architecture.md`; fields `derived`):
   - `class UploadRejection(Enum)`: `UNSUPPORTED_TYPE`, `CORRUPT`, `TOO_LARGE`, `TOO_MANY_PIXELS`.
   - `@dataclass(frozen=True) class SessionImage`: `image_id: str`, `pixels: NDArray`, `width: int`, `height: int`, `source_format: str`, `uploaded_at: datetime`.
   - `@dataclass(frozen=True) class ProcessingSettings`: `threshold: float = 10.0`, `color_count: int = 12`, `input_limits: InputLimits = InputLimits()`.
2. `ports.py`, each a `typing.Protocol`:
   - `SessionImageStore`: `save_original(session_id, image)` (also discards any stored result), `load_original(session_id) -> SessionImage | None`, `save_result(session_id, result)`, `load_result(session_id) -> EnhancementResult | None`, `delete_session(session_id)`, `idle_sessions(before) -> list[str]`, `touch(session_id, now)`.
   - `Clock`: `now() -> datetime`.
   `EnhancementResult` is added in increment 12. Use a forward reference until then.
3. `errors.py`: `UploadRejected(reason: UploadRejection, message: str)` and `NoImageInSession(message: str)`.
4. Rejection messages (`derived`), written without color-only cues:
   - `UNSUPPORTED_TYPE`: "This file is not a PNG or JPEG image."
   - `CORRUPT`: "This image file is damaged or incomplete and cannot be opened."
   - `TOO_LARGE`: "This file is larger than 10 MB."
   - `TOO_MANY_PIXELS`: "This image is larger than 12 megapixels."
5. `ProcessUpload(store, clock, settings)`. `execute(ProcessUploadRequest(session_id: str, data: bytes)) -> ProcessUploadResponse(image_id: str, width: int, height: int)`. It calls `decode_1(data, settings.input_limits)`, maps `DecodeError.reason` to `UploadRejection`, assigns `image_id = uuid4().hex`, saves the original, and touches the session. A rejected upload leaves the stored session unchanged.

### Verification

- With a fake store: a valid PNG and a valid JPEG are stored, and the response has the right size.
- Each invalid fixture from increment 05 raises `UploadRejected` with the matching reason and message, and nothing is saved.
- A second upload replaces the first image, and a stored result is discarded.
- `docker compose run --rm dev lint-imports --config src/portal/pyproject.toml` passes.
- `docker compose run --rm dev pytest src/portal/tests/core` passes.

### Risk

This is the first integration of two parts and the first use of the core boundary. Framework or filesystem code leaking into core would break the dependency rule and every later fake-based test.

### Failure indicators

- `lint-imports` reports a forbidden import from `chromasense.core`.
- Core tests need a real folder or FastAPI to run.
- Core repeats file checks that `decode_1` already does, so the two can disagree.

### Isolation test

Run `ProcessUpload` with a fake store and a fake clock on the increment 05 fixtures only, with no Web API and no storage adapter installed.

### Rollback

Delete the files this increment added under `src/portal/chromasense/core/` and `src/portal/tests/core/`. Return to the state after `10-acceptance-evaluation.md` and set this row to `rolled back`.

### Main rules (repeated)

- Add the core models, ports, errors, and `ProcessUpload` only.
- Application Core imports Color Engine and the standard library only. Test it with fakes for every port.
- A new upload replaces the session's previous image and result.
