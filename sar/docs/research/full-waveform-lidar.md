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


## Discrete-return lidar to bare-earth DTM: what the code does today (checked 2026-10-21)

**Finding.** `search_system/remains_anomaly_pipeline.py` (1410), function `fetch_lidar_dtm_3dep`, builds a DTM with a PDAL pipeline that runs `readers.ept` (USGS 3DEP Entwine tiles), then `filters.range Classification[2:2]`, then `writers.gdal` (mean, nodata −9999).
- It **does rasterise a DTM**, but only from points the data provider has **already classified as ground (class 2)**.
- It does **no ground filtering of its own** (no `filters.smrf`, `filters.pmf`, `filters.csf`, `filters.elm` or outlier removal).
- It does not use laspy.
- It shells out to the `pdal` CLI. PDAL is not installed on this box or in CI, and there is no test of this function.
- `geo_connectors/dep3.py` (920) instead pulls USGS's **pre-made** 3DEP DTM from the ImageServer. It also documents that the notebook's old "smrf_filter: Applied" output was fake.

**Gap.**
- Unclassified clouds, such as a team's own drone lidar, or projects with poor classification, would give an empty or wrong DTM.
- There is no noise or outlier step.
- `mean` gridding leaves holes where there are no ground returns; there is no IDW or TIN fill.
- There is no check that a raster was actually produced.

**Suggested fix (prototype, not built).** Add an optional "classify" mode: reset classes, run `filters.elm` and `filters.outlier`, then `filters.smrf`, keep class 2, and write with `writers.gdal` using `output_type idw` and a set radius. Make it skip cleanly when PDAL is absent, and test it on a small public sample cloud. References:
- the [PDAL ground filter tutorial](https://pdal.io/en/stable/tutorial/ground-filters.html)
- OpenSourceOptions, [How to Create a DEM (or Raster) from a Lidar Point Cloud](https://opensourceoptions.com/how-to-create-a-dem-or-raster-from-a-lidar-point-cloud/) (2021 blog guide)
- [erickfaria/LidarToolkit](https://github.com/erickfaria/LidarToolkit) (MIT; small 2025 Python toolkit, unreviewed)
- the arijolma.org DEM/DTM/DSM explainer ([category page](https://arijolma.org/category/software-development/)), an affiliate-style blog used for terminology only. The specific "bare-earth DEM guide" page could not be fetched (Cloudflare block).

- [sanya186/LiDAR-Data-preprocessor](https://github.com/sanya186/LiDAR-Data-preprocessor) has **no licence** (all rights reserved by default). It was created 2025-11-08 and has 0 stars. It is a Gradio and Colab demo that works on **2D LiDAR depth images** (PNG or JPG, for example KITTI depth): DFT/iDFT, median and mean filtering, PCA/SVD stats and histograms. It does **not** read point clouds (no LAS/LAZ), filter ground or build a DTM, so it **does not fill the 1410 gap**. Recorded for completeness only.

**Data access.**
- [USGS Lidar Explorer](https://apps.nationalmap.gov/lidar-explorer/) for finding 3DEP projects.
- NASA [LP DAAC](https://www.earthdata.nasa.gov/centers/lp-daac) for GEDI and other land products.

**Terminology.** "TEM = terrain elevation model", as it appeared in a pasted AI snippet, is **not a standard term**. The standard terms are **DEM** (digital elevation model, often used loosely), **DTM** (bare-earth terrain) and **DSM** (top surface, including canopy and buildings). TEM means transmission electron microscopy (see the glossary in PROTOTYPES.md).
