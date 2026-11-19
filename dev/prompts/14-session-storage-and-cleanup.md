# Increment 14: Session storage and cleanup

**Status:** Standard
**Depends on:** 13
**SRS IDs:** SRS-NFR-005, SRS-FR-011

### Main rules

- Add `FilesystemSessionImageStore`, `EndSession`, and `PurgeIdleSessions` only.
- Keep each session's files in its own folder, and nothing outside it. Deleting a session deletes the whole folder.
- Reject any session ID that is not 16 to 128 characters of `A–Z`, `a–z`, `0–9`, `_`, or `-`, so it cannot form a path.

### Capability

Session images live on the filesystem, and they are removed when a session ends or goes idle (Decision 3).

### What may change

- New files: `src/portal/chromasense/storage/filesystem_session_image_store.py`, `core/use_cases/end_session.py`, `core/use_cases/purge_idle_sessions.py`, and tests in `src/portal/tests/storage/` and `src/portal/tests/core/`.

### What must stay

- The port signatures from increment 11. The adapter implements them exactly.

### Implementation notes

1. `FilesystemSessionImageStore(root: Path)` (layout `derived`): `{root}/sessions/{session_id}/` holds `original.png` with `original.json` (image ID, size, format, upload time), and after enhancement `result.json`, `result.npz` (palette arrays, labels, and mask), and `enhanced.png` when there are enhanced pixels. A `last_used` file's modification time is the session's last use.
2. `save_original` writes the original and deletes any result files. `touch` updates `last_used` with `os.utime`. `idle_sessions(before)` lists sessions whose `last_used` time is earlier. `delete_session` uses `shutil.rmtree` and ignores a missing folder.
3. Write files through a temporary name and rename, so a half-written image is never read.
4. Do not log image content or file paths that contain image data.
5. `EndSession(store)`: `execute(EndSessionRequest(session_id))` deletes the session.
6. `PurgeIdleSessions(store, clock, idle_minutes)`: `execute(PurgeIdleSessionsRequest())` deletes every session idle longer than `idle_minutes`, and returns the count deleted. Server Main's startup cleanup in increment 15 uses `idle_sessions` with a time in the future, so all sessions are deleted.

### Verification

- Round trip on a temporary folder: a saved original and result load back with equal pixels and fields.
- `save_original` after a result removes the result files.
- `EndSession` removes the session folder, and nothing for that session remains under the root.
- A session last used 31 minutes ago is purged with `idle_minutes = 30`, and one used 5 minutes ago is not.
- The session IDs `../x` and `abc` are rejected with `ValueError`.
- `docker compose run --rm dev pytest src/portal/tests/storage src/portal/tests/core` passes, and `lint-imports` passes.

### Main rules (repeated)

- Add `FilesystemSessionImageStore`, `EndSession`, and `PurgeIdleSessions` only.
- Keep each session's files in its own folder. Deleting a session deletes the whole folder.
- Reject any session ID that could form a path.
