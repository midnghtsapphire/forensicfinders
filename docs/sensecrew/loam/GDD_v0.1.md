# GDD v0.1 — "Ground Truth" (working title): sensing-games training sim
**Authors:** Loam-D / Loam-N (Grok Bot), for Audrey Evans · **Lead:** Strata · **Date:** 2026-11-04 20:20 MST (UTC-7) · **Status:** DRAFT for review, local only. Supersedes `GDD_v0.md` (kept unchanged, not deleted).
**Basis:** v0 sources (forensicfinders main @ `a2630989`, read-only) plus six lead rulings dated 2026-11-04. Legend: [READ] checked in a file · [DOI-VERIFIED] resolved via api.crossref.org this session · [UNVERIFIED].

## 0. Changelog vs v0
- R1: the game path uses only Bedrock's seeded synthetic DEM fixtures `fixtures/dem_synthetic_*.tif`; no real DEM anywhere.
- R2: `search_theory.py` is QUARANTINED. Because `optimal_search.py` does `import search_theory as st` (line 66 [READ]) and calls `st.check_poa`, `st.bayes_update`, `st.tasking_table`, `st.read_segments`, `st._is_row`, **optimal_search.py is also out of the game path** (quarantine is transitive). Scoring moves to a Bedrock reimplementation (NEW-01) built from Koopman/Stone and cited by DOI.
- R3: `lpb_mpb2003.json` is blocked. `lost_person_sim.py` imports `lost_person_behavior as lpb` (line 153 [READ]), which loads that table, so lost_person_sim is also out of the game path. It's replaced by a prior-distribution interface (NEW-02) whose placeholders are labelled SYNTHETIC.
- R4: licence. forensicfinders is a private repo; internal use is OK; licence choice pending with Audrey.
- R5: sweep widths come only from cited values supplied by Ledger-Play and the sensor pairs. Uncited cells stay `null` and are flagged.
- R6: new components use registry placeholders NEW-01…NEW-10.

## 1. Vision (unchanged from v0)
An honest ground-detection training sim. The player learns the method: screen → survey → confirm, and POA/POD/POS reasoning. The entertainment skin never changes physics. Per SOIL_SENSING_TIERS.md [READ], "atomic-level" techniques confirm samples; they don't locate buried objects from a distance.

## 2. Core loop
1. **Brief:** seeded synthetic scenario. The terrain is `fixtures/dem_synthetic_<seed>.tif` (Bedrock, NEW-03). The prior POA map comes from the **NEW-02 prior interface** (§2a).
2. **Deploy sensor:** tool, segment, effort (km of track, or h with z = v·t).
3. **Read noisy, honest data:** a seeded Bedrock sensor model with stated uncertainty and modelled false positives.
4. **Update map:** NEW-01 `bayes_update`: POA_i' = POA_i(1−POD_i)/(1−Σ_j POA_j·POD_j), with a never-searched Rest-of-World (ROW) segment.
5. **Search/confirm:** commit effort, dig, or sample (Tier 3).
6. **Score (NEW-01 only):** POD_i = 1−exp(−W_i z_i / A_i) (random-search / exponential detection, Koopman 1956b); POS = Σ POA_i·POD_i; optimum by Lagrange "water-filling", z_i = max(0, ln(POA_i r_i/λ)/r_i) with r_i = W_i/A_i (Koopman 1957; Stone 1975). Game score = player POS ÷ optimal POS on the same seed, plus calibration (Fusion). Missions with a null W can't be scored (§3a).

Units: A km², z km (or h), W km, v km/h, r km⁻¹, POA/POD/POS ∈ [0,1], seed int.

### 2a. NEW-02 prior interface (R3)
`prior(seed:int, scenario:ScenarioSpec, dem:Path) -> PoaRaster{grid, transform, provenance, label}`
- `DistanceDistribution` protocol: `quantiles() -> {p25,p50,p75,p95}` in km, `source`, `label`.
- Ships only `SyntheticPlaceholderDistribution` (for example lognormal, μ and σ set per mission), with `label="SYNTHETIC — not behavioural data"` written into every output and shown in the HUD.
- A real LPB table can plug in later only after a licence ruling (owner Strata). Until then nothing loads `lpb_mpb2003.json`.
- Movement concepts (Tobler hiking speed, correlated random walk) may be reimplemented by Bedrock with a citation. Tobler 1993 is an NCGIA technical report with no DOI [UNVERIFIED].

### 2b. NEW-01 search-theory core (R2): citations
| Ref | Use | DOI | Status |
|---|---|---|---|
| Koopman, B.O. (1956a) The Theory of Search. I. Kinematic Bases. *Operations Research* 4(3) | sweep width, coverage | 10.1287/opre.4.3.324 | DOI-VERIFIED |
| Koopman (1956b) The Theory of Search. II. Target Detection. *Oper. Res.* 4(5) | exponential detection law | 10.1287/opre.4.5.503 | DOI-VERIFIED |
| Koopman (1957) The Theory of Search [III. The Optimum Distribution of Searching Effort]. *Oper. Res.* 5(5) | optimal allocation | 10.1287/opre.5.5.613 | DOI-VERIFIED (Crossref title shows only "The Theory of Search"; the part-III subtitle is UNVERIFIED) |
| Stone, L.D. (1975) *Theory of Optimal Search*. Academic Press, Mathematics in Science and Engineering vol. 118 | KKT / water-filling, Bayesian update | book DOI UNVERIFIED (Crossref returns only a front-matter chapter, 10.1016/s0076-5392(08)60541-x; reviews exist at 10.1137/1019060 and 10.2307/2286890) | UNVERIFIED — cite the book by ISBN once checked |
Clean-room rule: Bedrock implements from these papers. It does not copy or port quarantined code. Golden tests use analytic hand-computed cases from the papers, not search_theory's tests.

## 3. Progression / tech tree (SOIL_SENSING_TIERS.md tiers [READ])
A node unlocks when its learning objective (LO) passes on 3 consecutive seeds. "W source" means a cited sweep-width cell (see §3a).

**Tier 1: Screening**
| Node | Principle | Owner | Measurable LO | Sim source | Licence / W |
|---|---|---|---|---|---|
| 1a LiDAR DEM differencing | DEM difference > level of detection → pit/fill | Waveform | F1 ≥ 0.8 on seeded pits/mounds | `realdata/microtopo.py` (API UNVERIFIED) on `dem_synthetic_*.tif` pairs | PDAL BSD; lasR GPL-3 offline; W: null until cited |
| 1b Full-waveform lidar | Gaussian decomposition | Waveform | ≥90% synthetic returns within ±0.15 m (target UNVERIFIED) | KNOWN GAP → NEW-04; HELIOS++ offline | GPL offline only |
| 1c InSAR | phase/coherence; C-band loses coherence under forest | Fringe | correct sensor choice for a forested segment ≥80% | NEW-05 + `geo_connectors/hyp3.py` (980), synthetic interferograms | MintPy GPL offline; StaMPS don't use |
| 1d SAR/NDVI change | backscatter or NDVI change vs baseline | Backscatter | log-ratio baseline shown beside ML; ROC AUC reported | `sar-change-detection` (300), `s2_change.py` | TorchGeo MIT; SSL4EO CC-BY-4.0 attribute |
| 1e TWI prior | topographic wetness | Aquifer | Spearman ≥0.9 vs WhiteboxTools on `dem_synthetic_*` | `multi_proxy/twi.py` (UNVERIFIED path) | WBT MIT; MERIT don't use |

**Tier 2: Ground survey**
| Node | Principle | Owner | LO | Sim source | Licence / W |
|---|---|---|---|---|---|
| 2a GPR | t = 2d√εr/c | Deepscan + Humus | depth ±10% given εr | `gpr-wave-model/` (500), `instrument_input/` (810) | gprMax GPL offline |
| 2b EMI | eddy currents, metal only | Deepscan | 0 claims of non-metal detection | NEW-06 | dipole-model citation UNVERIFIED |
| 2c Ground gamma | K/Th/U → soil context | Isotope | applies gamma context to GPR velocity; never used as a detector | NEW-07 (Poisson counts) | sensing depth UNVERIFIED |
| 2d Soil dielectric | Topp εr(θ) | Humus | εr within stated uncertainty | `multi_proxy/dielectric.py` (UNVERIFIED), `sensor-fusion-grid` (400) | LUCAS internal only |
| 2e Fusion | consensus + calibrated uncertainty | Fusion | Brier score better than the best single sensor | `sensor-fusion-grid` | PyOD/HDBSCAN BSD; TerraMind UNVERIFIED |

**Tier 3: Sample analysis**
| Node | Principle | Owner | LO | Sim source | Licence |
|---|---|---|---|---|---|
| 3a soil_dna_sensor qPCR | LOD95/LOQ | Humus | calls a result below LOD95 "inconclusive" | `qpcr_assay.py`, `qpcr_interpret.py` | synthetic curves |
| 3b GC-MS / 16S | VOC peaks / community shift | Humus + Chitin | flags a signature vs baseline | `lab_readers.py` | synthetic exports |
| 3c LIBS | elemental lines, sample in hand | Isotope | element ID; knows it can't locate | NEW-08 | line database citation UNVERIFIED |
| 3d Taphonomy / insect | degree-days | Chitin | interval brackets truth; non-graphic | NEW-09 | literature UNVERIFIED |

### 3a. Sweep-width table (R5)
`fixtures/sweep_width_cited_synthetic.json` (NEW-10, owners Ledger-Play + sensor pairs). Schema per cell: `{resource, target, vegetation, visibility, W_km|null, source_doi_or_url|null, supplied_by, flag}`.
- Any cell without a source stays `W_km: null`, `flag: "UNCITED — not scorable"`.
- No defaults, interpolation or guesses. NEW-01 refuses to score a segment whose W is null and says why in the HUD.
- `realdata/sweep_width.py` (which doesn't import search_theory [READ]) is a design reference for the canopy model W_eff = W_open(1−cover)^k. Reuse needs a Strata check because its output targets the quarantined CSV format.

## 4. First 3 synthetic missions (seeded; synthetic fixtures only)
- **M1 "Water-filling" (seed 1001):** 4 segments + ROW on `dem_synthetic_1001.tif`; POA from a NEW-02 SYNTHETIC placeholder; 10 km budget. Score with NEW-01 against the optimum and naive plans. LO: ≥90% of optimal POS. **Gate:** needs ≥1 cited W cell; otherwise M1 runs in "coverage-only" mode, with the player choosing coverage C directly and no W (honest, scorable without W).
- **M2 "Pit or mound" (seed 1002):** `dem_synthetic_1002a/b.tif` pair; node 1a; then one NEW-01 Bayesian update. LO: F1 ≥0.8, and the POA update matches the analytic value to 1e-9.
- **M3 "Screen, survey, confirm" (seed 1003):** `dem_synthetic_1003.tif`; 1a → 2a → 3a. Segment polygons are procedurally generated by Bedrock (the v0 plan to use `caltopo_export_synthetic.json` is dropped as unnecessary). LO: within budget, correct tier order, no over-claiming.
Every run writes `seeds.jsonl` plus output sha256 for byte-identical replay.

## 5. Two-phase plan
**Phase 1 (core, headless):** NEW-03 DEM fixtures → NEW-01 search core (failing analytic tests written first by the Navigator) → NEW-02 prior → M1–M3 via `python -m sensegame.sim`. Golden tests: NEW-01 analytic cases + Verity determinism + an existing-suite run for the reused modules (`registry.py <id> --test`).
**Phase 2 (polish):** Godot 4 + gdext v0.5.5 thin client; Pixel Lantern; Quill briefings; Ledger-Play seeded sweeps (≤100).

## 6. Manual run (proposed; Makefile doesn't exist yet)
```
make dem SEED=1001          # python -m sensegame.dem --seed 1001 --out fixtures/dem_synthetic_1001.tif
make sim MISSION=M1 SEED=1001
make score RUN=out/M1_1001  # python -m sensegame.search_core score ...   (NEW-01; no search_theory/optimal_search)
make determinism SEED=1001  # run twice, compare sha256
make test
godot --headless --path game/ -s tests/run.gd   # phase 2
```

## 7. Licence & registry
- forensicfinders: private repo; internal use OK. **Licence choice pending with Audrey.** Nothing ships externally until it's decided.
- Placeholders: NEW-01 search-theory core · NEW-02 prior interface · NEW-03 synthetic DEM fixtures · NEW-04 full-waveform lidar · NEW-05 InSAR SBAS · NEW-06 EMI · NEW-07 atomic-molecular (gamma) · NEW-08 LIBS reader · NEW-09 taphonomy/insect · NEW-10 cited sweep-width table. Strata assigns real numbers.

## 8. Open questions
1. The Stone 1975 book DOI/ISBN needs verification; Koopman 1957 subtitle unverified.
2. Should `sweep_width.py` (no search_theory import, but writes its CSV format) stay as a reference only or be reused? Strata/Verity.
3. Can `microtopo.py`, `gpr-wave-model` and the Tier-3 modules be reused? Owners must confirm they have no transitive import of search_theory or lpb (only optimal_search and lost_person_sim were checked [READ]).
4. GeoTIFF writer for NEW-03: rasterio/GDAL licence check (expected permissive, UNVERIFIED).
5. Tobler 1993 has no DOI; acceptable as a technical-report citation?

## 9. Loam-N review (v0.1)
- **R1:** every DEM reference is `dem_synthetic_*.tif`; the v0 real-DEM `--dem` path is gone ✔.
- **R2:** no call into search_theory remains. I caught the transitive import in `optimal_search.py`, which v0 missed (v0 scored via `evaluate_plan`/`compare_plans`); that's a v0 defect, now fixed ✔. Formulas are restated with DOIs; 3 of 4 refs are DOI-VERIFIED and the Stone book is honestly marked UNVERIFIED ✔.
- **R3:** lost_person_sim is out (its lpb import was found); placeholders are labelled SYNTHETIC in outputs and the HUD ✔.
- **R4 ✔, R5:** null-W cells are unscorable, with an honest coverage-only fallback for M1; no guessed numbers ✔. **R6 ✔.**
- **Units:** r km⁻¹ · z km → dimensionless exponent ✔; GPR ✔.
- **Hard rules:** R3 determinism (sha256) ✔, R4 CLI ✔, R5/R6 licences ✔, R7 forbidden paths untouched, soil_dna_sensor naming ✔, R8 nothing committed ✔.
- **Residual:** module-reuse transitive checks (Q3) must be done before Phase 1 code. That's acceptable for a design doc.

Loam-N APPROVE
