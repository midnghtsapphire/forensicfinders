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
