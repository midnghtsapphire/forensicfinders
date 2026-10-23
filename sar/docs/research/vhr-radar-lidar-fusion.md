# VHR radar + lidar fusion for SAR triage (PROTOTYPE)

**Registry ID: 2030** · **Status: PROTOTYPE / RESEARCH** · No claimed detection results.

Idea: use **very high-resolution (VHR) SAR** change cues and **lidar / DEM micro-relief** together to triage search sectors. This note is a crawl → walk → run roadmap for two product shapes, with **verified citations only**. Pasted AI-summary claims (“radar penetrates vegetation”, “real-time grave detection”) are corrected below.

Related Audrey send (not a VHR paper): Hirashima et al. (2022) *Forensic Science International* — human DNA extraction from soil with BSA/skim milk additives (DOI [10.1016/j.forsciint.2022.111284](https://doi.org/10.1016/j.forsciint.2022.111284), PII S0379073822001141). Abstract-only; paywalled. Belongs with soil eDNA **2000**, not this sensor stack.

---

## 0. Source verification (do not cite the paste claims)

| Pasted cue | What it actually is | Use for missing-person VHR? |
|---|---|---|
| ResearchGate 339582539 / PMC7085660 | Ullo, Zarro & Wojtowicz (2020). *LiDAR-Based System and Optical VHR Data for Building Detection and Mapping*. *Sensors* 20(5):1285. doi:[10.3390/s20051285](https://doi.org/10.3390/s20051285). LiDAR nDSM + WorldView-2 OBIA for **buildings** in Lioni, Italy. | Method cue for OBIA / nDSM + optical fusion — **not** a missing-person detector. |
| ResearchGate 352869352 | Spröhnle, Fuchs & Aravena Pelizari (2017). *Object-Based Analysis and Fusion of Optical and SAR Satellite Data for Dwelling Detection in Refugee Camps*. *IEEE JSTARS* 10(5):1780–1791. doi:[10.1109/JSTARS.2017.2664982](https://doi.org/10.1109/JSTARS.2017.2664982). WorldView-2 + TerraSAR-X (X-band) OBIA for **dwellings**. | Shows optical+X-band SAR fusion for **structures**; metal roofs show in SAR; vegetation penetration is **not** claimed. |
| NASA NTRS (WorldView bare earth, boreal) | Neigh et al. (2021). *Estimating Bare Earth in Sparse Boreal Forests With WorldView Stereo Imagery*. *IEEE GRSL*. doi:[10.1109/LGRS.2021.3112387](https://doi.org/10.1109/LGRS.2021.3112387); NTRS PDF [20210024091](https://ntrs.nasa.gov/api/citations/20210024091/downloads/Neigh2021.pdf). Stereo WV → DTM; useful under **&lt;~40%** canopy cover (NMAD &lt;~1.6 m); errors rise above that. | Bare-earth / height under **sparse** canopy — not “radar sees through forest”. Optical stereo, not SAR. |
| MDPI *Remote Sensing* 16(4):670 (2024) | Papić et al. *Person Mobility Algorithm and Geographic Information System for Search and Rescue Missions Planning*. doi:[10.3390/rs16040670](https://doi.org/10.3390/rs16040670). GIS **terrain passability / mobility** for SAR planning. | Mobility layer for planning — **not** lidar/radar person detection. |
| arXiv 2307 (fusing VHR aerial + lidar) | Tingzon, Cowan & Chrzanowski (2023). *Fusing VHR Post-disaster Aerial Imagery and LiDAR Data for Roof Classification in the Caribbean*. arXiv:[2307.16177](https://arxiv.org/abs/2307.16177). Multimodal CNN fusion for **roof type/material**. | Fusion pattern (feature-level beats single modality) — **buildings/roofs**, not graves. |

### Corrected physics (vs generic AI bullets)

| Claim in paste | Correction |
|---|---|
| “Radar penetrates vegetation” | **Band-dependent.** X-band (TerraSAR-X, Capella, Umbra, Sentinel-1 C-band is better than X but still canopy-limited) mostly **surface / volume scatter** in leaf-on forest; little understory. **L-band / P-band** (e.g. ALOS-2 L-band, airborne P-band) penetrate foliage better and sense trunks/ground more. Do not treat commercial VHR X-band as a canopy penetrator. |
| “Real-time” | Orbital revisit is hours–days; tasking + downlink + processing is not phone-live. Airborne can be same-day. Nothing here is real-time person tracking. |
| “Detects missing persons from space” | Published work above is **buildings, dwellings, bare-earth under sparse canopy, mobility GIS, roofs**. No verified orbital “person finder”. Use as **terrain / disturbance triage** only. |

Shipped stack already covers pieces: STAC S1 log-ratio (**910**), 3DEP DTM diff (**920**), Gi* void / micro-relief (**1100** / **1110**), dielectric (**1120**), camera+scene timeline (**1913**), time-series step detector (**300**).

---

## Recommendation: option (B)

| Option | Shape | Verdict |
|---|---|---|
| **(A)** One combined fusion tool | Single binary that ingests SAR + lidar and emits one “fusion score” | **Defer.** Needs labelled disturbance sites, band-aware weighting, and invites false confidence. |
| **(B)** Two add-ons + shared interchange | (B1) VHR SAR change-detection add-on · (B2) lidar micro-relief add-on · both read/write the same GeoTIFF + GeoJSON contract | **Recommend.** Ships crawl pieces independently; fusion later is a join on the interchange, not a rewrite. |

**Why B:** 910/920/1100 already exist as separate tools; VHR SAR (Umbra/Capella) and lidar (3DEP/OpenTopography) have different licenses, resolutions, and failure modes. Shared rasters/vectors let **1913** and sector runners consume either cue without a monolithic scorer.

---

## Shared interchange (both options)

| Artifact | Format | Fields / notes |
|---|---|---|
| Raster cue | Cloud-optimized GeoTIFF, EPSG:4326 or local UTM, float32 | Band 1 = cue value (dB ratio, coherence loss, residual height m). Nodata = NaN. Sidecar `.json` with `source`, `sensor`, `band`, `t0`, `t1`, `registry_id`. |
| Vector cues | GeoJSON FeatureCollection | `kind`: `sar_change` \| `lidar_microrelief`; `score` optional float; `authority` / notes; no case PII in git. |
| Timeline row | JSONL via **1913** | `source`, `t`, `bbox` or `geom`, `href` to raster/vector. |

---

## Map to existing registry IDs

| ID | Role in this roadmap |
|---|---|
| **920** 3DEP | Bare-earth DTM / epoch difference for micro-relief crawl |
| **910** STAC | Sentinel-1 COG search + `log_ratio_db` / anomalies (C-band free path) |
| **940** ArcGIS | Municipal lidar / imagery layers when hosts allowlisted |
| **1100** / **1110** Gi* void detector | Cluster micro-relief residuals; ROC only with user labels |
| **1120** dielectric | Depth/context if later GPR/soil work joins the same sector |
| **1913** timeline | Merge SAR/lidar cue events with camera frames |
| **300** sar-change-detection | Multi-year C/P-band **point** time-series step model (complementary; not VHR pair GeoTIFF) |
| **980** `sar_pair` (stub) | Amplitude-ratio / coherent-change on two GeoTIFFs — crawl code for B1 |

---

## Crawl — free / open data and access

| Source | What you get | Access |
|---|---|---|
| **Sentinel-1** GRD/COG | C-band dual-pol; ~10 m; global free | Element84 Earth Search STAC (already **910**); ASF Vertex |
| **Umbra** open data | X-band VHR spotlight (selected AOIs) | [Umbra Open Data](https://umbra.space/open-data/) — download terms on site; not full tasking |
| **Capella** open data | X-band VHR samples | Capella Open Data / STAC where published; check current portal |
| **ALOS-2** L-band | Better vegetation penetration than X/C for many forest scenes | JAXA / NASA collaborations; ASF / Earthdata where released — **not** unlimited free global like S1 |
| **USGS 3DEP** | Lidar-derived DTM/DSM CONUS | **920** `exportImage` / getSamples; The National Map |
| **OpenTopography** | Global/US lidar point clouds & rasters | opentopography.org API (coldtrace already knows the key env var pattern) |

Honest crawl limits: Umbra/Capella open catalogs are **sparse**. Most US work starts with **S1 + 3DEP**. X-band open scenes are for method practice, not canopy digs.

**Crawl next small step (runnable on free data):**
1. Pick a neutral public bbox (no case).
2. Pull two S1 GRD COGs same orbit/pass via **910**; write amplitude-ratio GeoTIFF with **980** `sar_pair.amplitude_ratio_db` (or `stac.log_ratio_db` on windows).
3. Pull 3DEP DTM via **920**; run residual / Gi* (**1100**) on a small chip.
4. Emit GeoJSON cues + one **1913** timeline row each. **No scoring as “find”.**

---

## Walk — option B add-ons

### B1 — VHR SAR change-detection add-on
- Inputs: two co-registered amplitude (and optional complex) GeoTIFFs; metadata for band (X/C/L).
- Outputs: log-ratio dB raster; optional coherence / CCD index when SLC/complex available; anomaly polygons.
- Prefer same geometry (orbit, look); refuse silent resample without a flag.
- Band note in sidecar: never label X-band products as “penetrating”.

### B1a — Optional speckle filtering before change detection

Speckle is multiplicative noise in SAR intensity imagery; filtering it before a log-ratio
can reduce false change cues, but it also blurs edges and can suppress small real changes.
So in `sar_pair` (**980**) despeckling is **optional and off by default**
(`despeckle_method=None`); the unfiltered behaviour is unchanged.

**Shipped today (classical, numpy only, no training and no GPU):**
- `lee_filter` — classical Lee (local linear MMSE under the multiplicative speckle model,
  Lee 1980), parameterised by window size and number of looks.
- `refined_lee_filter` — edge-aware variant: a small window where the local coefficient of
  variation exceeds the speckle-only value (likely edge or point target), the large window
  elsewhere.
- Both are exercised against **synthetic Gamma-distributed speckle** on a step edge in
  `test_sar_pair.py`; when filtering is on, the method/window/looks are recorded in the
  GeoTIFF tags and the JSON sidecar so a run is reproducible.

**Optional add-ons (not implemented here, not vendored):** the survey repository
*Practical-SAR-Despeckling-Codes* (Yangtian Fang) collects recent single-image SAR
intensity despecklers — <https://github.com/YangtianFang2002/Practical-SAR-Despeckling-Codes>.
As of 2026-10-21 that repository publishes **no LICENSE file** (GitHub reports no license),
so its code is *not* copied or vendored into this repo; only the citation and the method
list are recorded here.

| Method (from that repo) | Paradigm | Needs deep learning? | Needs a GPU? |
|---|---|---|---|
| CL-SAR-Despeckling (ISPRS 2024) | self-/contrastive-supervised CNN | yes | yes, in practice for training; GPU strongly preferred for inference |
| SAR-USE (TGRS 2023) | unsupervised + supervised CNN | yes | yes for training |
| Speckle2Void (TGRS 2021) | unsupervised (blind-spot) CNN, TensorFlow | yes | yes for training |
| MRDDANet (TGRS 2021) | supervised CNN | yes | yes for training |
| SAR-CAM (JSTARS 2021) | supervised CNN | yes | yes for training |
| MONet (TGRS 2020) | supervised CNN | yes | yes for training |
| NR-SAR-DL (TGRS 2020) | supervised CNN, TensorFlow | yes | yes for training |
| SAR-CNN (IEEE SPL 2017) | supervised CNN | yes | yes for training |
| SAR-BM3D (TGRS 2011) | numerical (non-local, MATLAB) | **no** | no |
| PPB (TIP 2009) | numerical (non-local, MATLAB) | **no** | no |

The re-implementations in that repo are organised as BasicSR training configs (PyTorch), i.e.
they assume a training dataset and GPU training before any use. The two numerical methods
(SAR-BM3D, PPB) are MATLAB downloads from their original authors, under those authors' own terms.
Adopting any of them here would need a license check first; the classical Lee filters above
are our own implementation and carry no such constraint.

Reference: Fang Y, Liu R, Peng Y, Guan J, Li D, Tian X. *Contrastive learning for real SAR image
despeckling.* ISPRS J. Photogramm. Remote Sens. 218:376–391 (2024). DOI:
[10.1016/j.isprsjprs.2024.11.003](https://doi.org/10.1016/j.isprsjprs.2024.11.003).

### B2 — Lidar micro-relief add-on
- Inputs: DTM or LAS→DTM (810 / 3DEP / OpenTopography).
- Outputs: detrended residual height; Gi* hot/cold cells (**1110**); optional nDSM if DSM+DTM exist (building/canopy mask — Ullo-style, not person detect).
- Neigh et al.: stereo-optical bare earth only trusted under sparse canopy — document canopy % if using WV stereo instead of lidar.

### Shared walk step
Define one `cue.v1` JSON schema used by both add-ons; add a tiny validator test. Still no fusion score.

---

## Run — optional light fusion (only after labels)

If (and only if) you have **field-labelled** disturbance / control cells:
1. Spatial join B1 + B2 cues on the interchange grid.
2. Train a **transparent** rule or logistic on labelled cells (not a black-box “grave net”).
3. Report ROC with **1100** `curve` pattern; Admiralty grade (**1200**) on the product claim.
4. Timeline (**1913**) carries both cues + soil sample IDs from **2000** if used.

Option (A) monolithic tool is only reconsidered here, after B1 and B2 each pass a labelled panel alone.

---

## Field validation required (before any claim)

- Known dig / control grids with GNSS, photos, soil notes (case/ only, gitignored).
- Same-orbit S1 pairs vs one tasked X-band pair on the **same** grid — compare false-alarm maps.
- Lidar epoch difference vs single-date micro-relief (seasonal leaf-off preferred).
- Canopy cover estimate (NLCD / treecover) so X/C vs L expectations are stated.
- Human review of every automated polygon; no autonomous “detection” language.

---

## First small build (code)

See **980** `geo_connectors/sar_pair.py`: synthetic GeoTIFF amplitude-ratio + optional coherent-change index, unit-tested. Real Umbra/Capella files stay outside git.

---

## Real today vs speculative

| Real today | Speculative |
|---|---|
| S1 log-ratio + 3DEP residual + Gi* as **triage layers** | Orbital X-band “sees through trees to a body” |
| OBIA / DL fusion for **buildings & roofs** (cited papers) | Unlabelled fusion score marketed as person find |
| L-band literature better for forest floor cues than X-band | Treating Capella/Umbra open scenes as real-time SAR |

Sources are only those verified in §0 and the data portals above. Nothing here claims a detection result.
