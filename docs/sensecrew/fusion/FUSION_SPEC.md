# FUSION_SPEC v0.1 — seeded uncertainty maps over CleanScorer (NEW-01)

Owner: Sense-Fusion (Fusion-D / Fusion-N). Status: **doc-only proposal, no code, no swarm**. Licence: UNLICENSED (private repo; licence pending Audrey). Base: main `a2630989`.

## 0. Ground truth on interfaces
- **CleanScorer is not in the repo yet.** `git grep -i "cleanscorer|NEW-01"` across all branches finds it only in docs: `docs/sensecrew/loam/GDD_v0.2/0.3.md` (branch `sensecrew/loam/gdd`, PR #10) and `LEDGER.md`. No `ledgerplay/scoring.py` exists. This spec therefore targets the **expected contract** from GDD v0.3 §2a:
```python
class Scorer(Protocol):
    def pod(self, w_km: float, track_km: float, area_km2: float) -> float      # 1-exp(-W z/A), Koopman 1956b, doi:10.1287/opre.4.5.503
    def pos(self, segments: list[Segment], effort_km: dict[str, float]) -> float   # Σ POA·POD
    def optimal(self, segments: list[Segment], budget_km: float) -> dict[str, float]  # KKT water-filling, Koopman 1957 doi:10.1287/opre.5.5.613; Stone 1975 (no DOI)
    def update(self, segments: list[Segment], effort_km: dict[str, float]) -> list[Segment]  # Bayes after a miss
# Segment = {name, area_km2, poa, w_km|None, speed_kmh|None, is_row}
```
- Invariants inherited: ROW effort = 0; Σ POA = 1 ± 1e-9; `w_km=None` → `UncitedSweepWidth`, never substituted. Fusion must propagate that error, never impute W.
- Fusion consumes the Scorer **only through this Protocol** (dependency injection). It never imports `search_theory`, `optimal_search`, `lost_person_behavior`, `forensic_pipeline`, `realdata/fusion.py` (UNCERTAIN, see RULE7_AUDIT.md) or `evidence_fusion.py`.

## 1. Pipeline (module `sensegame/fusion/`, NEW-13 placeholder)
1. **Inputs:** a seeded scenario (Segments from NEW-02 prior, labelled SYNTHETIC), per-sensor seeded readings rasters from Bedrock sensor models on `fixtures/dem_synthetic_<seed>.tif`, and the effort plan.
2. **Consensus layer:** per-cell normalised sensor layers combined with a weighted robust-z mean (median/1.4826·MAD), reimplemented clean-room. `multi_proxy/consensus.py` (CLEAN) may be reused for the multiplicative variant, with a guard for degenerate layers.
3. **Anomaly score:** PyOD v3.6.7 (BSD-2; e.g. IForest/ECOD with fixed `random_state`) and/or HDBSCAN 0.8.44 (BSD-3; `outlier_scores_`, `probabilities_`; deterministic given data order, so cell order is a fixed row-major order).
4. **Calibrated uncertainty, always paired with the score:** for every cell, emit `{anomaly_score, p_anomaly_calibrated, ci_low, ci_high, n_boot}`. Calibration is done by isotonic/Platt fit on a **synthetic held-out seed set** with known planted targets. Uncertainty is a seeded bootstrap of B replicates (B in config, default PLACEHOLDER 200), with replicate seeds derived as `sha256(f"{seed}:{i}")[:8]`. Report reliability (ECE, Brier) per run. No score is written without its uncertainty band; a writer-level assertion enforces this.
5. **Scorer coupling:** cell maps aggregate to segments (area-weighted) → `p_detect_hint` per segment, shown to the player as information. They **do not** change POA directly. POA changes only via `Scorer.update` after a search miss, so fusion never becomes a hidden locator. Debrief reports `pos`, `optimal`, η, and the calibration of the fusion map against the seed's planted truth.
6. **TerraTorch (TerraMind/Prithvi embeddings): ON HOLD.** Not imported, not in requirements, until Verity verifies the TerraMind model-card licence. A feature flag `FUSION_EMBEDDINGS=0` is reserved.

## 2. Determinism (rule 3)
- Single `numpy.random.Generator(PCG64(seed))`; child streams via `SeedSequence(seed).spawn`. No global RNG, no wall-clock, no dict-order dependence, sorted segment names.
- Threading pinned (`OMP_NUM_THREADS=1`, `n_jobs=1`) so float reductions are order-stable.
- Outputs: `uncertainty_map_<seed>.tif` (rasterio BSD-3 / GDAL, deterministic tags, no timestamp) + `fusion_<seed>.json` (sorted keys, fixed float repr `%.17g`), plus `seeds.jsonl` rows `{seed, config_sha256, output_sha256, lib_versions}`.
- **Same seed + same config + pinned versions → byte-identical files** (sha256 equality).

## 3. Manual entrypoints (rule 4)
- `make fusion SEED=1002 CONFIG=fixtures/fusion_config_synthetic.json` → `python -m sensegame.fusion --seed 1002 --config … --out out/fusion/1002/`
- `make fusion-replay SEED=1002` re-runs it and diffs sha256 against `seeds.jsonl`.
- `make fusion-test` → `python -m pytest sensegame/fusion/tests`.

## 4. Golden tests (Fusion-N writes them first, failing)
1. `test_determinism_bytes`: two runs with seed 1002 → identical sha256 for .tif and .json; seed 1003 → different.
2. `test_score_has_uncertainty`: every cell/segment record has a calibrated p and CI; the writer rejects records missing them.
3. `test_calibration_synthetic`: on planted-target synthetic seeds, ECE ≤ PLACEHOLDER (to be set by Verity).
4. `test_scorer_contract_passthrough`: uses a stub Scorer implementing the Protocol (analytic 2-segment case); fusion never changes POA except via `update`; `UncitedSweepWidth` propagates.
5. `test_no_forbidden_imports`: AST scan fails on search_theory, optimal_search, lost_person_behavior, forensic_pipeline, dossier, evidence_fusion, evidence_scoring, public_records*, realdata.fusion, terratorch.
6. `test_fixtures_synthetic_only`: every input path matches `fixtures/*synthetic*`.
7. Existing suites stay green: `multi_proxy/test_engines.py`, `sar/sensor-fusion-grid/test_sensor_fusion_grid.py` (registry `--test`).

## 5. Fixtures (synthetic only)
`fixtures/fusion_config_synthetic.json`, `fixtures/fusion_sensors_synthetic_<seed>.npz` (seeded planted targets + noise), and the DEMs from NEW-03. No real coordinates, sites, or case data, and no PII.

## 6. Open items
CleanScorer implementation (Bedrock, NEW-01); Verity ruling on `realdata/fusion.py` lineage; TerraMind licence; ECE threshold and B; NEW-13 registry number confirmation (Strata).
