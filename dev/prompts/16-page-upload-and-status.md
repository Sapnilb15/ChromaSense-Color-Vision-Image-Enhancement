# Increment 16: Page, upload, and status messages

**Status:** Standard
**Depends on:** 15
**SRS IDs:** SRS-FR-001, SRS-FR-002, SRS-FR-004, SRS-NFR-005, SRS-NFR-003

### Main rules

- Build the single page and its upload step only. Add no second page.
- The browser does no pixel work. It sends the file and shows what the server returns.
- Every status message is text in one shared `aria-live` region, never color alone.

### Capability

The user picks a PNG or JPEG with the file picker and sees the original image, or a clear error.

### What may change

- New files: `web_ui/templates/base.html`, `web_ui/templates/index.html` (replacing the placeholder), `web_ui/static/css/app.css`, `web_ui/static/js/upload.js`, `web_ui/static/js/status.js`, `web_ui/static/js/session.js`.
- `web_api/routers/pages.py`: mount `web_ui/static` at `/static` with `StaticFiles`.

### What must stay

- Every API endpoint, its responses, and all use cases.

### Implementation notes

1. `base.html`: `lang="en"`, viewport meta, a `<header>` with the name ChromaSense, a `<main>`, and a `<footer>` stating: "ChromaSense adjusts colors to help tell them apart. It does not diagnose color vision deficiency or give medical advice, and it does not show exactly what typical color vision sees."
2. `index.html`, first part, in this order:
   - A short introduction of the workflow: upload, choose a profile and severity, compare, download.
   - Step 1 form: a visible `<label>` for `<input type="file" accept="image/png,image/jpeg">`, with the limits "PNG or JPEG, up to 10 MB and 12 megapixels" in its description (`aria-describedby`).
   - A status region: `<div id="status" role="status" aria-live="polite">`.
   - An original image `<figure>` with `<img alt="Original image">` and a caption, hidden until an upload succeeds.
3. `status.js`: `setStatus(text, kind)`, where `kind` is `info`, `success`, or `error`. Prefix the visible text with "Uploading:", "Done:", or "Error:", so the state never relies on color.
4. `upload.js`: on the file input's `change` event, `fetch("/api/image", {method: "POST", body: FormData})`. Announce "Uploading:" before the request. On 201, set the image `src` to `/api/image/view/original?v=<timestamp>`, show the figure, and announce the size. On an error, announce `Error: <message>` from the JSON body and keep any earlier original on screen. Keep keyboard focus on the file input.
5. `session.js`: `window.addEventListener("pagehide", () => navigator.sendBeacon("/api/session/end"))`.
6. `app.css`: system font stack, a readable base size, `:focus-visible` outlines at least 2 px with contrast of at least 3:1, and images at `max-width: 100%`.

### Verification

- In the browser, choosing a PNG and then a JPEG each shows the original image with its size announced.
- Choosing a renamed text file and a truncated JPEG each shows `Error:` with the server's reason, and no image request is made for that file.
- Closing the tab removes the session folder from the data volume.
- `docker compose run --rm dev pytest src/portal/tests` passes.

### Main rules (repeated)

- Build the single page and its upload step only. Add no second page.
- The browser does no pixel work.
- Every status message is text in one shared `aria-live` region, never color alone.
