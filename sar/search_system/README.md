# search_system (1400): multi-scale burial-search ranking (PROTOTYPE)

**PROPRIETARY - ALL RIGHTS RESERVED.** (c) 2026 Audrey Evans / Walter-Evans Forensic Intelligence Systems.
No license is granted (see `LICENSE`). Pre-patent-filing; the repository must stay private (see `docs/PATENT_PREP.md`).

Ported 2026-10-21 from Audrey's `search-system` zip. `__pycache__` was skipped, and so was the case cohort
(`CASE_COHORT.md`), which lives only in the private `case-files` repo. Status: **PROTOTYPE**.
Every number the demos print is **synthetic**.

| ID | File | What |
|---|---|---|
| 1410 | `remains_anomaly_pipeline.py` | Lidar mound→sink DoD signature, NDVI/report/nitrate layers, stratified Gi*, change confidence, blocked-CV calibrated P(grave), NMS candidates, operating curve |
| 1420 | `run_county.py` | AOI tiling, 3DEP EPT / OpenTopography ingest, config validation, county sweep, GeoTIFF export |
| 1430 | `field_confirmation.py` | qPCR assay QC (LOD95/LOQ, triplicate concordance, IPC inhibition, ordered calls) + culvert/void detector |
| 1440 | `coldcase_master.py` | Case scaffolding with sealed truth, blind validation harness, SHA-256 hash-chained evidence log, chain verify, anchor manifest |
| 1450 | `fall_physics.py` | Monte-Carlo fall/slide landing distribution on a DEM, 95% ellipse, recovery percentile, sensitivity |

Tests: `python3 -m unittest test_search_system` (synthetic only). Demo outputs go to `$SEARCH_SYSTEM_OUT`
(default `out/search_system`, gitignored). The original paths under `/mnt/agents/output` were replaced.

## Audit (fix first, label as prototype, nothing dropped)
**Fixed**
- **Label leakage (1410 `make_tile`):** report points and nitrate samples were placed *exactly on the planted graves*.
  That handed the model the answer and inflated every demo AUC/recall that used `make_tile`
  (county sweep, operating curve, cold-case validation). They are now empty by default. The two
  remaining demos that still place nitrate on graves are marked `ORACLE` (upper bound, not a result).
- **qPCR copies/g (1410 `qpcr_quantify`):** an arbitrary `50 / ng` factor was replaced with
  copies/rxn × elution/template ÷ soil grams (new required args).
- **Duplicate `rank_sites_gistar` (1410):** the first definition was silently shadowed; it was removed.
- **`compute_tile_rasters` (1420):** `array or default` crashed on numpy arrays; it now uses explicit None checks.
- **LOD95 (1430):** the docstring claimed a logistic fit but the code interpolates (docstring corrected). When the
  lowest standard already hits 95%, the code returned None; it now returns that concentration as an upper bound.
- **Fall physics (1450):** `n_mc` and the RNG seed were hard-coded; both are now parameters.

**Labelled (kept, marked in code)**
- Fusion weights, `nitrate_threshold_mgkg=40`, `qpcr_loq_copies_per_g=1e3`, and the sink-window heuristic are
  **unsourced hand-set values**. The sink window compares epoch-interval length, not time since burial.
- The NDVI layer in every demo is **pure random noise** (placeholder, no signal).
- The cold-case `demo` "validation" derives truth from the planted grave, so it checks the plumbing, not performance.
  The demo run after the fix printed detection 1.0 and truth-in-top-3 = 2/3. That is synthetic and must not be cited
  (see `docs/VALIDATION_PROTOCOL.md`).
- `field_confirmation` demo LOD95/LOQ (150/200) are **made-up placeholders**, not a validated assay.
- `BLUE_OCEAN` source strings are short labels, not checked in the port. `verify_chain` claimed "admissible"
  evidence; this was softened to tamper-evident.
- Fall-physics Cd/A/μ ballparks have no citation. The default μ=0.30 is below the 0.4–0.7 range the module itself states.

**Removed as case-identifying**
- A named real terrain ("Sharp Mountain") in the fall demo and a cohort ID (VAL-02) in a docstring were replaced
  with generic wording. Cohort IDs (OPS-06/07) in `REWARD_PRIORITY.md` were genericised. No names, dates of birth
  or coordinates were present in the code.

Overlap to reconcile later: Gi* (here vs 1110), void detector (here vs 1100), qPCR QC (here vs 1300).
