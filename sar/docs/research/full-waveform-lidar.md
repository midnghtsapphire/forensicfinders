# Full-waveform lidar for SAR terrain mapping

**Registry ID: 2060** · **Status: PROTOTYPE / RESEARCH** · Code: **985** `geo_connectors/waveform.py`

No results are claimed. This note lists sources and a small first step.

## Why waveform, not only point clouds
A discrete-return lidar gives a few points per pulse. A full-waveform system records the whole
returned energy against time. The last significant return in a footprint is usually read as
ground. Under canopy that can give a terrain estimate where discrete returns are sparse. For
search and rescue that matters for slope, drainage, and access mapping under trees. It is **not**
a way to detect people or small objects: GEDI footprints are about 25 m across.

## Training source
- NASA ARSET, *Spaceborne Lidar for Monitoring Vegetation Structure and Biomass using GEDI*,
  **Part 1: Introduction to Full-Waveform Lidar** (Oct 23, 2025; trainers S. Cooley, N. Pinto).
  <https://www.earthdata.nasa.gov/learn/trainings/spaceborne-lidar-monitoring-vegetation-structure-biomass-using-gedi>
- Self-paced companion with Colab tutorial on L1B waveforms (NASA EarthRISE):
  <https://nasa-earthrise.github.io/training_Getting_started_with_GEDI_spaceborne_lidar/intro-to-waveform-lidar>
- YouTube `k0S5irotxy0`: <https://www.youtube.com/watch?v=k0S5irotxy0>. **Caveat:** YouTube's
  oEmbed metadata (checked 2026-10-21) gives this video as *"Meet GEDI! The Global Ecosystem
  Dynamics Investigation Sensor Aboard the ISS"* (SciTech Daily). That is a GEDI overview, not the
  ARSET recording. Use the ARSET page above for the training itself.

## Data sources
| Source | What | Access |
|---|---|---|
| GEDI L1B v002 (`GEDI01_B`) | Geolocated received waveforms, ~25 m footprints, ISS orbit (~51.6° N/S coverage) | LP DAAC <https://lpdaac.usgs.gov/products/gedi01_bv002/>; `earthaccess.search_data(short_name="GEDI01_B", version="002", bounding_box=...)` |
| GEDI L2A v002 (`GEDI02_A`) | Ground elevation and relative-height (RH) metrics derived from L1B | LP DAAC <https://lpdaac.usgs.gov/products/gedi02_av002/>; `short_name="GEDI02_A"` |
| NEON AOP `DP1.30001.001` | *LiDAR slant range waveform*, airborne, NEON sites only | <https://data.neonscience.org/data-products/DP1.30001.001>; NEON API `https://data.neonscience.org/api/v0/products/DP1.30001.001` (or `neonUtilities`) |

`earthaccess` needs a free NASA Earthdata login (`earthaccess.login()`), stored outside git.
Check the quality flags in L2A (`quality_flag`, `degrade_flag`) before using any ground value.

## Code: 985
`waveform.decompose(wf, t)` removes a median baseline, estimates noise by MAD, finds smoothed
peaks above `noise_sigmas` × noise, then fits a sum of Gaussians with `scipy.optimize.curve_fit`.
It returns the peaks sorted in time and the last one as `ground`. Tests use a synthetic two-return
waveform only (`python3 -m unittest geo_connectors.test_waveform`).

## Roadmap
1. **Crawl:** run 985 on a handful of L1B shots over a known open area; compare the ground peak with
   the L2A ground elevation and with 3DEP (920). Record the differences; do not tune for them.
2. **Walk:** same under canopy at one NEON site where AOP waveforms and discrete lidar overlap.
3. **Run:** only if 1–2 agree, add GEDI ground points as a sparse layer for sector terrain maps.
