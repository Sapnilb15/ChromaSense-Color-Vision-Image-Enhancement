# Increment 10: Acceptance evaluation

**Status:** CRITICAL
**Depends on:** 09
**SRS IDs:** SRS-NFR-007

### Main rules

- Add the acceptance test and its results document only. Do not change filter behavior in this increment.
- Never create, generate, or alter held-out images. The team sets them aside before tuning. If they are missing, the test skips with a reason.
- Do not tune the engine against the held-out set. Tuning uses the development fixtures only.

### Capability

One test measures the 80 percent target on the held-out set and reports the results that the acceptance plan asks for.

### What may change

- New files: `src/color_engine/tests/acceptance/test_separation_target.py`, `src/color_engine/tests/data/acceptance/labels.json` (schema and an empty `images` list if the team has not supplied images yet), `docs/acceptance-results.md`.

### What must stay

- All filters and rules. If the test shows a shortfall, record it and raise it with the user. Do not change a filter here.

### Implementation notes

1. `labels.json` schema (`derived`):
   ```json
   {
     "threshold": 10,
     "severity": 1.0,
     "images": [
       {
         "file": "chart-01.png",
         "type": "chart",
         "regions": [
           {"id": "bar-a", "box": [x, y, width, height], "reference_rgb": [r, g, b]}
         ]
       }
     ]
   }
   ```
   `type` is `photo`, `chart`, or `map`.
2. For each profile (protan, deutan) and each image: decode with `decode_1`, then run filters 2 to 5 with the recorded threshold and severity and a palette color count of 12.
3. Eligible pairs come from the labeled target regions, following the acceptance plan: a pair of regions is eligible when the reference colors are at least the threshold apart in the original and below it after simulation. Measure each region's mean CIELAB in the original and enhanced pixels inside its box, simulate both, and count the pair as improved when the simulated distance grew.
4. Also report newly confusable region pairs and the count of changed pixels outside every target region box.
5. The test prints a Markdown table by profile and image type: improved, eligible, percent, newly confusable, and pixels changed outside target regions, with the threshold and severity. It fails if either profile is below 80 percent. It is skipped with the reason `held-out set not supplied` when `images` is empty.
6. `docs/acceptance-results.md` records the date, the threshold, the severity, the printed table, and a short note. Until the held-out set exists, it says that no results are recorded yet.

### Verification

- With the held-out set supplied, the test reports at least 80 percent improved pairs for protan and for deutan, and `docs/acceptance-results.md` holds the table.
- Without it, the test is skipped with the reason above. That is `yellow` in tracking.
- `docker compose run --rm dev pytest src/color_engine/tests/acceptance -s` prints the table or the skip reason.

### Risk

The SRS success measure counts photos, charts, and maps equally. Photos have noisy regions, so palette clusters may not line up with the labeled regions, and the measure could fall short even when flat graphics pass.

### Failure indicators

- Percent improved below 80 for one profile, often for photos only.
- Many pixels changed outside target boxes, meaning the mask is wider than the labeled regions.
- Newly confusable pairs after enhancement.

### Isolation test

Run the same measurement on the development fixtures from increments 07 to 09 with one hand-written `labels.json` in a temporary folder. Then run it per image type to find which type falls short.

### Rollback

Delete the acceptance test and keep `docs/acceptance-results.md` with a note that the evaluation is not in place. Return to the state after `09-separation-check.md` and set this row to `rolled back`.

### Main rules (repeated)

- Add the acceptance test and its results document only. Do not change filter behavior in this increment.
- Never create, generate, or alter held-out images. If they are missing, the test skips with a reason.
- Do not tune the engine against the held-out set.
