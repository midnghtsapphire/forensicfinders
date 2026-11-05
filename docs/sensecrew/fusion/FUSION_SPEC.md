# FUSION_SPEC v0.2: seeded uncertainty maps over CleanScorer (NEW-01)

Owner: Sense-Fusion (Fusion-D / Fusion-N). Status: **doc-only draft (PR #18), no code, no swarm**. Licence: UNLICENSED (private repo; licence pending Audrey). Base: main `a2630989`.
Registry: **1080 (PROVISIONAL, pending Verity's collision check against `sar/registry.json`)**. Replaces the placeholder used in v0.1.

## 0. Changelog v0.1 → v0.2 (Strata rulings, 2026-11-04)
1. Registry placeholder → **1080 (provisional)** everywhere.
2. Calibration gate: **ECE ≤ 0.05 on synthetic holdouts**. Bootstrap: **B = 1000 seeded resamples**.
3. `realdata/fusion.py` stays **out of the game path**. It is replaced by a clean-room spec (§2), written only from public sources and the Scorer contract. No more of fusion.py's body was read beyond what RULE7_AUDIT.md records, and no quarantined file was opened.
4. The consumer contract is rebuilt against **Bedrock's NEW-01 spec** (`specs/scorer-spec.md`, Bedrock draft 2026-11-04). Diffs vs the Loam GDD contract are in §1a. Bedrock's version governs.
5. TerraTorch stays **ON HOLD**.

## 1. Consumer contract (from Bedrock NEW-01 scorer-spec §1–§5)
```python
# sensegame/search_core.py  (re-exported by ledgerplay/scoring.py as the default Scorer)
@dataclass(frozen=True)
class Segment:
    name: str; area_km2: float; poa: float; w_km: float | None   # None = uncited -> unscorable
    speed_kmh: float | None = None; is_row: bool = False
class ScorerError(ValueError): ...
class UncitedSweepWidth(ScorerError): ...
class CleanScorer:   # stateless, pure, deterministic, stdlib math only
    def pod(self, w_km, track_km, area_km2) -> float            # -expm1(-W z / A)
    def pos(self, segments, effort_km: dict[str, float]) -> float  # fsum POA_i POD_i, ROW = 0
    def optimal(self, segments, budget_km) -> dict[str, float]     # closed-form water-filling, sorted keys
    def update(self, segments, effort_km) -> list[Segment]         # POA_i(1-POD_i)/(1-POS); ROW POA/(1-POS)
```
How fusion uses it:
- Fusion holds a `Scorer` by injection. It calls only these four methods and builds `Segment`s only through the dataclass (never dicts).
- Fusion catches `ScorerError` and `UncitedSweepWidth`, surfaces them to the HUD/debrief, and **never substitutes or imputes** W, POA or effort. It never renormalises POA (Bedrock rejects |ΣPOA−1| > 1e-9).
- Effort passed to the Scorer is km only. If a mission is in hours, fusion converts with `z_km = z_h·speed_kmh` before the call, as Bedrock requires.
- The fusion map is a **player-facing hint only**. POA changes only via `CleanScorer.update` after a miss, so fusion is never a hidden locator.
- Tolerances are reused, not invented: `TOL_UNIT = 1e-12` and `TOL_CONTRACT = 1e-9`.

### 1a. Diffs: Bedrock NEW-01 vs Loam GDD v0.3 §2a (Bedrock followed)
| Topic | Loam GDD v0.3 | Bedrock NEW-01 (adopted) |
|---|---|---|
| Segment type | dict `{name, area_km2, poa, w_km, speed_kmh, is_row}` | `@dataclass(frozen=True) Segment`, defaults `speed_kmh=None`, `is_row=False` |
| Errors | `UncitedSweepWidth` from `pos`/`optimal` | `ScorerError(ValueError)` base + `UncitedSweepWidth` subclass; uncited W also raised from **`update`**; full validation list (non-finite/negative inputs, area ≤ 0, ROW effort > 0, unknown or duplicate names, > 1 ROW, 1−POS < 1e-15 in update) |
| Module | `ledgerplay/scoring.py` | `sensegame/search_core.py`, re-exported by `ledgerplay/scoring.py` |
| Hours mode | out of scope (km-only) | optional; converted to km **before** the call, so the core stays km-only |
| Missing effort keys | unspecified | mean 0 effort |
| `optimal` algorithm | KKT water-filling (formula only) | closed-form sorted top-k, tie-break by name, O(n log n), no iterative tolerance; r=0 or p=0 → 0; all-unsearchable → zero plan (flagged in v0.2) |
| ROW in update | "ROW never searched" | explicit `POA_row' = POA_row/(1−POS)` |
| Numerics | not stated | stdlib `math` only, `math.fsum`, `-expm1`, canonical name order, sorted keys, `repr`/`%.17g` |
| Tolerances | 1e-9 | 1e-12 unit goldens + 1e-9 contract |
| Citations | Koopman ×3, Stone 1975 | adds Charnes & Cooper 1958 doi:10.1287/mnsc.5.1.44; Stone ISBN only "partly verified", no book DOI |
| Status | GDD adopted | **Bedrock draft, not approved**; no code yet |

## 2. Clean-room site/cell combiner (replaces realdata/fusion.py in the game path)
Module: `sensegame/fusion/combine.py` (registry 1080.1, provisional). It is written from public statistics and the contract above only.
- **Inputs:** `fixtures/*synthetic*` only (a path guard rejects anything else). Locations are **integer grid indices `(row, col)` plus fixture-local metres** on the synthetic DEM grid. No lat/lon, CRS-geographic coordinates, site names or free text anywhere in the schema. The schema validator rejects keys `lat`, `lon`, `latitude`, `longitude`, `address` and `site_id` strings that aren't of the form `cell_<r>_<c>`.
- **Per-layer normalisation:** robust z = (v − median)/(1.4826·MAD) (Hampel 1974 doi:10.1080/01621459.1974.10482962; Rousseeuw & Croux 1993 doi:10.1080/01621459.1993.10476408, both Crossref-verified). MAD = 0 → layer flagged `degenerate` and excluded, not zeroed. Optional rank percentile. `direction: lower` flips the sign.
- **Combination:** weighted mean Σwᵢzᵢ/Σwᵢ, with weights from the mission config (no built-in weights). Missing-layer policy is `zero` or `renormalise`, and is explicit in config.
- **Output:** per cell, the raw value, normalised value, weight and contribution for every layer (recomputable by hand), plus `score_kind: "relative ranking under configured weights; not a probability"`.
- `multi_proxy/consensus.py` (CLEAN) may be reused as the optional multiplicative variant, but only behind the degenerate-layer guard.

## 3. Anomaly score + calibrated uncertainty (always paired)
- Models: PyOD v3.6.7 (BSD-2; IForest/ECOD, fixed `random_state`) and/or HDBSCAN 0.8.44 (BSD-3; `outlier_scores_`, `probabilities_`; fixed row-major input order). TerraTorch/TerraMind **ON HOLD** (flag `FUSION_EMBEDDINGS=0`, not in requirements).
- Calibration: isotonic or Platt (Niculescu-Mizil & Caruana 2005 doi:10.1145/1102351.1102430) fit on synthetic calibration seeds with planted targets, evaluated on **disjoint synthetic holdout seeds**. ECE uses 15 equal-width bins (Naeini et al. 2015 doi:10.1609/aaai.v29i1.9602). **Gate: ECE ≤ 0.05**; Brier is reported too.
- Uncertainty: **B = 1000 seeded bootstrap resamples**. Replicate i is seeded by `SeedSequence([seed, i])`. Each cell gets the percentile 95% CI. Per-cell record: `{anomaly_score, p_anomaly_calibrated, ci_low, ci_high, n_boot: 1000, ece_holdout}`. The writer refuses any score without its band.

## 4. Determinism (rule 3)
`numpy.random.Generator(PCG64)` from `SeedSequence(seed)`. No global RNG, no wall-clock. Sorted keys and names. `OMP_NUM_THREADS=1`, `n_jobs=1`. Outputs are `uncertainty_map_<seed>.tif` (rasterio BSD-3, no timestamp tags) and `fusion_<seed>.json` (`%.17g`), plus `seeds.jsonl {seed, config_sha256, output_sha256, lib_versions}`. Same seed + config + pinned versions → **byte-identical** files. The Scorer side is already RNG-free per Bedrock §5.

## 5. Manual entrypoints (rule 4)
- `make fusion SEED=1002 CONFIG=fixtures/fusion_config_synthetic.json` → `python -m sensegame.fusion --seed 1002 --config … --out out/fusion/1002/`
- `make fusion-replay SEED=1002` re-runs and sha256-diffs against `seeds.jsonl`. `make fusion-test` → `python -m pytest sensegame/fusion/tests`.

## 6. Golden tests (Fusion-N writes them first, failing)
1. `test_determinism_bytes`: seed 1002 twice → identical sha256 (.tif and .json); seed 1003 → different.
2. `test_score_has_uncertainty`: every record has `p_anomaly_calibrated`, CI and `n_boot == 1000`.
3. `test_calibration_holdout`: ECE ≤ 0.05 on synthetic holdout seeds disjoint from the calibration seeds.
4. `test_scorer_contract_passthrough`: uses a stub `CleanScorer` reproducing Bedrock §6 goldens (pos 0.5056964470628461, update A 0.37211895300519393, within 1e-12). Fusion never alters POA except via `update`, and `UncitedSweepWidth`/`ScorerError` propagate unmodified.
5. `test_combine_handcomputed`: a 3-layer × 5-cell synthetic table → hand-computed robust-z and weighted scores (1e-12); MAD = 0 layer flagged as degenerate.
6. `test_no_geographic_fields`: schema rejects lat/lon/latitude/longitude/address.
7. `test_fixtures_synthetic_only`: every input path matches `fixtures/*synthetic*`.
8. `test_no_forbidden_imports`: AST scan fails on search_theory, optimal_search, lost_person_behavior, forensic_pipeline, dossier, evidence_fusion, evidence_scoring, public_records*, `realdata.fusion`/`realdata/fusion.py`, terratorch.
9. Existing suites stay green: `multi_proxy/test_engines.py`, `sar/sensor-fusion-grid/test_sensor_fusion_grid.py`.

## 7. Fixtures (synthetic only)
`fixtures/fusion_config_synthetic.json`, `fixtures/fusion_sensors_synthetic_<seed>.npz` (seeded planted targets + noise, grid indices only), `fixtures/fusion_holdout_synthetic_<seed>.npz`, plus NEW-03 `dem_synthetic_<seed>.tif`. No real coordinates, no case data, no PII.

## 8. Open items / blockers
Verity collision check for 1080; Bedrock NEW-01 approval and code (contract is draft); Verity ruling on realdata/fusion.py lineage (stays excluded regardless); TerraMind licence; M1 cited W (Bedrock §4b).
