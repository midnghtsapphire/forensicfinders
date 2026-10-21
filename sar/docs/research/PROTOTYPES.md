# Prototype / research ideas index

Status meanings:
- **SHIPPED** — working code with tests in this repo
- **PROTOTYPE / RESEARCH** — written plan or early code; no claimed field results
- **EVALUATED OUT** — looked at and intentionally not built (see linked note)
- **IDEA** — named only; no work yet

| Idea | Status | Registry | Next small step |
|---|---|---|---|
| Live geo connectors (STAC, 3DEP, Wayback, ArcGIS, MCP) | SHIPPED | 900–970 | Re-record any city-scale fixtures on a neutral bbox |
| Sourced taphonomy / dielectric / Gi* void detector / Admiralty table / qPCR QC | SHIPPED | 1000–1300 | Field-label a DEM for Gi* ROC (`void_detector curve`) |
| Public traffic cams + Ring (own account) + timeline merger | SHIPPED | 1910–1913 | Live Ring login with Audrey's token cache; add more public DOT sources to `cameras/sources.json` |
| Soil human (then canine) eDNA / CDI chemistry → portable kits → remote proxies | PROTOTYPE / RESEARCH | 2000 | `docs/research/soil-edna-detection.md` crawl: spiked-soil panel + published mtDNA assay + 1300 QC |
| Phone-attached GPR / mmWave / UWB sensor (+ Pi field host) | PROTOTYPE / RESEARCH | 2020 / 811 | Buy one raw-export kit; Pi 5/Zero 2 W host + GPS logger (`pi_radar_logger`); three labelled wall/paver scenes; see `phone-gpr-addon.md`. Closest GitHub: `midnghtsapphire/Radar` (benchtop FMCW, not phone) |
| VHR SAR change + lidar micro-relief (two add-ons, shared interchange) | PROTOTYPE / RESEARCH | 2030 | `docs/research/vhr-radar-lidar-fusion.md`; crawl: S1 pair via 910 + `sar_pair` 980 + 3DEP/Gi*; recommend option B |
| Invention disclosure (phone/Pi radar; VHR SAR+lidar add-ons; soil eDNA human→canine) | PROTOTYPE / RESEARCH | 2040 | `docs/research/INVENTION-DISCLOSURE.md`; keep private; provisional ~$65 micro-entity (verify uspto.gov); USPTO pro bono or attorney |
| Full-waveform lidar ground under canopy (GEDI L1B/L2A, NEON AOP) | PROTOTYPE / RESEARCH | 2060 / 985 | `docs/research/full-waveform-lidar.md`; run `waveform` 985 on a few L1B shots, compare with L2A ground and 3DEP (920) |
| Small buried/surface personal items (zippers, rivets, buttons, fabric, soles) | PROTOTYPE / RESEARCH | 2070 | `docs/research/buried-object-detection.md`; metal-detector test strip at 0–20 cm with GPS log, then magnetometer + GPR |
| Clandestine grave detection: literature + phased workflow (priors → NDVI → lidar Gi* → thermal → GPR/ER) | PROTOTYPE / RESEARCH | 2080 | `docs/research/clandestine-grave-detection.md`; next: a thermal ingest stub and an ER/conductivity record format; PermitStack disturbance-date lookup is an idea only |
| Ported search-system (ranking, county runner, assay QC, evidence log, fall physics) | PROTOTYPE | 1400–1450 / 2090 | `search_system/README.md` audit; next: run VALIDATION_PROTOCOL on ≥20 resolved cases (offline, case-files repo); merge Gi*/void/qPCR overlap with 1110/1100/1300 |
| Optional vision detection on camera/drone frames (template → small YOLO; OTVision tracking) | PROTOTYPE / RESEARCH | 2100 | `docs/research/vision-detection-tools.md`; next: OpenCV template-match stub behind `--detector` (default none) on 1911 frames |
| Notebook Doppler / SDR corrector | EVALUATED OUT | 1900 | Keep out of SAR; if wanted later, rebuild on SGP4/TLE in a radio-tools repo |
| Notebook "camera telemetry" as vendor ALPR scrape | EVALUATED OUT | — | Replaced by 1910 public feeds + own Ring |
| Notebook hard-coded STAC/3DEP/Wayback/ArcGIS + typed targets | EVALUATED OUT | — | Replaced by 900-series |
| Mine-alias NLP triage from notebook `run_county` layer 1 | IDEA | — | Only if a sourced place gazetteer exists; no case-named alias tables |
| Satellite-only "grave detector" | IDEA / speculative | — | Needs labelled training data; see 2000 Run section |
| Canine eDNA field kit | IDEA | — | After human soil assay validates (2000) |
| Hyperspectral / thermal flight add-on | IDEA | — | Collect labelled overflight data; do not score without ground samples |

Sources for research rows are only those cited inside the linked notes. Nothing here claims a detection result.
