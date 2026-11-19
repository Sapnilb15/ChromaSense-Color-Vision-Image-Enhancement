# ChromaSense Color Vision Image Enhancement

ChromaSense helps people with red–green color vision deficiency distinguish details in their own images. The same upload and enhancement workflow works with everyday photos, charts, maps, and other still graphics.

1. Upload a PNG or JPEG, up to 10 MB and 12 megapixels.
2. Select a protan or deutan profile and set the severity.
3. Compare the enhanced image with the original.
4. Download the enhanced image as a PNG.

ChromaSense detects colors likely to be confused under the selected profile and adjusts their lightness in targeted regions. Results depend on the image and the selected profile. If no useful adjustment is found, the original remains available. ChromaSense does not diagnose color vision deficiency or give medical advice.

## Project status

This branch rebuilds ChromaSense against the November 2026 SRS, which narrows the product to the red–green enhancement workflow above. The earlier build, which included AI interpretation, speech, and low vision features, is kept for reference in [Archive/BlindSpot_ChromaSense-main](Archive/BlindSpot_ChromaSense-main/).

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
| [Archive/](Archive/) | The earlier build and its documents, kept for reference |

## Run locally

The new build in `src/` does not exist yet. Run commands for it will be added here when stage 3 is done.

To run the earlier build, install Docker with Docker Compose, then run these commands from the repository root:

```bash
cd Archive/BlindSpot_ChromaSense-main
docker compose build
docker compose up portal
```

Open [ChromaSense on localhost](http://localhost:9090). Image enhancement runs on the server and works without an AI provider or API key.

## Evaluate the result

Use labeled photos, charts, and maps with known answers. For example, ask which photographed object matches a reference color, which bar matches a legend entry, or which map regions share a category.

The release target is improved simulated separation for at least 80% of eligible color pairs per profile on held-out images. Record results by profile and image type, check for newly confusable pairs, and verify that the enhancement preserves pixels outside its target regions. If participants are available, compare their answer accuracy on original and enhanced images.

## Project documents

- [Software Requirements Specification (docx)](docs/ChromaSense_SRS.docx), with its working copy in [dev/srs.md](dev/srs.md)
- [Architecture](dev/architecture.md)
- [Team roles and deliverables](TEAM_ROLES.md)
- [Earlier enhancement benchmark](Archive/BlindSpot_ChromaSense-main/docs/enhancement-evaluation.md)
- [Earlier build setup and test commands](Archive/BlindSpot_ChromaSense-main/README.md)
