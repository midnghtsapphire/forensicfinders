# SenseCrew Bedrock CHANGELOG

## 2380 (proposed) — DEM-derived grid layer spec — 2026-11-05
- Design spec only for a synthetic DEM→grid layer (`slope` rise/run m/m, Horn 1981 §IX/§XVI; `roughness` as 3×3 population RMS height in metres). No `sensegame.dem_layer` module, no `run_one_tile`, no orchestrator, no CleanScorer edit.
- Flat and other MAD=0 grids are `degenerate` and `excluded`, with computed values kept. Same rule as Fusion `combine.py` `robust_z` (PR #42 @ `ad83cba`): flagged and left out of the score, not given a z of 0. The 1.4826 factor stays in Fusion.
- Determinism: same elevation array + kind + `cell_m` → identical little-endian float64 bytes. Seed is provenance only (`dem.generate` / `fixtures/*synthetic*`). Geographic keys rejected. `M1_W_KM` unchanged (`None`).
- Failing goldens: `docs/sensecrew/bedrock/specs/tests/test_dem_layer_golden.py` (ImportError until the module exists).
- Proposed registry id 2380 under parent 2300. 2330 is NEW-10 (sweep-width table) and is not used. No `sar/registry.json` edit. Discussion #44. Bedrock-N APPROVE. Verity pending.

## case-view schema 0.1 — 2026-11-06
- Anonymized case-view contract Bedrock serves to the Godot game. Machine file: `docs/sensecrew/bedrock/schemas/case_view_enums.json` (JSON Schema draft 2020-12). Human spec: `docs/sensecrew/bedrock/schemas/CASE_VIEW.md`.
- `version` `0.1`, `status` `pending-audrey-confirm`, `synthetic_only_until_confirmed` true. Public fixtures are synthetic. The API allows `case_source` `real_anonymized`; a fixture row with that source is rejected.
- Unknown enum values are rejected and are not coerced. `location.label` is the const `predicted`. No coordinates and no fuzzed-coordinate substitutes.
- Synthetic fixture `sar/fixtures/case_view_synthetic_1001.json`. Tokens come from `random.Random(1001)`. Terrain ids are `fixtures/dem_synthetic_<seed>.tif`. No real case data.
- Registry provisional **2390** (`sensegame/case_view`). 2330 and 2380 are not used.
- Bedrock owns the contract. Quill owns token semantics. Secret owns the private table and export. GodotForge consumes. Tips go to the investigating agency and are never published.
- Bedrock-N APPROVE. Verity pending.

## case-view schema 0.1 follow-up — 2026-11-06
- `fixture_id` pattern is `^(sar/)?fixtures/[A-Za-z0-9._-]*synthetic[A-Za-z0-9._-]*$`. Checked-in ids are the repo-relative paths `sar/fixtures/dem_synthetic_<seed>.tif`. `fixtures/...` and `sar/fixtures/...` both validate. Other prefixes are rejected.
- `status` is `confirmed`. Audrey confirmed real cases in Sense-Quill chat 2026-11-06 10:55 MT; Quill v0.1 enums verified against PR #51 @f94e757.
- `synthetic_only_until_confirmed` stays true. Real exports stay blocked until Secret clears the CC-0003 identity question and the Charley Project licence and Verity co-signs the re-identification test.
- Bedrock-N APPROVE. Verity pending the re-identification co-sign.
