# Increment 17: Profile, comparison, and download

**Status:** Standard
**Depends on:** 16
**SRS IDs:** SRS-FR-003, SRS-FR-008, SRS-FR-009, SRS-FR-010, SRS-FR-011

### Main rules

- Add the profile and severity controls, the comparison slider, and the download link only.
- Offer protan and deutan only. Do not add a "no CVD" option or any other type.
- Offer the download only when the outcome is `ENHANCED`.

### Capability

The user picks a profile and severity, generates a result, compares it with the original at the same image area, and downloads it as a PNG.

### What may change

- `index.html`: add steps 2 to 4 below the upload step.
- New files: `web_ui/static/js/profile.js`, `web_ui/static/js/compare.js`.
- `app.css` for the new controls.

### What must stay

- The upload step, the status region, and every API endpoint.

### Implementation notes

1. Step 2, a `<fieldset>` with `<legend>Color vision profile</legend>`: two radio buttons, "Protan" and "Deutan", with none selected at first. A labeled `<input type="range" min="0" max="1" step="0.05">` for severity, starting at 1.0 (`derived`), with an `<output>` that shows the value as text. A "Enhance image" button, disabled until an image is uploaded and a profile is chosen.
2. `profile.js`: on "Enhance image", `POST /api/image/enhance` with `{"type", "severity"}`. Announce "Enhancing:" before the request. On 200, announce the `message` with "Done:" and update step 3. On an error, announce `Error: <message>`. Changing the profile or severity and pressing the button again generates a new result (SRS-FR-011). A new upload hides step 3 and the download link.
3. Step 3, comparison: a figure that stacks the original and the enhanced image at the same size, with the enhanced image clipped from the left by a labeled `<input type="range" min="0" max="100">` named "Comparison position", plus an `<output>` such as "50 percent enhanced". Both images have text alternatives that name the view, for example "Enhanced image for deutan, severity 0.8". `compare.js` sets the clip from the slider. When the outcome is not `ENHANCED`, step 3 shows only the original and the outcome message.
4. Step 4: `<a href="/api/image/export" download="chromasense-enhanced.png">Download enhanced PNG</a>`, shown only when the outcome is `ENHANCED`.
5. Load the enhanced image from `/api/image/view/enhanced?v=<timestamp>`, so the browser never shows a cached older result.

### Verification

- Protan and deutan, and severity 0 and 1, are each selectable, and each sends that value in the request.
- With the deutan red–green test image, the comparison slider reveals the original and the enhanced image over the same area, and the download saves a PNG that opens and matches the displayed enhanced image.
- A red and blue image shows the "No colors likely to be confused were found" message, with no download link.
- Switching deutan to protan and pressing "Enhance image" again updates the result.
- `docker compose run --rm dev pytest src/portal/tests` passes.

### Main rules (repeated)

- Add the profile and severity controls, the comparison slider, and the download link only.
- Offer protan and deutan only.
- Offer the download only when the outcome is `ENHANCED`.
