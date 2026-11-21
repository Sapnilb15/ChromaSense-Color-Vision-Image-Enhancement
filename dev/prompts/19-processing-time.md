# Increment 19: Processing time

**Status:** Standard
**Depends on:** 18
**SRS IDs:** SRS-NFR-001

### Main rules

- Add the timing test only. Change engine code only if the test fails, and only for speed, never behavior.
- Measure on the reference host: the `dev` container limited to 4 CPU cores and 8 GB.

### Capability

A test shows that a valid image within the limits is processed, or an invalid one rejected, within 30 seconds.

### What may change

- New file: `src/portal/tests/performance/test_processing_time.py`.
- If the test fails: chunking or sampling inside filters 2 to 4, with every earlier test still passing.

### What must stay

- Every filter contract and every result.

### Implementation notes

1. Build a 4000 × 3000 (12 megapixel) PNG in the test: red–green blocks with per-pixel noise so it behaves like a photo, under 10 MB.
2. Run `ProcessUpload`, `EnhanceImage` for deutan at severity 1.0, and `ExportImage` with the real engine and a `FilesystemSessionImageStore` on a temporary folder. Time the total with `time.perf_counter`.
3. Also time the rejection of a PNG header that declares 20 megapixels.
4. Mark the tests `@pytest.mark.performance`, and register the marker in `src/portal/pyproject.toml`.

### Verification

- `docker compose run --rm dev pytest src/portal/tests/performance -s` reports a total under 30 seconds for the 12 megapixel image, and under 2 seconds for the rejection.
- Every earlier test still passes.

### Main rules (repeated)

- Add the timing test only. Change engine code only for speed, never behavior.
- Measure on the reference host: the `dev` container limited to 4 CPU cores and 8 GB.
