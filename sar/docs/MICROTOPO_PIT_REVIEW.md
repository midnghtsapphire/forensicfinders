# microtopo.py reviewed for pit detection

**Who:** Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
**When:** 2026-10-24
**Why:** Audrey asked what M-TMAT does and does not cover for finding excavation pits.
**What:** New file. Read-only review of `blue-ocean-sar/realdata/microtopo.py` (806 lines)
and `test_microtopo.py` (316 lines, 18 tests). No code changed.
**Caveat:** `rasterio` and `scipy` are missing on this machine, so **all 18 tests skipped**
and I could not execute anything. This is a code read, not a verified run.

---

## What it covers, and covers well

- **Two bare-earth DEMs differenced on a common grid**, any CRS, reprojected to the baseline.
- **Vertical datum / geoid offset absorbed** by removing the median dZ over the window.
- **A defensible threshold** rather than a magic number:
  `LoD = t · sqrt(s1² + s2²)`, default t=1.96 (95 %), s1=s2=0.10 m (USGS QL2).
- **Pits and mounds labelled separately**, 8-connected, so a rise and a drop never merge.
- **Minimum area filter** (default 2 m²).
- **Per anomaly:** centroid lat/lon, cell count, area, mean and max dZ, volume, plus
  distance and bearing from a reference point. Sorted by |volume|, IDs assigned.
- **Shape context already computed:** local relief model (plane-detrended, so a uniform
  slope leaves no edge residue) and sky-view factor, with `mean_lrm_m` and `min_svf`
  recorded per anomaly.
- **Provenance:** ledger CSV, GeoJSON, KML and a manifest with SHA-256 hashes.
- **3DEP auto-fetch** for US sites — finds every 1 m project over the window from
  FESM_1m.gpkg, takes earliest and latest as the two epochs, range-requests only the window.
- **Meaningful exit codes:** 0 complete (zero anomalies is a valid result), 2 no overlap or
  no data, 3 fewer than two epochs.
- **An honest docstring.** It already says a DEM change says nothing about cause, and names
  construction, ploughing, erosion, vegetation misclassification and processing differences.

The tests are well built too — synthetic GeoTIFFs with known answers, checking sign,
sort order, bias removal, sub-LoD rejection, CRS reprojection and scaling with cell size.

---

## The number that decides everything

With the defaults: `1.96 × sqrt(0.10² + 0.10²)` = **0.277 m**.

**A disturbance shallower than ~28 cm will not register.** For a cold case where the ground
settled and revegetated years ago, that is the question to answer before anything else: is
the residual depression still deeper than 28 cm? If not, no amount of processing finds it,
and the honest move is to say so rather than lower `--t` until something appears.

Lowering the threshold is available (`--t`, `--rmse-baseline`, `--rmse-recent`) but it buys
false positives at a rate set by the next section.

---

## What it does not cover

Ordered by how much it would change results for pit detection.

**1. No horizontal co-registration.** The docstring states it plainly: *"It does not correct
a horizontal shift or a tilt between surveys."* This is the biggest gap. A sub-metre
horizontal offset between two lidar surveys produces a **dipole** — a paired pit and mound —
at every slope break. On sloped ground that manufactures false pits systematically. The
standard remedy estimates the shift from the relationship between dZ, slope and aspect over
stable terrain and applies it before differencing.

**2. No shape discrimination.** LRM and SVF are computed and *reported*, but nothing uses
them to classify. Every drop ≥ 2 m² and ≥ LoD becomes an `excavation_pit` — ditches, tyre
ruts, erosion gullies, borrow pits, stock ponds included. There is no elongation,
aspect-ratio or depth-to-width test, which is what would separate a grave-shaped feature
from a drainage feature.

**3. No pit-to-mound pairing.** Rises and drops are found independently and no relationship
between them is recorded. Pairing adjacent opposite-sign anomalies would earn its keep
twice: it flags the misregistration dipoles from gap 1, **and** it finds the genuine
excavate-and-pile-spoil signature. Cheap to add, high value.

**4. Vegetation and ground-classification change is named but not acted on.** Two surveys
processed with different ground-classification algorithms produce systematic dZ under
canopy. At forested sites this is likely the dominant false-positive source. No canopy mask,
no point-density check, no flag on cells where classification confidence differs.

**5. LoD is two scalars for the whole window.** Real lidar vertical accuracy varies with
slope, vegetation and point density. A single constant under-detects on flat open ground
and over-detects on steep or vegetated ground. A per-cell uncertainty raster would fix both.

**6. Two epochs only.** `find_epochs` takes the earliest and the latest project. A longer
stack would show *when* the change happened and separate progressive change (erosion,
subsidence) from abrupt change (excavation). That distinction is diagnostic and is currently
unavailable.

**7. US-only fetch.** FESM / prd-tnm is USGS. Outside the US there is no fetch path and you
must supply both DEMs yourself. The `--baseline/--recent` path works fine for that.

**8. No minimum depth, only minimum area.** A 2 m² patch at 0.28 m ranks the same way as a
2 m² patch at 1.5 m, except through the volume sort. A `--min-depth-m` would be one line.

**9. Default window is 120 m radius.** Right for a known LKP, too small for area search.

---

## What I would do, in order

1. **Pit/mound pairing** — smallest change, catches both the artefact and the real signature.
2. **Shape filters using the LRM and SVF already computed** — elongation and depth-to-width.
   No new data needed; the numbers are already in the ledger.
3. **Horizontal co-registration on stable terrain** — the real fix for gap 1, and the one
   that makes lowering `--t` safe.
4. **Slope-aware or per-cell LoD** — follows naturally from 3.
5. **Install rasterio and scipy somewhere and actually run the 18 tests.** Right now nobody
   on this machine knows whether they pass.
