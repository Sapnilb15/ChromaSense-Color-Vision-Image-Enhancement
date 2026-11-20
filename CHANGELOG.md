# Changelog

## 1.0 (in progress)

Release 1.0 is a rebuild against the [November 2026 SRS](docs/ChromaSense_SRS.docx). It narrows ChromaSense to one workflow for people with red–green color vision deficiency: upload a picture, choose a protan or deutan profile and severity, compare the enhanced image with the original, and download it.

The requirements went from about 110 rows in 0.5 to 18. Release 0.5 is available at the `v0.5` git tag.

### Removed

- AI interpretation of charts and maps, follow-up questions, verified and unverified flags, the AI cache, rate limits, and the spend cap
- Spoken playback and severe low vision support
- Local text recognition, shape and region detection, legend detection, image type classification, and the analysis endpoint
- Color identification by click, tap, or keyboard, and color naming
- The CVD simulator page, tritan and achromatopsia profiles, and the "no CVD" option
- Pattern overlays, the enhancement strength control, and the introduction page
- Drag and drop, clipboard paste, and HEIC and WEBP input
- Separate speed targets, usability score, uptime target, 200 and 400 percent zoom, and forced-colors requirements

### Changed

- **Large images**: images over 12 megapixels are rejected. Release 0.5 downscaled them.
- **Retention**: uploads are deleted when the session ends (page closed, 30 minutes idle, or server restart). Release 0.5 kept them for 24 hours.
- **Download**: always a PNG.
- **Success measure**: at least 80 percent of eligible color pairs must improve for each profile on held-out photos, charts, and maps. In 0.5 this was a `should`, measured on flat graphics only.
- **Speed**: one limit. Processing must finish, or report a recoverable error, within 30 seconds.
- **Profile**: protan and deutan only, and the profile is not stored in the browser.

### Added

- A message when enhancement could not improve a confusable pair
- A requirement that the app makes no medical, diagnostic, or exact-perception claims
- SVG renders of the architecture diagrams, generated from their Mermaid sources
- Google-style docstrings on every public module, class, and function, checked in CI by Ruff
- An audience statement at the top of each document, with the documentation set following ISO/IEC/IEEE 26514:2022

### Kept from 0.5

- Clean Architecture with a numbered Pipe and Filter pipeline
- Machado (2009) simulation, CIEDE2000 distances, and k-means palettes in CIELAB
- Lightness separation as the one enhancement method, chosen by the [0.5 evaluation](docs/enhancement-evaluation-v0.5.md)
- FastAPI with server-rendered pages, Docker Compose, and port 9090

## 0.5

The AI-powered color accessibility portal for people with CVD and low vision, built against the earlier SRS. Its code and documents are at the `v0.5` git tag, in `BlindSpot_ChromaSense-main/`.
