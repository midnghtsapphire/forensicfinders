# SenseCrew Bedrock CHANGELOG

## 2026-11-06

- Ledger append-only: the 10:42 constraint line edited in place by 3bf0c1a is restored verbatim. Superseding wording is `M1_W_KM` is None until a cited W exists (Verity hold, Decision B). Tests by scope: (a) scorer goldens + language_scan **57 passed** (goldens 41 passed, 0 xfailed, 0 skipped; language_scan 16 passed); (b) full `sar/sensegame` **65 passed, 0 xfailed, 1 skipped** (`test_dem_fixture_golden.py:109`, rasterio not installed). No M1 xfail remains. Licence n/a.
- Verity holds on #41: `M1_W_KM` is `None` until a cited W exists. Coverage-model fallback pointers are GDD v0.5 §4 / §4a. Merged `origin/main` with a merge commit. Licence n/a.
- CleanScorer (2310), Decision B (Discussion #28 comment 19445708; https://github.com/midnghtsapphire/forensicfinders/discussions/28#discussioncomment-19445708). `M1_W_KM` is `None` until a cited W exists (cited effective sweep width with Verity co-sign). `M1_W_SOURCE` cites that comment. Woolpert OH Statewide Phase 1 2019 B19, Table 2-4 (H = 2000 m AGL, FOV = 40°, stated swath 1.456 km) is geometric coverage only, not effective sweep width. M1 goldens score budget spend and geometric coverage. Coverage does not produce POD, POS, or a negative-evidence update. No path substitutes `0.9×swath` or any geometric fraction as W. `exponential_coverage_model` is a labelled model (`1 − exp(−C)` via `-math.expm1(-C)`, GDD v0.5 §4 / §4a) and is not M1 detection. NEW-10 / registry 2330 is not reused. Licence n/a.

## 2380 (proposed) — DEM-derived grid layer spec — 2026-11-05

- Design spec only for a synthetic DEM→grid layer (`slope` rise/run m/m, Horn 1981 §IX/§XVI; `roughness` as 3×3 population RMS height in metres). No `sensegame.dem_layer` module, no `run_one_tile`, no orchestrator, no CleanScorer edit.
- Flat and other MAD=0 grids are `degenerate` and `excluded`, with computed values kept. Same rule as Fusion `combine.py` `robust_z` (PR #42 @ `ad83cba`): flagged and left out of the score, not given a z of 0. The 1.4826 factor stays in Fusion.
- Determinism: same elevation array + kind + `cell_m` → identical little-endian float64 bytes. Seed is provenance only (`dem.generate` / `fixtures/*synthetic*`). Geographic keys rejected. `M1_W_KM` unchanged (`None`).
- Failing goldens: `docs/sensecrew/bedrock/specs/tests/test_dem_layer_golden.py` (ImportError until the module exists).
- Proposed registry id 2380 under parent 2300. 2330 is NEW-10 (sweep-width table) and is not used. No `sar/registry.json` edit. Discussion #44. Bedrock-N APPROVE. Verity pending.
