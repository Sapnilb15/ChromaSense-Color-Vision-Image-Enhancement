# Increment 13: View and export use cases

**Status:** Standard
**Depends on:** 12
**SRS IDs:** SRS-FR-004, SRS-FR-008, SRS-FR-010, SRS-FR-007

### Main rules

- Add `RenderView` and `ExportImage` only.
- Return PNG bytes from `encode_png`. Export only PNG.
- Pixels outside the mask in the exported PNG equal the decoded original exactly.

### Capability

Application Core returns the original or enhanced image for display, and the enhanced image as a PNG download.

### What may change

- New files: `core/use_cases/render_view.py`, `core/use_cases/export_image.py`, and tests in `src/portal/tests/core/`.

### What must stay

- `ProcessUpload`, `EnhanceImage`, the models, and the ports.

### Implementation notes

1. `class View(Enum)` (`derived`, in `core/models.py`): `ORIGINAL`, `ENHANCED`.
2. `RenderView(store, clock)`. `execute(RenderViewRequest(session_id, view)) -> RenderViewResponse(png: bytes, image_id: str)`.
   - `ORIGINAL` with no image → `NoImageInSession("Upload an image first.")`.
   - `ENHANCED` with no result or no enhanced pixels → `NoImageInSession("There is no enhanced image yet.")`.
3. `ExportImage(store, clock)`. `execute(ExportImageRequest(session_id)) -> ExportImageResponse(png: bytes, filename: str)`, with `filename = "chromasense-enhanced.png"`. With no enhanced pixels → `NoImageInSession("There is no enhanced image to download.")`.
4. Both touch the session. The export is at the original resolution, because uploads are never downscaled.

### Verification

- `RenderView` for `ORIGINAL` returns a PNG that decodes to the stored original pixels.
- After an `ENHANCED` outcome, `ExportImage` returns a PNG that decodes to the stored enhanced pixels, and its pixels outside the mask equal the original exactly.
- After a `NO_CONFUSABLE_PAIRS` outcome, `RenderView` for `ENHANCED` and `ExportImage` both raise `NoImageInSession` with their messages.
- `docker compose run --rm dev pytest src/portal/tests/core` passes.

### Main rules (repeated)

- Add `RenderView` and `ExportImage` only.
- Return PNG bytes from `encode_png`. Export only PNG.
- Pixels outside the mask in the exported PNG equal the decoded original exactly.
