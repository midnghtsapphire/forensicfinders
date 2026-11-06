# SenseCrew Fusion LEDGER (append-only)

## 2371 (provisional) — sensegame/fusion combine + anomaly
- who: Sense-Fusion (Fusion-D drive, Fusion-N review)
- why: Strata GO (2026-11-05 08:22 MST) to implement FUSION_SPEC v0.2 §2–§7 as a synthetic-only hint layer.
- sources: FUSION_SPEC v0.2 (PR #18 @ 6fb9960); Bedrock scorer-spec 2310 (docs/sensecrew/bedrock/specs/scorer-spec.md, PR #41 @ 8e745c6); Hampel (1974) JASA 69:383–393; Rousseeuw & Croux (1993) JASA 88:1273–1283; Li et al. ECOD (2022, IEEE TKDE); Zadrozny & Elkan (2002) isotonic calibration; Naeini et al. (2015) ECE; Efron & Tibshirani (1993) bootstrap.
- data: procedural synthetic scenes only (synth.py); no case/, hfmr/, dossier, evidence/, public-records, realdata/fusion.py, TerraMesh, TerraTorch, LUCAS, Ultralytics.
- licence: UNLICENSED (private repo; licence pending Audrey)
- review: see sensecrew/ledger for Fusion-N APPROVE (<sha>)

## 2371 — Decision B null-W (coverage and budget only)
- who: Sense-Fusion
- why: Proofy Option B. M1_W_KM is None until a cited W exists. Fusion must not invent W or score M1 as detection.
- sources: https://github.com/midnghtsapphire/forensicfinders/discussions/28#discussioncomment-19445708 ; Bedrock PR #41 @ 21774e2215ea07aadddac62a4085d841b488a401 (scorer-spec §4b, CleanScorer coverage/budget methods, M1 goldens; includes origin/main @ 2ef0d0afcfd98e604bfaae5d6655a8dccd8bae23, same tip as daily/2026-11-06).
- ruling: M1_W_KM is None until a cited W exists. M1_W_SOURCE cites that comment. Woolpert OH 2019 Table 2-4 (H = 2000 m, FOV = 40°, stated swath 1.456 km) is geometric coverage only. Surveyed is not detected. Coverage does not produce POD, POS, or a negative-evidence update. No path substitutes 0.9×swath, or any geometric fraction, as effective W. exponential_coverage_model is a labelled model (GDD v0.5 §4 / §4a) on player-supplied C and is not M1 detection. Registry 2330 untouched.
- data: no change to combine.py, anomaly.py, or synthetic fixtures. Fusion production modules do not set a numeric M1 width and do not call pod/pos/optimal/update.
- licence: UNLICENSED (private repo; licence pending Audrey)

## 2370/2371 — registry coverage, and #41 @ c933dd7
- who: Sense-Fusion
- why: `sar/test_registry_coverage.py` failed because `sensegame/fusion/tests/test_fusion.py` sat outside every component test command, so `registry.py --test-all` never ran fusion.
- action: registered provisional 2370 (parent 2300; pytest `sensegame/fusion/tests`, test_cwd `.` under sar/) and 2371 (`sensegame/fusion/combine.py`, parent 2370). Did not reuse 2330. `combine.py`, `anomaly.py`, and the synthetic fixtures are unchanged.
- also: merged Bedrock #41 @ c933dd7c5800404f64360bd5c277f967e21151c8. That tip resolves DEM golden paths from the test file. Its parent fbd3e9b restored the 10:42 ledger line. M1_W_KM is None until a cited W exists. No second local edit to the DEM test.
- counts (venv CPython 3.12, OMP_NUM_THREADS=1, PYTHONHASHSEED=0):
  - fusion: cwd `sar/`, `pytest -q sensegame/fusion/tests` → 26 passed
  - sensegame: cwd repo root, `pytest -q sar/sensegame` → 92 passed
  - sensegame: cwd `sar/`, `pytest -q sensegame` → 92 passed
  - language scan: cwd `sar/`, `pytest -q test_language_scan.py` → 16 passed
  - registry coverage: cwd `sar/`, `python -m unittest test_registry_coverage` → 3 passed
  - `registry.py --test-all` from repo root, venv `python3` on PATH → exit 1, FAILED components 100, 700, 900. 2370 was not in that failed set. Those three failures are pre-existing and out of scope (missing `cryptography`; coldtrace missing `fastapi` / `pydantic_settings`; geo_connectors `test_example_case_config_is_synthetic` cannot parse `case/example.config.yaml`).
- licence: UNLICENSED (private repo; licence pending Audrey)

## 2371 — docs DEM mirror path
- who: Sense-Fusion
- why: Verity static delta on #42 @ 8ab7f2b. The specs mirror of the DEM golden test still opened `fixtures/` relative to cwd.
- action: `docs/sensecrew/bedrock/specs/tests/test_dem_fixture_golden.py` now resolves those paths from `__file__` (repo `parents[5]` / `sar`), the same rule as `sar/sensegame/tests/test_dem_fixture_golden.py`. Header states this copy is not dispatched by `registry.py` and is not collected by `pytest sensegame` or `pytest sar/sensegame`. The file originates on #41 (added in `8c98804`; blob on #41 @ c933dd7 was still the cwd-relative copy). 2330 was not reused. The dispatched sensegame test, `combine.py`, `anomaly.py`, and fusion fixtures were not edited.
- hold: GDD v0.5 §4 / §4a is the coverage-model pointer. GDD v0.5 is not yet published; the pointer stays a known hold until Loam's draft lands. M1_W_KM is None until a cited W exists.
- counts re-run on this change (venv CPython 3.12, OMP_NUM_THREADS=1, PYTHONHASHSEED=0):
  - fusion: cwd `sar/`, `pytest sensegame/fusion/tests` → 26 passed
  - sensegame: cwd repo root, `pytest sar/sensegame` → 92 passed
  - sensegame: cwd `sar/`, `pytest sensegame` → 92 passed
  - language scan: cwd `sar/`, `pytest test_language_scan.py` → 16 passed
  - registry coverage: cwd `sar/`, `python -m unittest test_registry_coverage` → 3 passed
  - `registry.py --test-all` from repo root → exit 1, FAILED 100, 700, 900 only (pre-existing; out of scope; Triage WR)
- licence: UNLICENSED (private repo; licence pending Audrey)

## 2371 — geo-key guard and seed drift
- who: Sense-Fusion
- why: Strata: a follow-up is justified only when it has a WR or issue link. None of the four Cubic findings had one. The geo-key list is a privacy guard, so it is fixed here. The silent seed append is fixed here. The CI clamp and the dependency pins are filed as issues because the first changes seeded bytes and the second is a packaging decision.
- action: `GEO_KEYS` also rejects geohash, bbox, crs, epsg, easting, northing, polygon, point, location, geojson, x_coord, y_coord, utm, and mgrs, matched case-insensitively. The nested dict and list walk stays. A rejection names the canonical key and does not include the field value. `seeds.jsonl` stays append-only. A different hash for the same seed exits 1 and appends nothing. `--accept-drift` appends a new record whose `drift_from` is the sha256 of the previous record. The same output hashes do not append.
- issues: https://github.com/midnghtsapphire/forensicfinders/issues/52 (raw bootstrap percentiles; evidence at 9dee8f8 `anomaly.py` L106; Cubic https://github.com/midnghtsapphire/forensicfinders/pull/42#discussion_r4482495429). https://github.com/midnghtsapphire/forensicfinders/issues/53 (pin pytest, add or decline scipy, pin-set test; evidence at 9dee8f8 `requirements-fusion.txt` L2; Cubic https://github.com/midnghtsapphire/forensicfinders/pull/42#discussion_r4482495501). Assignment to midnghtsapphire returned 403 from this integration.
- hold: M1_W_KM is None until a cited W exists. GDD v0.5 §4 / §4a is the coverage-model pointer and is not yet published. 2330 was not reused.
- counts (venv CPython 3.12, OMP_NUM_THREADS=1, PYTHONHASHSEED=0):
  - fusion: cwd `sar/`, `pytest sensegame/fusion/tests` → 126 passed
  - sensegame: cwd repo root, `pytest sar/sensegame` → 192 passed
  - language scan: cwd `sar/`, `pytest test_language_scan.py` → 16 passed
  - registry coverage: cwd `sar/`, `python -m unittest test_registry_coverage` → 3 passed
- licence: UNLICENSED (private repo; licence pending Audrey)

## 2371 — replay ignores ledger-only fields
- who: Sense-Fusion
- why: Verity CHANGES at 0.88 on #42 @ f7e928b. `--replay` compared the whole record, including `drift_from`, which `run()` never writes, so an accepted drift failed replay when the outputs matched.
- action: `_outputs` is the one normalization. It strips record-only fields (`drift_from`). `record_run` and `--replay` both compare that view. A replay mismatch prints `REPLAY_MISMATCH`, at most 10 differing key names, and SHA-256 digests of the normalized expected and got outputs. It does not print field values, and it does not append. M1_W_KM is None until a cited W exists. GDD v0.5 §4 / §4a remains the coverage-model pointer. 2330 was not reused.
- tests: `test_replay_after_accept_drift_passes`, `test_replay_after_chained_accept_drift_passes`, `test_replay_output_mismatch_exits_nonzero_and_appends_nothing` (also asserts a raw value is absent from stdout and stderr).
- counts (venv CPython 3.12, OMP_NUM_THREADS=1, PYTHONHASHSEED=0):
  - fusion: cwd `sar/`, `pytest sensegame/fusion/tests` → 129 passed
  - sensegame: cwd repo root, `pytest sar/sensegame` → 195 passed
  - language scan: cwd `sar/`, `pytest test_language_scan.py` → 16 passed (no live deferral token)
  - registry coverage: cwd `sar/`, `python -m unittest test_registry_coverage` → 3 passed
- licence: UNLICENSED (private repo; licence pending Audrey)

## 2371 — Strata seed 1003 replay regression
- who: Sense-Fusion
- why: Strata reproduced the replay bug at f7e928b with seed 1003: tamper the stored hash, `--accept-drift`, then `--replay` exited 1 and dumped both dicts. The only difference was `drift_from`.
- action: `test_strata_seed_1003_accept_drift_then_replay` follows those steps from cwd `sar/` against a temporary `seeds.jsonl`, never the repo ledger. Replay exits 0. A second tamper plus `--accept-drift` also replays. A further tamper without that flag exits nonzero, appends nothing, and the streams contain `REPLAY_MISMATCH`, the key name, and digests, not the hash values or a dict. M1_W_KM is None until a cited W exists. GDD v0.5 §4 / §4a remains the coverage-model pointer. 2330 was not reused.
- counts (venv CPython 3.12, OMP_NUM_THREADS=1, PYTHONHASHSEED=0):
  - fusion: cwd `sar/`, `pytest sensegame/fusion/tests` → 130 passed
  - sensegame: cwd repo root, `pytest sar/sensegame` → 196 passed
  - language scan: cwd `sar/`, `pytest test_language_scan.py` → 16 passed
  - registry coverage: cwd `sar/`, `python -m unittest test_registry_coverage` → 3 passed
- licence: UNLICENSED (private repo; licence pending Audrey)
