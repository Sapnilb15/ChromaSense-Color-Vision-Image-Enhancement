# ChromaSense Color Vision Image Enhancement

ChromaSense helps people with red–green color vision deficiency distinguish details in their own images. The same upload and enhancement workflow works with everyday photos, charts, maps, and other still graphics.

1. Upload a PNG or JPEG.
2. Select a protan or deutan profile and set the severity.
3. Compare the enhanced image with the original.
4. Download the enhanced image as a PNG.

ChromaSense detects colors likely to be confused under the selected profile and adjusts their lightness in targeted regions. Results depend on the image and the selected profile. If no useful adjustment is found, the original remains available.

## Run locally

Install Docker with Docker Compose, then run these commands from the repository root.

```bash
cd BlindSpot_ChromaSense-main
docker compose build
docker compose up portal
```

Open [ChromaSense on localhost](http://localhost:9090). Image enhancement runs on the server and works without an AI provider or API key.

## Evaluate the result

Use labeled photos, charts, and maps with known answers. For example, ask which photographed object matches a reference color, which bar matches a legend entry, or which map regions share a category.

The release target is improved simulated separation for at least 80% of eligible color pairs per profile on held-out images. Record results by profile and image type, check for newly confusable pairs, and verify that the enhancement preserves pixels outside its target regions. If participants are available, compare their answer accuracy on original and enhanced images.

## Project documents

- [Software Requirements Specification](docs/ChromaSense_SRS.docx)
- [Team roles and deliverables](TEAM_ROLES.md)
- [Existing enhancement benchmark](BlindSpot_ChromaSense-main/docs/enhancement-evaluation.md)
- [Portal setup and test commands](BlindSpot_ChromaSense-main/README.md)
