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

**Suggested fix (now built as 925, see below).** Add an optional "classify" mode: reset classes, run `filters.elm` and `filters.outlier`, then `filters.smrf`, keep class 2, and write with `writers.gdal` using `output_type idw` and a set radius. Make it skip cleanly when PDAL is absent, and test it on a small public sample cloud. References:
- the [PDAL ground filter tutorial](https://pdal.io/en/stable/tutorial/ground-filters.html)
- OpenSourceOptions, [How to Create a DEM (or Raster) from a Lidar Point Cloud](https://opensourceoptions.com/how-to-create-a-dem-or-raster-from-a-lidar-point-cloud/) (2021 blog guide)
- [erickfaria/LidarToolkit](https://github.com/erickfaria/LidarToolkit) (MIT; small 2025 Python toolkit, unreviewed)
- the arijolma.org DEM/DTM/DSM explainer ([category page](https://arijolma.org/category/software-development/)), an affiliate-style blog used for terminology only. The specific "bare-earth DEM guide" page could not be fetched (Cloudflare block).

- [sanya186/LiDAR-Data-preprocessor](https://github.com/sanya186/LiDAR-Data-preprocessor) has **no licence** (all rights reserved by default). It was created 2025-11-08 and has 0 stars. It is a Gradio and Colab demo that works on **2D LiDAR depth images** (PNG or JPG, for example KITTI depth): DFT/iDFT, median and mean filtering, PCA/SVD stats and histograms. It does **not** read point clouds (no LAS/LAZ), filter ground or build a DTM, so it **does not fill the 1410 gap**. Recorded for completeness only.

**Data access.**
- [USGS Lidar Explorer](https://apps.nationalmap.gov/lidar-explorer/) for finding 3DEP projects.
- NASA [LP DAAC](https://www.earthdata.nasa.gov/centers/lp-daac) for GEDI and other land products.

**Terminology.** "TEM = terrain elevation model", as it appeared in a pasted AI snippet, is **not a standard term**. The standard terms are **DEM** (digital elevation model, often used loosely), **DTM** (bare-earth terrain) and **DSM** (top surface, including canopy and buildings). TEM means transmission electron microscopy (see the glossary in PROTOTYPES.md).

## Ground-filtering fix: `geo_connectors/lidar_dtm.py` (925, PROTOTYPE, built 2026-10-21)

Pipeline: `build_dtm(xyz, method="idw"|"tin", engine="auto"|"pdal"|"pmf", out_path=...)`.
1. **Outlier removal:** kNN mean-distance statistical filter, plus a robust (median/MAD) z-score on height vs local neighbours. This catches isolated high and low noise points (birds, multipath).
2. **Ground classification:** if `python-pdal` is installed, PDAL `filters.smrf` (Pingel, Clarke & McBride 2013, [doi:10.1016/j.isprsjprs.2012.12.002](https://doi.org/10.1016/j.isprsjprs.2012.12.002)). Otherwise our own numpy/scipy **progressive morphological filter**, written from the published description in Zhang et al. 2003 ([doi:10.1109/TGRS.2003.810682](https://doi.org/10.1109/TGRS.2003.810682)): minimum-elevation grid, grey openings with growing windows, slope-scaled height thresholds. No third-party code was copied.
3. **Gridding:** IDW (kNN) or TIN (Delaunay linear interpolation), with nearest-neighbour **hole filling** reported as a mask.
4. **Output:** GeoTIFF via rasterio; `validate_raster` raises `EmptyRaster` if the file is missing or all nodata.
5. **Missing dependencies:** `MissingDependency` / test skips. PDAL is optional, so `engine="auto"` falls back to PMF. laspy is only needed to read LAS/LAZ.

**Synthetic test result (seed 1; not field data).** The cloud is 60 x 60 m: a sloped, undulating known surface with vegetation, two buildings, and 1% noise (30,062 points).
- With the PMF engine, ground recall was 1.00, and vegetation and building points kept as ground were 0.00.
- After outlier removal, the injected noise was 100% removed.
- DTM RMSE against the true surface was **0.021 m for IDW** (max 0.13 m) and **0.021 m for TIN** (max 0.09 m), on a 1 m grid with 100% valid cells. Gridding all points with no ground filter gives 2.03 m RMSE.
- The test threshold is RMSE < 0.15 m.
- These numbers show the code works on an easy synthetic case only. Real clouds (steep terrain, dense low vegetation, bridges) need parameter tuning, and comparison against a USGS-classified 3DEP tile is the next check.

1410 `fetch_lidar_dtm_3dep` is unchanged (it still keeps provider class 2). Its docstring now points to 925 for unclassified clouds. [erickfaria/LidarToolkit](https://github.com/erickfaria/LidarToolkit) (MIT) was a reference only; nothing was taken from it.

## Lidar as images: what transfers and what doesn't (added 2026-10-21)

**"Reprocess lidar into ADF-STEM images" is not a real workflow.** The phrase comes from an AI-generated summary. ADF-STEM (annular dark-field scanning transmission electron microscopy) images are formed by electrons scattered from atomic columns in a nanometre-thick specimen. Lidar is laser ranging over metres to kilometres. No processing step turns one into the other, and the STEM physics (for example, Z-contrast intensity scaling with atomic number) has no lidar counterpart.

**What does transfer** is generic image analysis applied after rasterising lidar:
- **Rasterise first.** Grid the point cloud into an **elevation image** (DTM, DSM, or a local-relief / DTM-difference image; see 925 `lidar_dtm.py` and 1410) or an **intensity / range image** (per-cell return intensity, or the sensor's native range image).
- **Then apply image methods**, including those also used on STEM images:
  - template matching, such as normalised cross-correlation of a depression or mound template, as in 2060;
  - blob detection and local-maximum or centroid finding, such as sub-pixel centroids of compact anomalies;
  - morphology and thresholding.
- Only the image-processing step is shared. Evidence for a burial or object still comes from terrain physics and ground truth, not from any TEM analogy.

Related code (references only, nothing copied):
- [alexandrx/lidar_cloud_to_image](https://github.com/alexandrx/lidar_cloud_to_image) (2019, C++/ROS1).
  - Converts spinning-lidar scans (Velodyne/Ouster) into range, intensity, reflectivity and noise images.
  - No GitHub licence file, but `package.xml` declares Apache 2. Treat it as Apache-2.0 per the package manifest, and confirm before reuse.
  - Inspired by PRBonn/cloud_to_image.
  - It is for vehicle sensor frames, not aerial DTMs.
- [awi-response/LidarProcessing](https://github.com/awi-response/LidarProcessing) (AWI, Python).
  - An aerial-campaign pipeline: PDAL, laspy and rasterio produce DSM, DTM and CHM. Its code references SMRF and CSF ground filters and TIN gridding with fill.
  - **No licence** (all rights reserved by default), so read it but do not copy.
  - It is the closest analogue to 925.
- [t-luanamn/LiDAR-Data-Processing-Pipeline](https://github.com/t-luanamn/LiDAR-Data-Processing-Pipeline) (2025, notebooks).
  - **Unlicense** (public domain).
  - Its `pipeline.json` keeps provider class 2, then runs `filters.outlier` (radius 1.0 m, min_k 3) and `writers.gdal` IDW at 1 m. That is essentially the 1410 approach plus an outlier step. It does no ground classification of its own.
  - Trivially reusable, but 925 already covers it.
- Tabata et al., [arXiv:2607.14639](https://arxiv.org/abs/2607.14639) (2026), *Image-to-Point Cloud Registration Made Easy with Rectified Flow-based LiDAR Upsampling*.
  - It treats lidar as an imaging sensor: it densifies a sparse scan into a lidar intensity image with conditional rectified flow, matches it to a camera image, and solves pose with PnP-RANSAC.
  - Its results are self-reported on R3LIVE.
  - It is a real example of the "lidar → image → image methods" pattern, for camera–lidar registration rather than terrain.
