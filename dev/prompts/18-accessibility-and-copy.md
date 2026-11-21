# Increment 18: Accessibility, layout, and interface copy

**Status:** CRITICAL
**Depends on:** 17
**SRS IDs:** SRS-NFR-002, SRS-NFR-003, SRS-NFR-006

### Main rules

- Add browser tests and fix what they find in the Web UI only. Add no feature.
- The whole workflow works by keyboard alone, with visible focus, labels for screen readers, and no horizontal page scroll on phone or desktop widths.
- No interface text claims to diagnose, give medical advice, or show exactly what typical color vision sees.

### Capability

The page passes keyboard, screen reader label, contrast, layout, and copy checks.

### What may change

- New tests in `src/portal/tests/browser/`.
- `web_ui/templates/*.html`, `web_ui/static/css/app.css`, and `web_ui/static/js/*.js`, only to fix failures found here.

### What must stay

- Every API endpoint, use case, and engine file.

### Implementation notes

1. Run Playwright against a live server started by a pytest fixture with `build_app` and a temporary data folder.
2. Tests:
   - **Keyboard workflow**: with no mouse, Tab to the file input, set a file with `set_input_files`, choose Deutan with the arrow keys, move severity with the arrow keys, press "Enhance image" with Enter, move the comparison slider with the arrow keys, and reach the download link. Check `:focus-visible` styles at each stop, and that focus is never trapped.
   - **axe**: `axe-playwright-python` with tags `wcag2a`, `wcag2aa`, `wcag21aa`, and `wcag22aa` reports no violations before upload, after upload, after an `ENHANCED` result, and after an error.
   - **Layout**: at 375 × 812 and 1280 × 800, `document.documentElement.scrollWidth <= window.innerWidth`, and the full workflow completes.
   - **Not color alone**: every status message starts with its text prefix, and every control has a text label.
   - **Copy**: the rendered page and the messages in `core/policy/outcome.py` contain none of "diagnos" (except in the footer's "does not diagnose"), "medical" (except "does not ... give medical advice"), "cure", "correct your vision", or "see what others see".
3. Fix each failure at its source. Do not disable an axe rule.

### Verification

- `docker compose run --rm dev pytest src/portal/tests/browser` passes.

### Risk

This increment has several goals that can conflict: a custom comparison slider, contrast, visible focus, and phone layout all touch the same controls. Fixing one can break another.

### Failure indicators

- axe contrast or label violations that come back after another fix.
- The comparison slider or severity slider cannot be moved with the arrow keys.
- Horizontal scroll at 375 px caused by the comparison figure.
- A status change that a screen reader does not announce.

### Isolation test

Run each browser test on its own against the page with a stubbed API (Playwright `page.route`), so failures come from the Web UI alone. Then run them against the live server.

### Rollback

Revert the Web UI changes from this increment and keep the tests. Return to the state after `17-profile-compare-download.md` and set this row to `rolled back`.

### Main rules (repeated)

- Add browser tests and fix what they find in the Web UI only. Add no feature.
- The whole workflow works by keyboard alone, with visible focus, labels, and no horizontal page scroll.
- No interface text claims to diagnose, give medical advice, or show exactly what typical color vision sees.
