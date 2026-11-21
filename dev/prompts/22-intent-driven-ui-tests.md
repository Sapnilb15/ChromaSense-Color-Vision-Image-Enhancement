# Increment 22: Intent-driven UI tests

**Status:** CRITICAL
**Depends on:** 21
**SRS IDs:** SRS-FR-012

### Main rules

- Add the intent suite and fix what it finds in the Web UI only. Add no feature, endpoint, or screen.
- An intent finds elements only by accessible role and name, label, or visible text, and acts only as a user can. No ID, class, or CSS selector, no `set_input_files` on a hidden input, no `fill` on a slider, and no `force=True`. One exception: in Firefox only, when the file chooser does not open after the checks have shown the control is visible, reachable, uncovered, and large enough, the runner sets the file directly and logs a warning (see `tracking.md` › 22 › Notes).
- When an intent fails, fix the Web UI. Never weaken an oracle, skip a step, or loosen an expected message to make it pass.

### Capability

Before anyone spends time on user testing, one command shows whether a person can actually complete each task on the page: upload, choose a profile and severity, compare, download, recover from a rejected file, and start again. A failure names the intent, the step, and what a user would have met, with a screenshot and trace.

### Why the existing browser tests did not catch the failures

The tests from increments 16 to 18 reach controls by ID (`#file-input`, `#status`) and set values directly (`set_input_files`, `fill`). Those calls succeed even when a control is hidden, covered by another element, off screen, too small to press, or has a misleading name, so the tests stay green while a person cannot use the page. They also run only in Chromium. The intent suite checks what the user meets instead.

### What may change

- New files `src/portal/tests/browser/intents/catalog.py`, `oracles.py`, and `test_intents.py`, and new fixtures in `src/portal/tests/browser/conftest.py`.
- `Dockerfile` (`dev` target): `playwright install --with-deps chromium firefox webkit`.
- `.gitignore`: add `test-results/`.
- `.github/workflows/ci.yml`: run the intent suite.
- `web_ui/templates/*.html`, `web_ui/static/css/app.css`, and `web_ui/static/js/*.js`, only to fix failures found here.
- `docs/code/portal.md` (how to run the suite and read a trace), `CHANGELOG.md` (1.0 › Added).

### What must stay

- Every API endpoint, use case, storage, and engine file.
- The existing tests in `src/portal/tests/browser/`. They may only gain shared fixtures.
- `dev/`, except this increment's row in `tracking.md`.

### Implementation notes

1. **Known defects first.** D1 and D2 are already listed in `tracking.md` › 22 › Notes. Put the team's PNG files that failed to display in `src/color_engine/tests/data/samples/ui/`. Add any further UI failure the team has seen to those Notes, in one line each. Write an intent (or a step) for each one and confirm it fails on the current code. Record the failure message.

2. **Catalog** (`catalog.py`). Plain frozen dataclasses, no new dependency. A `Step` holds the step in plain words (`says`), the accessible `role` (or `"label"`), the exact `name`, the `action` (`choose_file`, `click`, `choose`, `slide`, `download`, or `see`), an optional `value`, the text the status region must start with next (`expect_status`), and an optional heading that the control must sit within one screen of (`near`). An `Intent` holds a `key`, the `goal`, its `srs_ids`, its `steps`, and the HTTP error statuses it expects.

   Minimum intents:

   | Goal | SRS IDs |
   | --- | --- |
   | Enhance a photo and download it | SRS-FR-001, SRS-FR-003, SRS-FR-008, SRS-FR-010 |
   | Upload a file that is not an image, read why it was refused, then upload a valid one | SRS-FR-002, SRS-NFR-004 |
   | Upload a picture with no confusable colors and read that nothing needed changing | SRS-FR-009 |
   | Compare the same area of both images with the comparison slider | SRS-FR-004, SRS-FR-008 |
   | Switch from Deutan to Protan and get a new result | SRS-FR-011 |
   | Replace the picture and see no trace of the old result | SRS-FR-011 |
   | Set severity to 0 and to 1 and enhance at each | SRS-FR-003 |
   | Enhance PNG files of different kinds (RGBA, palette, embedded color profile, 6 megapixels), and the team's PNG files that failed to display, and see both images each time (D1) | SRS-FR-004, SRS-FR-008 |
   | After an enhanced result, find and press "Download enhanced PNG" with no more than one screen of scrolling from the comparison (D2) | SRS-FR-010 |

3. **Actions** (`test_intents.py`). Each step acts like a person:
   - `choose_file`: `with page.expect_file_chooser() as chooser:` then click the visible control the user would press, then `chooser.value.set_files(...)`. If no visible control opens the chooser, that is a failure.
   - `click`: Playwright `click()` with its actionability checks, never `force=True`.
   - `drag_to` on a slider: in pointer mode, drag with `page.mouse`; in keyboard mode, Tab to it and use arrow keys and Home/End.
   - Keyboard mode reaches every control with Tab from the top of the page and acts with Enter, Space, and arrow keys only.
   - `download`: `page.expect_download()`, then open the file with Pillow, check it is a PNG, and compare it with the enhanced image fetched by the page.

4. **Oracles** (`oracles.py`). Run all of them after every step. Each returns a sentence a person would understand, or nothing:
   - **Found once**: the role and name match exactly one element.
   - **Visible and reachable**: it is visible, has a box of at least 24 × 24 CSS pixels (WCAG 2.2 target size), can be scrolled fully into the viewport, and `document.elementFromPoint` at its center returns it or a descendant, so nothing covers it.
   - **Enabled** when the step acts on it, and a disabled control has visible text that says why.
   - **Responds**: within 2 seconds of the action, the status region or the page visibly changes; the final state arrives within 30 seconds (SRS-NFR-001).
   - **Status**: the `aria-live` region's text matches `expect_status`, and no message from an earlier step is still shown.
   - **Images**: every visible `img` has `complete`, `naturalWidth > 0`, a rendered box larger than zero, and a non-empty `alt`. In the comparison, the original and enhanced images cover the same area on screen.
   - **Focus**: after an action, `document.activeElement` is not `body` and is visible.
   - **Clean console and network**: no uncaught error, no `console.error`, no failed request, and no response of 400 or more except the rejection the intent expects.
   - **Layout**: `document.documentElement.scrollWidth <= window.innerWidth`.

5. **Matrix and reports.** Parametrize each intent over mode (pointer, keyboard), viewport (375 × 812, 1280 × 800), and browser (Chromium, Firefox, WebKit). Start `context.tracing` for every run. On failure, save `test-results/<intent>-<mode>-<viewport>-<browser>/` with `trace.zip` and `screenshot.png`, and fail with a message in this form:

   > Intent "Enhance a photo and download it", step 3 "Choose the Deutan profile" (pointer, 375 × 812, webkit): the Deutan radio button is covered by the "Comparison position" slider.

6. **Fix the Web UI** for each failure at its source, then rerun the whole matrix.

### Verification

- `docker compose run --rm dev pytest src/portal/tests/browser/intents` passes every run of the matrix.
- Each known defect listed in Notes has an intent that failed before its fix and passes after it.
- `grep -nE "locator\\(|#[a-z-]+|set_input_files|\\.fill\\(|force=True" src/portal/tests/browser/intents/` finds nothing in `catalog.py`, and in `test_intents.py` finds only the Firefox fallback's `set_input_files`.
- Temporarily hiding the file input's visible control, covering the Enhance button with another element, and breaking the enhanced image URL each make at least one intent fail with a readable message. Undo each change after the check.
- Every other command in `structure.md` still passes, with the existing test counts unchanged or higher.

### Main rules (repeated)

- Add the intent suite and fix what it finds in the Web UI only. Add no feature.
- Find elements only by role and name, label, or visible text, and act only as a user can.
- Fix the Web UI when an intent fails. Never weaken an oracle to make it pass.
