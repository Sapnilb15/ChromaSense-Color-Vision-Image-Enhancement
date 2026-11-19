# ChromaSense Color Vision Image Enhancement

ChromaSense helps people with red–green color vision deficiency distinguish details in their own images. The same upload and enhancement workflow works with everyday photos, charts, maps, and other still graphics.

1. Upload a PNG or JPEG, up to 10 MB and 12 megapixels.
2. Select a protan or deutan profile and set the severity.
3. Compare the enhanced image with the original.
4. Download the enhanced image as a PNG.

ChromaSense detects colors likely to be confused under the selected profile and adjusts their lightness in targeted regions. Results depend on the image and the selected profile. If no useful adjustment is found, the original remains available. ChromaSense does not diagnose color vision deficiency or give medical advice.

## Releases

| Release | Where | What it is |
| --- | --- | --- |
| 1.0 | This branch (`refactorForSRS`), tagged `v1.0` when the build is complete | The red–green enhancement workflow above, built against the [November 2026 SRS](docs/ChromaSense_SRS.docx) |
| 0.5 | Git tag [`v0.5`](../../tree/v0.5) | The earlier AI color accessibility portal, with AI interpretation, speech, low vision features, and four CVD types |

[CHANGELOG.md](CHANGELOG.md) lists what changed between 0.5 and 1.0.

## Release 1.0 status

| Stage | File | Status |
| --- | --- | --- |
| 1. Requirements | [dev/srs.md](dev/srs.md) | Done |
| 2. Architecture | [dev/architecture.md](dev/architecture.md) | Done |
| 3. Structure | [dev/structure.md](dev/structure.md) | Done |
| 4. Prompts | [dev/prompts/](dev/prompts/) | Done: 20 increments, tracked in [tracking.md](dev/prompts/tracking.md) |
| 5. Build | [src/](src/) | Not started |

## Repository layout

| Folder | Contents |
| --- | --- |
| [dev/](dev/) | Requirements, architecture, structure, and the prompts and guides that the agents follow |
| [src/](src/) | Application code |
| [docs/](docs/) | The SRS, code documentation, [user guides](docs/user-guides/), and [diagrams](docs/diagrams/) |

## Run locally

Release 1.0 in `src/` is not built yet. Its run commands will be added here when the build is complete.

To run release 0.5, install Docker with Docker Compose. Then check out the tag in a separate folder, so it stays apart from the 1.0 work:

```bash
git worktree add ../chromasense-v0.5 v0.5
cd ../chromasense-v0.5/BlindSpot_ChromaSense-main
docker compose build
docker compose up portal
```

Open [ChromaSense on localhost](http://localhost:9090). Image enhancement runs on the server and works without an AI provider or API key. When you are done, remove the folder with `git worktree remove ../chromasense-v0.5`.

## Evaluate the result

Use labeled photos, charts, and maps with known answers. For example, ask which photographed object matches a reference color, which bar matches a legend entry, or which map regions share a category.

The release target is improved simulated separation for at least 80% of eligible color pairs per profile on held-out images. Record results by profile and image type, check for newly confusable pairs, and verify that the enhancement preserves pixels outside its target regions. If participants are available, compare their answer accuracy on original and enhanced images.

## Project documents

- [Software Requirements Specification (docx)](docs/ChromaSense_SRS.docx), with its working copy in [dev/srs.md](dev/srs.md)
- [Architecture](dev/architecture.md)
- [Changelog](CHANGELOG.md)
- [Team roles and deliverables](TEAM_ROLES.md)
- [Release 0.5 enhancement benchmark](docs/enhancement-evaluation-v0.5.md)
