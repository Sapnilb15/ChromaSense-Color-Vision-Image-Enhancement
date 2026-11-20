# Acceptance results

Results for SRS-NFR-007: enhancement must improve the simulated separation of at least 80 percent of eligible color pairs for each profile on the held-out test set.

## Status

**No results are recorded yet.** The held-out set has not been supplied. Until it is, the acceptance test is skipped with the reason `held-out set not supplied`.

## How to add the held-out set

The team sets these images aside before any engine tuning. They must never be created, generated, or changed by the build.

1. Put PNG and JPEG photos, charts, and maps in `src/color_engine/tests/data/acceptance/`.
2. In `labels.json` in the same folder, list each image with its type and its labeled target regions:

   ```json
   {
     "threshold": 10,
     "severity": 1.0,
     "images": [
       {
         "file": "chart-01.png",
         "type": "chart",
         "regions": [
           {"id": "bar-a", "box": [40, 120, 60, 200], "reference_rgb": [200, 40, 40]},
           {"id": "bar-b", "box": [120, 120, 60, 200], "reference_rgb": [40, 160, 40]}
         ]
       }
     ]
   }
   ```

   - `type` is `photo`, `chart`, or `map`.
   - `box` is `[x, y, width, height]` in pixels. Draw it inside the region, so it holds only that region's pixels.
   - `reference_rgb` is the region's intended color.

3. Run the evaluation and copy the printed table into the Results section below:

   ```bash
   docker compose run --rm dev pytest src/color_engine/tests/acceptance -s
   ```

## How pairs are counted

- A pair of target regions is **eligible** for a profile when the reference colors are at least the threshold apart (CIEDE2000) in the original and below it after simulating that profile.
- An eligible pair is **improved** when the simulated distance between the two regions' mean colors is greater after enhancement than before.
- **Above threshold after** counts improved pairs whose simulated distance after enhancement reaches the threshold. A pair can improve and still be below the threshold, so this column shows how many pairs are no longer confusable at all.
- **Newly confusable** counts pairs that were not eligible, were at least the threshold apart after simulation before enhancement, and fall below it after.
- **Pixels changed outside target regions** counts pixels that differ between the original and enhanced image and lie outside every labeled box.

The test fails if either profile is below 80 percent.

## Results

| Date | Threshold | Severity | Notes |
| --- | --- | --- | --- |
| none yet | | | Held-out set not supplied |
