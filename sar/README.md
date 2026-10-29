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
| 820 | `exif_metadata` | EXIF metadata reader (camera, datetime, GPS, software) |
| 850 | `decode_hooks` | Decode seam: the one place sensor data is conditioned after decoding. Hooks registered here run inside `read_cog_window` (910) and `read_points`/`read_gpr_csv` (810). Identity until a hook is registered, so it changes nothing on its own |
| 900 | `geo_connectors` | Live public geo connectors with retry/backoff and host allowlist; recorded fixtures for offline tests; SAR_LIVE_TESTS=1 for live |
| 901 | `geo_connectors/netio.py` | HTTP: https-only allowlist, 429/5xx/network retry with exponential backoff + jitter, size cap |
| 910 | `geo_connectors/stac.py` | STAC search (Element84 Earth Search S1/S2, NASA CMR LPCLOUD HLS) with paging; COG window read; NDVI, ΔNDVI, S1 log-ratio dB, sigma anomalies |
| 920 | `geo_connectors/dep3.py` | USGS 3DEP DTM exportImage (GeoTIFF), getSamples point elevations, DTM difference |
| 930 | `geo_connectors/wayback.py` | Wayback CDX query and content-digest change list |
| 940 | `geo_connectors/arcgis.py` | ArcGIS REST layer query, GeoJSON, resultOffset paging; municipal hosts via allow_host() |
| 950 | `geo_connectors/mcp_server.py` | stdio MCP server: search_stac_satellite, query_usgs_lidar, sample_usgs_elevation, wayback_cdx_diff, arcgis_query |
| 960 | `geo_connectors/verify_connectors.py` | Live health check of all 5 endpoints; writes out/health.json and status=PASS|FAIL to $GITHUB_OUTPUT (used by aegis-health-check) |
| 970 | `geo_connectors/run_sectors.py` | Sector pipeline from a case config: cloud-filtered STAC, COG ΔNDVI, 3DEP centre elevation (used by aegis-sar-runner) |

| 980 | `geo_connectors/hyp3.py` | ASF HyP3 Sentinel-1 InSAR: finds same-track, same-frame interferometric pairs and submits them to ASF's free cloud processing (8000 credits/month). Earthdata login from env or `~/.netrc`, never argv |

IDs are permanent. Never reuse a retired number. A child ID such as 910 runs its parent's tests (900).

## Offline vs. live
- **Offline is the default.** Connector tests replay responses recorded from the real endpoints on 2026-10-21, kept in `geo_connectors/fixtures/`. The recording used a neutral bbox in the Nebraska Sandhills, not a case area.
- **HyP3 / ASF fixture:** `geo_connectors/fixtures/asf_slc_search.json` was recorded live on 2026-10-24 from the ASF search API over the same neutral Nebraska Sandhills bbox. Searching ASF needs no credentials; only submitting jobs does.
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
