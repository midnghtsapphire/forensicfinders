# sar/: forensicfinders SAR toolchain

This folder holds the deterministic search tools, every one covered by tests. Each component has a stable number in `registry.json`.
New here? Read this file first, then [`docs/HANDOFF.md`](docs/HANDOFF.md).

## Quickstart (about 5 minutes)
1. Use Python 3.12 or newer: `python3 --version`.
2. Install the test dependencies from the repo root:
   ```bash
   pip install numpy rasterio piexif pillow -r sar/coldtrace/backend/requirements-test.txt
   ```
   On a Debian/Ubuntu system Python, add `--user --break-system-packages`, or use a venv.
3. Run everything offline: `python3 sar/registry.py --test-all`. It should end with `ALL OK`. On 2026-10-21 that was 597 tests: 0 failed, about 30 skipped for optional dependencies or live checks.
4. List the components: `python3 sar/registry.py`
5. Test one component: `python3 sar/registry.py 910 --test`, or open its details with `python3 sar/registry.py 910`.

## Registry
| ID | Path | What it does |
|---|---|---|
| 100 | `blue-ocean-sar` | Sensing toolchain: person finder, dual comms publisher, provenance, evidence package, opendata adapters, realdata terrain/NDVI/change/sweep-width modules |
| 110 | `blue-ocean-sar/evidence` | Evidence chain-of-custody package and importers |
| 120 | `blue-ocean-sar/opendata` | Public open-data adapters (fixtures only in tests) |
| 130 | `blue-ocean-sar/realdata` | DEM terrain, microtopography, Sentinel-2 NDVI/change, sweep width, field log, evidence scoring/fusion |
| 140 | `blue-ocean-sar/public_records_engine.py` | Pluggable public-records engine (no built-in data; Census Geocoder connector; authority required per connector) |
| 150 | `blue-ocean-sar/master_sensor_wave_search_script_v2.py` | Multi-band GPR/sensor scoring script (covered by test_provenance.py, 22 tests) |
| 200 | `hfmr` | Historical forensic material reanalysis: acquisition, archive, retrieval, discovery, municipal/construction records, evidence engine |
| 300 | `sar-change-detection` | SAR (radar) change detection |
| 400 | `sensor-fusion-grid` | Sensor fusion into a voxel grid |
| 500 | `gpr-wave-model` | Ground-penetrating-radar wave physics model |
| 600 | `cot-export` | Cursor-on-Target export for ATAK |
| 700 | `coldtrace` | Temporal GIS FastAPI backend (viewshed, NDVI/elevation change, heat map). No demo data: missing inputs answer {status: no_data} HTTP 424 |
| 800 | `lpb` | Data-driven lost-person-behavior distance rings; tables must cite a source (unverified tables refused by default) |
| 810 | `instrument_input` | LiDAR (LAS/CSV) and GPR (CSV) file input plus deterministic synthetic samples in local metres (no geo coords) |
| 811 | `instrument_input/pi_radar_logger.py` | Pi field logger stub (GPS JSONL + synthetic burst + preview); see phone-gpr Pi section |
| 820 | `exif_metadata` | EXIF metadata reader (camera, datetime, GPS, software) |
| 900 | `geo_connectors` | Live public geo connectors with retry/backoff and host allowlist; recorded fixtures for offline tests; SAR_LIVE_TESTS=1 for live |
| 901 | `geo_connectors/netio.py` | HTTP: https-only allowlist, 429/5xx/network retry with exponential backoff + jitter, size cap |
| 910 | `geo_connectors/stac.py` | STAC search (Element84 Earth Search S1/S2, NASA CMR LPCLOUD HLS) with paging; COG window read; NDVI, ΔNDVI, S1 log-ratio dB, sigma anomalies |
| 920 | `geo_connectors/dep3.py` | USGS 3DEP DTM exportImage (GeoTIFF), getSamples point elevations, DTM difference |
| 930 | `geo_connectors/wayback.py` | Wayback CDX query and content-digest change list |
| 940 | `geo_connectors/arcgis.py` | ArcGIS REST layer query, GeoJSON, resultOffset paging; municipal hosts via allow_host() |
| 950 | `geo_connectors/mcp_server.py` | stdio MCP server: search_stac_satellite, query_usgs_lidar, sample_usgs_elevation, wayback_cdx_diff, arcgis_query |
| 960 | `geo_connectors/verify_connectors.py` | Live health check of all 5 endpoints; writes out/health.json and status=PASS|FAIL to $GITHUB_OUTPUT (used by aegis-health-check) |
| 970 | `geo_connectors/run_sectors.py` | Sector pipeline from a case config: cloud-filtered STAC, COG ΔNDVI, 3DEP centre elevation (used by aegis-sar-runner) |
| 980 | `geo_connectors/sar_pair.py` | Pairwise SAR GeoTIFF amplitude-ratio (dB) + coherent-change index; synthetic tests; crawl for 2030 |
| 1000 | `forensic_models` | Sourced, data-driven forensic models (constants.json: every constant has a DOI/URL; unsourced ones are user_required) |
| 1010 | `forensic_models/taphonomy.py` | Megyesi ADD from TBS, Vass PMI (aerobic/burial), Topp θ↔ε, saponified fraction (rate user-supplied) |
| 1020 | `forensic_models/soil_nitrogen.py` | Grave-soil N pathway with sourced Q10 and WFPS optimum; site rates must be supplied |
| 1100 | `forensic_models/void_detector.py` | validate/run/demo/curve: real DEMs (file or 3DEP via 920) → detrend or epoch diff → Gi* anomaly cells; ROC/AUC only from user labels |
| 1110 | `forensic_models/gistar.py` | Getis-Ord Gi* (queen, self-inclusive, binary); matches PySAL esda to 1e-9 |
| 1120 | `forensic_models/gpr_dielectric.py` | eps_eff=(1-θ)[ε_fat(1-f_sap)+ε_soap f_sap]+θ ε_soil, v=0.3/√ε, reflection coefficient, depth from TWT |
| 1200 | `forensic_models/reliability.py` | Deterministic Admiralty A–F/1–6 grading from a versioned lookup table (reliability_rubric.json) |
| 1300 | `forensic_models/qpcr_qc.py` | qPCR QC from QuantStudio/Bio-Rad CFX exports: efficiency, R², NTC/EB, IPC ΔCq inhibition |
| 1900 | `docs/DOPPLER_EVALUATION.md` | Evaluation: notebook Doppler corrector does not belong (doc only, no code) |
| 1910 | `cameras` | Public webcam/traffic-cam + Ring (own account) connectors and frame-to-timeline merger |
| 1911 | `cameras/public_cams.py` | Data-driven public camera registry (sources.json); list + timestamped snapshots with SHA-256 metadata |
| 1912 | `cameras/ring_cam.py` | Ring via ring_doorbell: devices, history, download, snapshot; token cache mode 600; credentials from env only |
| 1913 | `cameras/timeline.py` | Merge camera frames/events and satellite scenes into a sorted SAR timeline (JSONL) |
| 2000 | `docs/research/soil-edna-detection.md` | PROTOTYPE/RESEARCH: crawl-walk-run roadmap for human (then canine) soil eDNA and CDI chemistry; cited sources only, no claimed results |
| 2010 | `docs/research/PROTOTYPES.md` | Index of notebook/research ideas with status and next small step |
| 2020 | `docs/research/phone-gpr-addon.md` | PROTOTYPE: phone/USB mmWave & GPR roadmap + Raspberry Pi field host BOM/wiring; ties to 1120 and 811 |
| 2030 | `docs/research/vhr-radar-lidar-fusion.md` | PROTOTYPE: VHR SAR + lidar micro-relief crawl-walk-run; recommend two add-ons (B); verified citations; no claimed results |
| 2040 | `docs/research/INVENTION-DISCLOSURE.md` | PROTOTYPE: invention disclosure (2020/811, 2030/980, 2000); prior art; not legal advice; keep private |

IDs are permanent. Never reuse a retired number. A child ID such as 910 runs its parent's tests (900).

## Offline vs. live
- **Offline is the default.** Connector tests replay responses recorded from the real endpoints on 2026-10-21, kept in `geo_connectors/fixtures/`. The recording used a neutral bbox in the Nebraska Sandhills, not a case area.
- **Live run:** `cd sar && SAR_LIVE_TESTS=1 python3 -m unittest -v geo_connectors.test_geo_connectors.Live`
- **In GitHub Actions:** run the `sar-tests` workflow by hand and tick **live**. There is no schedule. Setting the repo variable `SAR_LIVE_ALLOWED=0` turns the live job off.

## GitHub Actions (all manual)
| Item | What it does |
|---|---|
| `.github/workflows/sar-tests.yml` | Offline test suite, plus an optional live job (tick **live**) |
| `.github/workflows/daily_sar_run.yml` | Despite the name: **workflow_dispatch only**, no cron, no auto-commit. Health check, then the sector run; uploads `out/` as artifact `sar-run-<run id>` |
| `.github/actions/aegis-health-check` | Runs registry 960. Output `status` = `PASS` or `FAIL` (really written to `$GITHUB_OUTPUT`). Inputs: `out_dir` (default `out`), `skip`, `fail_on_error` |
| `.github/actions/aegis-sar-runner` | Runs registry 970. Inputs: `config` (relative to `sar/`, default the synthetic template), `max_cloud_cover` (default 20), `nasa_bearer_token` (optional, masked), `out_dir` |

Both actions write under `${{ github.workspace }}/out`, not the notebook's hard-coded `/workspace/out`. Turn off every live run by setting the repo variable `SAR_LIVE_ALLOWED=0`. Optional secret: `EARTHDATA_TOKEN`.

## Real vs. aspirational
Only things that actually ran are listed as real. See HANDOFF.md section 6 for the full list.
