# GDD v0 — "Ground Truth" (working title): sensing-games training sim
**Authors:** Loam-D (driver) / Loam-N (navigator), Grok Bot, for Audrey Evans · **Lead:** Strata · **Date:** 2026-11-04 20:15 MST (UTC-7) · **Status:** DRAFT for review, local only (not committed/pushed)
**Sources read this session (read-only, `gh api`, forensicfinders main @ `a2630989a8bc4971a8ed8efe9038783701810869`):**
`sar/docs/SOIL_SENSING_TIERS.md`, `sar/registry.json`, `sar/blue-ocean-sar/realdata/{lost_person_sim,optimal_search,sweep_width,search_theory}.py` (docstrings + signatures; not every line), `realdata/test_{lost_person_sim,optimal_search,sweep_width,search_theory}.py` (grep only), revvel-standards `standards/LEDGER_STANDARD.md`.
**Not opened (rule 7):** case/, hfmr/, dossier.py, evidence/, public_records_engine.py. Registry ids 110/140/200/990 were seen only as registry entries and are excluded from the game.
**Legend:** [READ] = checked in a file this session · [UNVERIFIED] = assumption or not yet checked.

## 1. Vision
A training simulator that teaches how ground-detection search actually works: every sensor has limits, every reading is noisy, and probability, not certainty, decides where to search. The player gets better at the method (screen → survey → confirm, POA/POD/POS reasoning), not at beating made-up mechanics. The entertainment skin (art, narrative by Quill) sits on top and never changes the science (Pixel Lantern: exaggeration labelled).
Non-goals: real cases, real people, PII, forensic casework, or any claim that a sensor sees what it physically can't. SOIL_SENSING_TIERS.md [READ] says it plainly: "atomic-level" techniques (LIBS, gamma, nanosensors) are confirmation tools and "none of them locate a buried object from a distance". The game must teach that.

## 2. Core loop (training sim first)
1. **Brief:** a seeded synthetic scenario. The prior POA map comes from `lost_person_sim.py simulate` (agent-based Monte Carlo, Tobler speed, LPB-calibrated) [READ] **or**, for buried-target missions, from a seeded procedural prior (Bedrock). See blocker B1.
2. **Deploy sensor:** choose a tool from the unlocked tier, the segment, and the effort (track km or hours). The budget is in km of track (`optimal_search` unit="km", or hours with z = v·t [READ]).
3. **Read noisy, honest data:** Bedrock returns a seeded synthetic reading from that sensor's physics model, plus its stated uncertainty. False positives (clutter, roots, metal trash) are part of the model.
4. **Update the probability map:** after an unsuccessful pass, `search_theory.bayes_update` [READ]: POA_i' = POA_i(1−POD_i)/(1−ΣPOS), with a Rest-of-World (ROW) segment that is never searched. Raster variant: `lost_person_sim.py update` [READ].
5. **Search/confirm:** commit effort, dig, or sample (Tier 3).
6. **Score:** use the existing modules only. `search_theory.coverage_pod` (POD = 1−exp(−C), C = W·TTL/A) [READ]; `optimal_search.evaluate_plan` / `compare_plans` give the player's POS against the Koopman/Stone optimum and naive plans (`optimal_gain`) [READ]; `sweep_width.py` supplies W with a source on every number. Its built-in table is "mostly null", so W must come from calibration or a cited value [READ]. **No scoring is rebuilt.** Game score = player POS ÷ optimal POS from the same seed, plus a calibration score (how well stated confidence matched outcomes; Fusion owns the method) [UNVERIFIED design].

Units contract (Loam-N): area km², track km, W km, speed km/h, effort km or h, POA/POD/POS dimensionless in [0,1], seed int.

## 3. Progression / tech tree (from SOIL_SENSING_TIERS.md three tiers [READ])
Unlock rule: a node unlocks when its learning objective (LO) passes on 3 consecutive seeds.

### Tier 1: Screening (where to look; wide area, remote)
| Node | Real principle | Owner | Measurable LO | Sim source | Licence notes |
|---|---|---|---|---|---|
| 1a LiDAR DEM differencing (M-TMAT) | Two bare-earth DEMs differenced; change > level-of-detection is classed `excavation_pit` / `fill_mound`; penetrates canopy | Waveform | Player picks the LoD threshold; F1 ≥ 0.8 on seeded synthetic pits/mounds | `realdata/microtopo.py` (named in TIERS doc; **file not opened** [UNVERIFIED API]) | PDAL BSD. lasR is GPL-3 (flagged in TIERS): offline only per rule 5 |
| 1b Full-waveform lidar | Gaussian decomposition of return waveform | Waveform | Recover ≥90% of synthetic returns within ±0.15 m [UNVERIFIED target] | **KNOWN GAP**: module doesn't exist; HELIOS++ offline generator | HELIOS++ GPL mode: offline CLI only |
| 1c InSAR | Phase/coherence deformation; C-band fails under forest canopy (TIERS) | Fringe | Player explains a coherence loss; picks the right sensor for a forested segment ≥80% of the time | `geo_connectors/hyp3.py` (registry 980 [READ]); new insar component | Dolphin/ISCE3 permissive; MintPy GPL offline; StaMPS don't use |
| 1d SAR/NDVI change | Backscatter or NDVI change vs baseline | Backscatter | Log-ratio baseline always reported beside ML; ROC AUC is shown to the player | `realdata/s2_change.py` (TIERS) and `sar-change-detection` (registry 300 [READ]) | TorchGeo MIT; SSL4EO CC-BY-4.0 data: attribute |
| 1e Hydrology prior (TWI) | Water/plume pathways shape where material moves | Aquifer | Rank segments by TWI to match the oracle (Spearman ≥0.9) | `multi_proxy/twi.py` [UNVERIFIED path] vs WhiteboxTools | WBT MIT; MODFLOW PD; MERIT NC: don't use |

### Tier 2: Ground survey (metres, on foot)
| Node | Principle | Owner | LO | Sim source | Licence |
|---|---|---|---|---|---|
| 2a GPR | Dielectric contrast; two-way travel time t = 2d·√εr / c | Deepscan + Humus (εr) | Depth estimate within ±10% given εr; picks a hyperbola apex | `gpr-wave-model/` (registry 500 [READ]); `instrument_input/` GPR CSV (810 [READ]) | gprMax GPL-3: offline B-scan library only |
| 2b Magnetic induction / EMI | Eddy-current response, **metal only** | Deepscan | Player never claims EMI detects non-metal targets (0 errors); clears metal clutter | **Missing** ("ranked #1 missing" in TIERS): new component, number from Strata | analytic, cite dipole model [UNVERIFIED source] |
| 2c Ground gamma | K-40/Th-232/U-238 → soil texture/moisture **context**, not detection | Isotope | Uses gamma context to correct GPR velocity; doesn't use gamma as a detector | new atomic-molecular component (Poisson counts) | constants need URL/DOI; sensing depth **unverified** (TIERS says so) |
| 2d Soil dielectric/moisture | εr from moisture (Topp) | Humus | Predicts εr within stated uncertainty | `multi_proxy/dielectric.py` [UNVERIFIED path]; `sensor-fusion-grid` (400 [READ]) | OSSL MIT models; LUCAS internal only (rule 6) |
| 2e Fusion | Multi-sensor consensus + calibrated uncertainty | Fusion | Brier score improves over best single sensor | `sensor-fusion-grid/`, consensus.py [UNVERIFIED] | PyOD/HDBSCAN BSD; TerraMind licence unverified |

### Tier 3: Sample analysis (what is it; sample in hand)
| Node | Principle | Owner | LO | Sim source | Licence |
|---|---|---|---|---|---|
| 3a soil_dna_sensor qPCR | Cq vs copies; LOD95/LOQ | Humus | Correctly calls results below LOD95 "not detected / inconclusive" | `realdata/qpcr_assay.py`, `qpcr_interpret.py` (TIERS) | synthetic logistic curves only |
| 3b GC-MS / 16S | VOC peaks; community shift | Humus + Chitin | Reads a synthetic TIC; flags a decay-VOC signature against a baseline | `realdata/lab_readers.py` (TIERS) | synthetic exports only |
| 3c LIBS | Elemental lines at the laser spot; needs the sample | Isotope | Identifies elements from synthetic spectra; knows it can't locate anything | **Missing** (LIBS reader, TIERS #2) | analytic sim; cite line database [UNVERIFIED] |
| 3d Insect trace / taphonomy | Degree-day development | Chitin | Interval estimate brackets the truth on seeded runs; non-graphic | new component | cited literature [UNVERIFIED] |

## 4. First 3 synthetic training missions (all seeded; fixtures/*synthetic* only)
Fixtures that match `fixtures/*synthetic*` [READ in tree]: `realdata/fixtures/caltopo_export_synthetic.json`, `realdata/fixtures/nwis_iv_synthetic_okanogan.json` (contents **not opened** [UNVERIFIED]).
- **M1 "Water-filling" (seed 1001):** pure search theory. 4 segments + ROW, segments CSV generated from seed (POA, area_km2, sweep_width_km from a cited W). Player allocates 10 km of track. Score: `optimal_search.compare_plans`. LO: reach ≥90% of optimal POS, and explain why the highest-POA segment isn't always fully funded. Uses no sensor; teaches POD/POS.
- **M2 "Pit or mound" (seed 1002):** Tier-1 node 1a on a procedurally generated synthetic DEM pair (Bedrock seed). Then Bayesian update after one unsuccessful pass. LO: F1 ≥0.8, plus a correct POA update (matches `bayes_update` to 1e-6).
- **M3 "Screen, survey, confirm" (seed 1003):** segment geometry seeded from `caltopo_export_synthetic.json` [UNVERIFIED that it has polygons]. Tier 1 (1a) → Tier 2 (2a GPR, analytic) → one Tier-3 sample (3a qPCR, synthetic). LO: total effort ≤ budget; correct tier order; no over-claimed detection.
The seed log (`seeds.jsonl`) replays every mission byte-for-byte (rule 3).

## 5. Two-phase plan (ChatDev GameDev style)
**Phase 1 (core, headless):** Bedrock `python -m sensegame.sim --mission M1 --seed 1001` wraps the existing modules (extends them, doesn't replace them). Golden tests: the existing realdata `test_*.py` plus new determinism tests (Verity). Navigator writes the failing test first. No Godot yet.
**Phase 2 (polish):** Godot 4 + gdext v0.5.5 thin client renders core outputs only; Pixel Lantern palettes and a11y; Quill briefings; Ledger-Play tunes cost/time with seeded sweeps (≤100 agents), never physics.

## 6. Manual run notes (rule 4) [proposed; Makefile doesn't exist yet]
```
make sim MISSION=M1 SEED=1001      # -> python -m sensegame.sim --mission M1 --seed 1001 --out out/M1_1001
make score RUN=out/M1_1001         # -> python sar/blue-ocean-sar/realdata/optimal_search.py <segments.csv> ... (CLI flags UNVERIFIED)
make determinism SEED=1001         # run twice, sha256 compare
make test                          # python3 sar/registry.py <id> --test  (registry _doc [READ]) for 130 + new ids
godot --headless --path game/ -s tests/run.gd   # phase 2
```
Existing CLIs [READ]: `search_theory.py segments.csv [--passes passes.csv] --out result.json`; `lost_person_sim.py simulate --lat --lon --category --hours --dem --out --seed ...` and `lost_person_sim.py update`.

## 7. Open questions / blockers
- **B1:** `lost_person_sim.py` CLI requires a real `--dem`. `synthetic_flat_terrain` is "for tests only; the CLI never uses this" [READ]. A game prior needs either a sanctioned synthetic-DEM path (extend the module, with owner approval) or a synthetic GeoTIFF fixture named `*synthetic*`. Decision needed from Strata.
- **B2:** the `search_theory.py` docstring says it was built from `docs/case-files/general/wisar_*` workbook/checklist [READ]. Those are generic WiSAR materials, not a case, but they sit under a "case-files" path. Verity/Strata must rule whether importing this module conflicts with rule 7 ("case-files"). Until then: **flag, don't ship**.
- **B3:** `lost_person_sim` depends on `lost_person_behavior.py` / `lpb_mpb2003.json` (Perkins/Roberts/Feeney 2003) [READ in docstring]. Table licence and redistributability are unverified.
- Q4: `sweep_width_tables.json` is mostly null [READ]. Which cited W values may the game use for synthetic missions?
- Q5: microtopo.py, s2_change.py, qpcr_assay.py, lab_readers.py, multi_proxy/* APIs weren't opened. Owning pairs should confirm.
- Q6: registry ids for new components (EMI, LIBS, atomic-molecular, full-waveform, sensegame core): Strata to assign.
- Q7: forensicfinders repo licence: the API returned no SPDX id [READ: blank]. Shipping terms are unknown.

## 8. Loam-N review
- **Units:** consistent km/km²/h; GPR formula t = 2d√εr/c is dimensionally correct (d m, c m/s → s). 1b's ±0.15 m and other LO thresholds are design targets marked UNVERIFIED. OK.
- **Citations:** every repo claim is tagged [READ] or [UNVERIFIED]; module APIs not opened are flagged. External science constants (EMI dipole, LIBS lines, degree-day) lack DOIs. That's acceptable for a GDD; it must be fixed before the science pairs implement.
- **Rule compliance:** R5 GPL tools offline only, no Ultralytics ✔; R6 LUCAS internal ✔; R7 forbidden paths not opened, registry 110/140/200/990 excluded, soil_dna_sensor naming ✔, missions use only *synthetic* fixtures or seeded procedural data ✔; R3 seeds ✔; R4 CLI ✔; R8 nothing committed ✔; R10 reuse-not-rebuild scoring ✔.
- **Open issues blocking a code start (not this doc):** B1 (synthetic DEM path) and B2 (case-files provenance of search_theory) need Strata/Verity rulings. The GDD flags both and doesn't resolve them silently.
- Verdict: the GDD v0 is fit for review as a design document; implementation is gated on B1/B2.

Loam-N APPROVE
