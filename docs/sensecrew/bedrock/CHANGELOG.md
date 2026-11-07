# SenseCrew Bedrock CHANGELOG

## 2026-11-06

- `test_dem_fixture_golden` resolves committed fixtures from `Path(__file__)` (`sar/sensegame/tests` → `sar/`) so `pytest sar/sensegame` passes with cwd at the repo root and with cwd `sar/`. Fixture bytes and SHA-256 goldens unchanged. `test_registry_coverage.py` from cwd `sar/`: 3 passed. Scorer and DEM goldens are already reached by component 2300 (`sensegame/tests`); language_scan is component 1000. Registry 2330 not touched. Licence n/a.
- Ledger append-only: the 10:42 constraint line edited in place by 3bf0c1a is restored verbatim. Superseding wording is `M1_W_KM` is None until a cited W exists (Verity hold, Decision B). Tests by scope: (a) scorer goldens + language_scan **57 passed** (goldens 41 passed, 0 xfailed, 0 skipped; language_scan 16 passed); (b) full `sar/sensegame` **65 passed, 0 xfailed, 1 skipped** (`test_dem_fixture_golden.py:109`, rasterio not installed). No M1 xfail remains. Licence n/a.
- Verity holds on #41: `M1_W_KM` is `None` until a cited W exists. Coverage-model fallback pointers are GDD v0.5 §4 / §4a. Merged `origin/main` with a merge commit. Licence n/a.
- CleanScorer (2310), Decision B (Discussion #28 comment 19445708; https://github.com/midnghtsapphire/forensicfinders/discussions/28#discussioncomment-19445708). `M1_W_KM` is `None` until a cited W exists (cited effective sweep width with Verity co-sign). `M1_W_SOURCE` cites that comment. Woolpert OH Statewide Phase 1 2019 B19, Table 2-4 (H = 2000 m AGL, FOV = 40°, stated swath 1.456 km) is geometric coverage only, not effective sweep width. M1 goldens score budget spend and geometric coverage. Coverage does not produce POD, POS, or a negative-evidence update. No path substitutes `0.9×swath` or any geometric fraction as W. `exponential_coverage_model` is a labelled model (`1 − exp(−C)` via `-math.expm1(-C)`, GDD v0.5 §4 / §4a) and is not M1 detection. NEW-10 / registry 2330 is not reused. Licence n/a.

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

## case-view schema 0.1 Verity CHANGES — 2026-11-06
- Verity returned PR #51 @ `f94e757` as CHANGES at 0.84.
- Emitting `real_anonymized` requires all of: per-source terms `yes`, Secret's pinned full-quasi-identifier k-anonymity plus linkage review, and Secret's export co-sign. Schema confirmation alone is not clearance.
- Emission is a closed allowlist. Every row is validated against the schema before it is emitted. `banned_fields` is defence in depth only, not the primary control.
- Checker violations are a JSON path plus a fixed code. They do not include the submitted value or a hash of an identifier.
- `geometry`, `geohash`, `bbox`, `lat`, `lon`, `date`, and `last_seen_date` are rejected on every emitted object. A string, float, or bool `seed` is rejected and is not coerced. Anchored patterns reject a leading extra, a trailing extra, and a newline.
- Bedrock-N APPROVE. Verity re-identification co-sign still pending.

## case-view emission wording — 2026-11-06
- Secret corrected the `real_anonymized` clearance text in `CASE_VIEW.md`. A row is emitted as `real_anonymized` only when all seven checks hold: `terms_allows_derived_use=yes` on every source, `identity_status=confirmed` for every case, no `removal_requested` and no resolved hold, a freshly minted active `CASE_TOKEN`, a passed stand-in location check, Secret's pinned `k>=5` full-quasi-identifier test plus linkage and attribute-inference review, and Verity's private comment-only re-identification co-sign pinned to the artifact SHA-256.
- Secret runs the tests. Verity is the co-signer. If any check fails, the row is not emitted. Any change to the schema, code, sources, or access expires the co-sign.
- Schema confirmation alone is not clearance. Emission stays a closed allowlist with every row validated before emit. `banned_fields` stays defence in depth only.
- `case_view_enums.json` was not edited. Its SHA-256 stays `0a37d3b103c2a15489b7b18ffee604ee103614cb8eaa55d184aa6924f2b8ce7a`.
- Bedrock-N APPROVE.

## case-view status revert — 2026-11-06
- Verity returned PR #51 @ `fae78acf` as CHANGES at 0.86. The three technical fixes had passed at 0.90.
- `status` is `pending-audrey-confirm` again. `synthetic_only_until_confirmed` stays true. The earlier `confirmed` value is withdrawn. Adopting the real-case policy is not the same as confirming this contract.
- The attribution that a chat had confirmed this contract is removed from the living spec, the schema, the fixture, the tests, and the registry note. Schema confirmation alone is not clearance.
- Private row-token breadcrumbs are removed from those same living files. `identity_status=confirmed` for every case.
- Bedrock-N APPROVE.

## case-view emission value names — 2026-11-06
- Secret corrected emission condition 2 in `CASE_VIEW.md`. Emission requires `identity_status=confirmed_public` for every case. `unconfirmed_pending_audrey` never emits. No case's own status is named.
- Any change expires Verity's co-sign. The list is the matcher, the test harness, the artifact, the schema, the code, the sources, and the access.
- `case_view_enums.json` was not edited. Its SHA-256 stays `a6ddf87232a8a1fa1c64b774a0cc89f474034606f8895010bb57e6c11bb53a38`.
- Bedrock-N APPROVE.

## case-view emission_gate alignment — 2026-11-06
- Verity returned PR #51 @ `54fa05f` as CHANGES at 0.87. The schema annotation `emission_gate` and its test now list the same seven conditions as `CASE_VIEW.md`, including `identity_status=confirmed_public` as the only value that emits and `unconfirmed_pending_audrey` as a value that never emits.
- The old three-code gate is replaced by Verity's private comment-only co-sign pinned to the artifact SHA-256. Secret runs the tests. Any change expires the co-sign, including the matcher, the test harness, the artifact, the schema, the code, the sources, and the access.
- The exporter enforces these gates. JSON Schema does not.
- Enums file SHA-256 is `97efab8581d87b12836c4c715871185d0cc3a7768a1046dba45d0b42c6c8f5ea`.
- Bedrock-N APPROVE.

## case-view co-sign pins and export blockers — 2026-11-06
- Secret re-pinned PR #51 at `270f0df`. Condition 7 now pins the co-sign to `artifact_sha256`, `schema_commit`, `harness_commit`, `reference_snapshot`, `quasi_identifier_list`, `threshold` (`k>=5`), and `sanitized_pass_fail_counts`.
- `real_export_block` also names starter-row identity confirmation and fresh tokens minted after confirmation, with the Charley Project licence and the Verity co-sign. No case's own status is named.
- Bedrock-N APPROVE.
