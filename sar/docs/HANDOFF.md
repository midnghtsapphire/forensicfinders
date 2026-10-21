# HANDOFF: taking over the SAR toolchain

Everything here is based on what actually ran on 2026-10-21. Where something was only claimed, it says so.

## 1. Mental model
- `sar/` is a set of separate Python components. Each has a number in `registry.json`.
- Nothing invents data. A missing input yields `no_data` or an error. If you see a number, a component computed it from inputs you can inspect.
- Targets are **computed and saved with their inputs**, never typed in. The notebook's target files were typed coordinates; see section 6.
- No component calls an LLM. If you ever add one, it must be optional, gated (`SAR_LLM_ENABLE=1`), and pointed at a small local model through an OpenAI-compatible `SAR_LLM_BASE_URL`, such as Ollama at `http://localhost:11434/v1`.

## 2. First hour, step by step
1. `git checkout sar-consolidation`, then `cd sar`.
2. `python3 registry.py`: read the table and note the IDs you care about.
3. `python3 registry.py --test-all`: expect `ALL OK`. If a block fails, see section 7.
4. Try a live connector against a neutral area:
   ```bash
   python3 -c "from geo_connectors import dep3; print(dep3.sample_elevations([(-100.48, 41.02)]))"
   ```
   Expect roughly 817 m.
5. Try the MCP server:
   ```bash
   printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 -m geo_connectors.mcp_server
   ```
   To wire it into an MCP client, set command `python3`, args `["-m", "geo_connectors.mcp_server"]` and cwd `sar/`.

## 3. Running each component
| ID | Offline | Live / real use |
|---|---|---|
| 100–150 | `python3 registry.py 100 --test` | See `blue-ocean-sar/README.md`. 140: `python3 blue-ocean-sar/public_records_engine.py "<public address>"` (Census only) |
| 200 | `python3 registry.py 200 --test` | `python3 -m hfmr --help`, run from `sar/` |
| 300–600 | `python3 registry.py <id> --test` | Each folder's README |
| 700 | `python3 registry.py 700 --test` (needs fastapi and pytest) | `cd sar && uvicorn coldtrace.backend.main:app`. Without `OPENTOPOGRAPHY_API_KEY` or Sentinel Hub keys, data routes return HTTP 424 `{"status":"no_data"}` by design |
| 800 | `python3 registry.py 800 --test` | Supply a **sourced** LPB table. The shipped example is marked unverified and refused unless `allow_unverified=True` |
| 810 | `python3 registry.py 810 --test` | `instrument_input.read_points("scan.las")` needs `pip install laspy lazrs`; CSV works without it |
| 820 | `python3 registry.py 820 --test` | `EXIFAnalyzer().analyze("photo.jpg")` |
| 900–950 | `python3 registry.py 900 --test` | `SAR_LIVE_TESTS=1 python3 -m unittest -v geo_connectors.test_geo_connectors.Live` |

### Connector cookbook (900s)
```python
from geo_connectors import stac, dep3, wayback, arcgis, netio
bbox = [-100.50, 41.00, -100.45, 41.05]          # synthetic sector
s2 = stac.search(bbox, "2025-06-01/2025-06-30", ["sentinel-2-l2a"], max_items=5,
                 query={"eo:cloud_cover": {"lt": 20}})
red = stac.read_cog_window(s2[0]["assets"]["red"], bbox)
nir = stac.read_cog_window(s2[0]["assets"]["nir"], bbox)
ndvi = stac.ndvi(red, nir)                       # ΔNDVI: stac.delta_ndvi(r0, n0, r1, n1)
s1 = stac.search(bbox, "2025-06-01/2025-06-30", ["sentinel-1-grd"])  # change: stac.log_ratio_db(before, after)
hls = stac.search(bbox, "2025-06-01/2025-06-30", ["HLSS30_2.0"], endpoint=stac.CMR_LPCLOUD)
dtm = dep3.export_dtm(bbox, size=(256, 256), out_path="/tmp/dtm.tif")
snaps = wayback.digest_changes(wayback.query_cdx("example.com", 2006, 2010))
netio.allow_host("gis.example-city.gov")         # municipal servers must be allowlisted first
fc = arcgis.query_layer("https://gis.example-city.gov/arcgis/rest/services/X/FeatureServer/0", where="1=1")
```
Every call retries 429, 5xx and network errors with exponential backoff (1, 2, 4, 8 s plus jitter), then raises `ConnectorError`. Nothing is faked on failure.

### Health check and sector run (960, 970)
Health check against the live endpoints:
```bash
cd sar
python3 -m geo_connectors.verify_connectors --out out/health.json
```
It prints `status=PASS|FAIL`; add `--skip wayback_cdx` if your network blocks archive.org.

Sector run on the synthetic sectors:
```bash
python3 -m geo_connectors.run_sectors --config case/example.config.yaml --out-dir out
```
On 2026-10-21 this found 3 before and 3 after Sentinel-2 scenes per sector. Mean NDVI was about 0.40 → 0.71 (SECTOR-A) and 0.31 → 0.55 (SECTOR-B), May → June green-up. ΔNDVI values are computed, not typed.

### In GitHub
1. Go to Actions → **daily_sar_run** → Run workflow.
2. Leave the config as the synthetic template; real case configs aren't in the repo.
3. Download the `sar-run-<id>` artifact, which holds `health.json` and `<case>_sectors.json`.
4. If the health status is `FAIL`, the sector step is skipped. Open `health.json` to see which endpoint failed.

## 4. Adding a case privately
1. `cp case/example.config.yaml case/<case-id>.config.yaml`. Git ignores everything in `case/` except the template and the README; confirm with `git check-ignore -v case/<case-id>.config.yaml`.
2. Fill in `authority`: the agency, the case or report number, and who authorised the work.
3. Run the components with that config's bboxes and dates. Write outputs into `case/` too.
4. Before any commit, run `git status` and make sure nothing under `case/` shows up.
5. The long-term home for real case configs and outputs is the private **case-files** repo. Don't push there without Audrey's approval.
6. Never put real names, coordinates or case material in code, tests, fixtures, examples or docs.

## 5. Adding a component
1. Copy in working code as-is, and run its tests where it came from first.
2. Add an entry to `registry.json` with the next free number in the right hundred, plus `test_cwd`, `test` and `source`.
3. Add fixture-based offline tests. Optional live tests must skip unless `SAR_LIVE_TESTS=1`.
4. Run `python3 registry.py --test-all`, then add a row to the PR's provenance table.

## 6. What's real vs. aspirational
**Real (ran on 2026-10-21):**
- **Element84 Earth Search STAC:** Sentinel-2 L2A and Sentinel-1 GRD search, paging.
- **NASA CMR-STAC LPCLOUD:** HLS search.
- **COG band math:** live windowed reads of the S2 red and NIR bands through rasterio, giving NDVI. ΔNDVI, S1 log-ratio and sigma anomalies are covered by unit tests.
- **USGS 3DEP:** exportImage returns a real GeoTIFF; getSamples returns elevations.
- **ArcGIS REST:** query with paging (Esri sample server).
- **Wayback CDX:** live API confirmed and fixture recorded. The box's own network couldn't complete TLS to web.archive.org; GitHub runners should work.
- **MCP server:** stdio, 5 tools.

**Rebuilt in the sar-make-it-work PR (1000-series):** decay kinetics, soil N, the void detector, Gi*, dielectric/GPR math, the reliability scorer and qPCR QC. See section 9.

**Aspirational or fake in the Gemini Notebook bootstrap (`master_unified_sar_bootstrap.py`, v4.0.0 "PRODUCTION"):**
- **STAC search:** a bug (bare dates give HTTP 400) made it *always* fall back to a hard-coded fake scene, `S2A_MSIL2A_20261015T…`. It still reported success.
- **3DEP:** made no request at all. It returned `"status": "Active"` and `"smrf_filter": "Applied (Canopy Removed)"` as constants.
- **ArcGIS and Wayback:** returned typed "simulated" rows, including invented digests `SHA1_ORIGINAL_HASH_001/002`.
- **Targets:** the "targets" were typed coordinates with typed confidences (0.84–0.965). Nothing computed them.
- **Taphonomic kinetics:** `calculate_decay_kinetics` uses constants with no source.
- **Admiralty scorer:** maps the type of source to an A–F grade by keyword; it's an opinion, not the NATO procedure.
- **Missing files:** "camera telemetry" (now built as 1910), "self-healing listener", `verify_connectors.py`, `config.yaml`, `docker-compose.yml`, `.env.example`, `sar_pipeline.yml` and the MCP schemas were **not in the zip**. A "v2" package with a daily `verify_connectors.yml` wasn't in it either.
- **`run_county.py`:** generates its DEM with `np.random.normal`.

## 7. Troubleshooting (all hit for real)
| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: numpy/fastapi/rasterio/piexif` | Install the step-2 dependencies. Debian's system pip needs `--user --break-system-packages` |
| Test runs hang or fail inside a venv lacking numpy | Use the same interpreter you installed into: `which python3` |
| `test_geo_connectors` fails to import, or stdlib `http` breaks | A module named `http.py` shadowed the stdlib. It's now `netio.py`; don't add files named like stdlib modules |
| STAC HTTP 400 | Use full RFC 3339 dates; `stac.normalize_datetime` does this for you |
| Wayback `TLS connect error … unexpected eof` | Network or egress problem on that machine, not the code. Try another network or a GitHub runner |
| coldtrace `Status code 204 must not have a response body` | Fixed: `response_class=Response, response_model=None` |
| coldtrace returns 424 `no_data` | Expected when no API keys are set; add keys to `.env` |
| `node --experimental-strip-types` unsupported (CLE repo) | Use Node 22 or newer: `nvm install 22`. If `NPM_CONFIG_PREFIX` is set, unset it first |
| Health-check step shows no `status` output | Fixed: `verify_connectors` appends `status=…` to `$GITHUB_OUTPUT`; the action writes `FAIL` if the script died first |
| Outputs missing at `/workspace/out` | Paths are now relative: `${{ github.workspace }}/out` in CI, `sar/out` locally |
| `ConnectorError: host not allowlisted` | `netio.allow_host("your.gis.host")` |

## 9. Forensic models (1000-series, added in the sar-make-it-work PR)
**Rule:** every constant lives in `forensic_models/constants.json` with a DOI or URL. Anything with no defensible published value is `user_required`. The code refuses to run until you supply it with a source:
```python
from forensic_models import constants, gpr_dielectric as gd
c = constants.load(overrides={"eps_soap": {"value": 4.0, "source": "lab measurement, sample #12, 2026-11-02"}})
e = gd.eps_eff(theta=0.25, f_sap=0.3, consts=c)   # ε_soil from Topp (1980) at θ
v = gd.gpr_velocity(e)                            # m/ns
```
| ID | Try it |
|---|---|
| 1010 | `taphonomy.megyesi_add(20)`, `taphonomy.vass_pmi(60, 12, 70, buried=True)`, `taphonomy.topp_eps(0.25)` |
| 1020 | `soil_nitrogen.simulate(...)` needs `k_ammonification` and `k_nitrification` overrides with a source |
| 1100 | `python3 -m forensic_models.void_detector demo`. Then `validate cfg.json` / `run cfg.json --out-dir case/out` with tiles `{"id","dem_path"}` or `{"id","bbox"}` (fetched from 3DEP), optional `baseline_dem_path` (epoch difference), `sign` low/high/both. ROC: `curve labels.csv --png roc.png` (columns `score,label`) |
| 1110 | `gistar.gi_star(grid)`. Verified equal to PySAL `esda.G_Local(star=True)` with queen lattice weights |
| 1200 | `reliability.grade("instrument_record", "original_file_with_hash", "documented", corroborations=2)` gives `A1`. Edit `reliability_rubric.json` and bump `version` to change the house rubric |
| 1300 | `qpcr_qc.qc(qpcr_qc.read_export(open("run.csv").read(), "quantstudio"), "ASSAY", ipc_target="IPC")`. Layouts: `quantstudio`, `biorad_cfx`, or pass your own column map |
| 1900 | Doc only: why the Doppler corrector was dropped |
| 1910–1913 | Public cams, Ring, timeline merger (section 10) |

**Still needs real-world validation:**
- Gi* thresholds against labelled field outcomes.
- The ε_fat value at your antenna frequency.
- A measured ε_soap.
- Site rate constants.
- qPCR acceptance limits against your lab's SOP.
- The house reliability rubric, reviewed with the agency.

The Vass formula and Megyesi regression are published models with wide error bands, not exact clocks.

## 10. Cameras (1910): public feeds, Ring, and the timeline
Install once for Ring: `pip install ring_doorbell`. Run everything from `sar/`. There are no app-level legal gates; the platforms enforce their own access rules.

### Public webcams and traffic cams (1911)
1. List registered sources: `python3 -m cameras.public_cams sources`
2. The registry is `cameras/sources.json` (data-driven). Supported types today: `caltrans_cctv` (Caltrans CWWP2 511 JSON) and `static_list` (your own public snapshot URLs). Add a new Caltrans district by copying an existing entry; no code change.
3. List cameras: `python3 -m cameras.public_cams list caltrans-d03`
4. Filter by distance: `python3 -m cameras.public_cams list caltrans-d03 --near 38.48 -121.51 5`
5. Capture a timestamped frame + metadata JSON (SHA-256):  
   `python3 -m cameras.public_cams snap caltrans-d03 caltrans-3-1 --out-dir out/frames`  
   Repeat with `--repeat 5 --interval 60` for a time series.

### Ring (Audrey's own account) (1912)
1. Copy `cameras/.env.example` and fill `RING_USERNAME` / `RING_PASSWORD` (and `RING_OTP` if Ring asks) for the first login only.
2. List devices: `python3 -m cameras.ring_cam devices`
3. Event history: `python3 -m cameras.ring_cam history "Front Door" --limit 20`
4. Download a recording: `python3 -m cameras.ring_cam download "Front Door" EVENT_ID --out-dir out/ring`
5. On-demand snapshot: `python3 -m cameras.ring_cam snapshot "Front Door" --out-dir out/ring`  
   After the first login, only the token cache at `~/.config/forensicfinders/ring_token.json` (mode 600) is used. Credentials are never printed.

### Frame-to-timeline merger (1913)
```bash
python3 -m cameras.timeline merge out/frames/*.json out/ring/*.json \
  --sectors out/SYNTH-0001_sectors.json --out out/timeline.jsonl
```
Merges public frames, Ring events/recordings/snapshots and satellite scene IDs from `run_sectors` into one sorted JSONL timeline (`t_utc`, `kind`, `source_id`, `label`, optional `lat`/`lon`/`media_path`/`sha256`).

### Tests
`python3 -m unittest cameras.test_cameras` (offline, mocked). Live public snapshot: `SAR_LIVE_TESTS=1 python3 -m unittest cameras.test_cameras.Public.test_live_caltrans_snapshot`. Ring live check needs Audrey's env credentials (not run in CI).

## 11. Research prototypes (2000+)
- `docs/research/PROTOTYPES.md` — every notebook/research idea with status and next small step.
- `docs/research/soil-edna-detection.md` (ID **2000**, PROTOTYPE / RESEARCH) — crawl → walk → run for human then canine soil eDNA / CDI chemistry. Cited papers only; no claimed results. Next step is a spiked-soil panel feeding qPCR QC (1300). Related FSI abstract (paywalled): Hirashima et al. 2022 DOI 10.1016/j.forsciint.2022.111284 (BSA aids soil DNA extraction).
- `docs/research/phone-gpr-addon.md` (ID **2020**, PROTOTYPE) — phone/USB mmWave crawl → low-freq GPR walk → Pi 5/Zero 2 W field host + GPS; logger stub **811**. Closest existing GitHub: `midnghtsapphire/Radar` (benchtop FMCW, not phone).
- `docs/research/vhr-radar-lidar-fusion.md` (ID **2030**, PROTOTYPE)
- `docs/research/INVENTION-DISCLOSURE.md` (ID **2040**, PROTOTYPE) — Evans concepts 2020/811, 2030/980, 2000; prior-art table; **not legal advice**; keep repo private until provisional filed. — VHR SAR + lidar micro-relief; **recommend option B** (two add-ons + shared GeoTIFF/GeoJSON). Maps to 920/910/1100s/1913; crawl stub **980** `sar_pair`. Corrects X-band “penetrates vegetation” myths. No claimed results.
- `docs/research/full-waveform-lidar.md` (**2060**) + `geo_connectors/waveform.py` (**985**); `docs/research/buried-object-detection.md` (**2070**, incl. mmWave scanner limits and a links-only unsolved-case item lookup design).

## 12. ISRID distance rings (800)
- `data/isrid_distances.json`: values transcribed from Koester (2008) *Lost Person Behavior*, dbS Productions, ISBN 978-1-879471-39-9, using the publisher's free excerpts. Every distance row has `n`, `page` and `url`.
- **Coverage is Dementia (1051) only** (p.164 distances in km/mi; p.164–165 elevation, mobility, dispersion, track offset, find location, scenario, survivability). The requested excerpt `2ISRID.pdf` (pp.15–17) describes ISRID's goals and inclusion/exclusion criteria and has **no tables**. Other categories need the printed book; add them with page numbers.
- `lpb.load_isrid()` returns a verified lpb table: `lpb.rings(lpb.profile(t, "human", "dementia", {"ecoregion": "temperate", "terrain": "mountain"}))`. Urban rows ignore terrain. An unlisted category returns no rings, never a made-up radius.
- Before this, `lpb` (800) had only `lpb_table.unverified.example.json` (hand-typed "Koester data", refused by default). `blue-ocean-sar/realdata/lost_person_behavior.py` uses the separate UK 2003 handbook (Perkins et al.) and is unchanged.
- Tests: `cd lpb && python3 -m unittest test_isrid` checks printed values (e.g. temperate mountain p95 8.3 km; urban p75 3.2 km; track offset p95 307 m).

## 13. Optional detector retraining (2110, `vision/`)
Off by default (`--detector none`). Output is **candidates for human review**, never identifications.
Licences: torchvision/torch BSD, OpenCV Apache-2.0. Ultralytics (AGPL) is not used.

1. **Install (optional):** `pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision` then
   `pip install -r vision/requirements-vision.txt`. Without these, the core still runs and the torch/cv2 tests skip.
2. **Stage test items (no case items, no people):** lay out backpacks, jackets, shoes, bags and bright fabric on
   2–3 different sites (grass, leaf litter, scrub). Log each item and its GPS position on a sheet.
3. **Photograph:** fly or walk several passes per site at 2–3 heights or angles and times of day. Save as
   `images/<site>/<flight>/<frame>.jpg`. The site/flight folders are what keep the train/test split leak-free.
   Keep images out of git; record only their SHA-256.
4. **Label:** self-host CVAT or Label Studio on the box. Use one box per item, one class per item type, and the
   same class names everywhere. Two people label a 10% overlap to check agreement. Export **COCO 1.0**.
5. **Train:** `python3 -m vision.detect train --coco labels.json --images images --epochs 10 --out out/vision/model.pt`
   (MobileNetV3 Faster R-CNN, COCO-pretrained, CPU is fine for a few hundred frames). Whole site/flight groups
   are held out for test.
6. **Evaluate:** `python3 -m vision.detect eval --coco labels.json --images images --weights out/vision/model.pt`.
   Report per-class recall and mAP on held-out groups only. Compare with the template baseline and with "no detector".
7. **Run on frames (optional):** `python3 -m vision.detect --detector frcnn --weights out/vision/model.pt
   --classes out/vision/model.classes.json out/frames/*.json`, or the training-free baseline
   `--detector template --template item.png`. Then
   `python3 -m cameras.timeline merge out/frames/*.json out/detections/*.json --out out/timeline.jsonl`.
   Candidates appear as `detector_candidate` with `review_status: unreviewed`.
8. **Tests:** `python3 -m unittest vision.test_vision` (synthetic images generated in the test; one CPU training step).

## 8. Guardrails
- CI is manual only (`sar-tests` and `daily_sar_run`, both workflow_dispatch). There is no schedule and no auto-commit; outputs go to artifacts. The notebook's daily cron and commit-back step were deliberately not carried over.
- Ring credentials are optional env vars or a mode-600 token cache. They are never in the repo and never printed.
- The `case/` contents never get committed here.


## 14. Sources table (2200)

Every DOI or URL cited in `sar/` belongs in `sar/data/sources.json`. After adding a citation:

1. Add a row with `source_id`, `type`, `verified` and `verified_date`, plus a `license` for repos and data.
2. Run `python3 sar/sources.py --render`.
3. Run `python3 sar/sources.py --check`.

`test_sources.py` fails if a cited DOI is missing or SOURCES.md is stale. The placeholder DOIs in `CITATION.cff.template` are excluded.
