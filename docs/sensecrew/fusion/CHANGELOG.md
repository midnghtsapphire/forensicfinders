# SenseCrew Fusion CHANGELOG

## 2371 (provisional) — combine.py + anomaly/calibration — 2026-11-05
- Added `sar/sensegame/fusion/` per FUSION_SPEC v0.2 (PR #18 @ 6fb9960): `combine.py` (robust z, Hampel 1974 / Rousseeuw & Croux 1993; MAD=0 layers flagged degenerate + excluded, not zeroed; per-layer raw/normalised/weight/contribution per cell; grid-index cells only; lat/lon/address rejected; fixtures/*synthetic* path guard), `anomaly.py` (PyOD 3.6.7 ECOD, isotonic calibration, B=1000 seeded bootstrap via SeedSequence([seed,i]), ECE 15-bin gate ≤0.05 on synthetic holdouts, writer refuses unbanded scores), `run.py`, `__main__.py` CLI, `synth.py` procedural generator, synthetic fixtures (seeds 1002/1003 run, 2001–2010 calibration, 3001–3010 holdout).
- Makefile: `fusion`, `fusion-replay`, `fusion-test`. Outputs `out/fusion/<seed>/fusion_<seed>.json` (%.17g floats, sorted keys, no timestamps) + `uncertainty_map_<seed>.tif` (no CRS); `out/fusion/seeds.jsonl` append-only hash log.
- Depends on PR #41 (`sensegame/search_core.py`, NEW-01 = 2310). Hint layer only; never changes POA.

## 2371 — Decision B null-W coverage-only — 2026-11-06
- Brought this branch up to date with Bedrock PR #41 @ 21774e2215ea07aadddac62a4085d841b488a401 (merge of `sensecrew/bedrock/new-01-cleanscorer`, which includes origin/main @ 2ef0d0afcfd98e604bfaae5d6655a8dccd8bae23, the same tip as `daily/2026-11-06`). Decision B (https://github.com/midnghtsapphire/forensicfinders/discussions/28#discussioncomment-19445708): M1_W_KM is None until a cited W exists. Woolpert OH 2019 Table 2-4 stated swath 1.456 km (H = 2000 m, FOV = 40°) is geometric coverage only.
- Fusion does not assume a numeric M1 width, does not substitute that swath or 0.9×swath as effective W, and does not score M1 through POD, POS, optimal, or update. `exponential_coverage_model` is a labelled model (GDD v0.5 §4 / §4a) and is not an M1 detection score. `combine.py`, `anomaly.py`, and the synthetic fixtures are unchanged. Registry 2330 is untouched.

## 2370/2371 — registry coverage and #41 DEM paths — 2026-11-06
- Registered provisional 2370 and 2371 in `sar/registry.json`. 2370 runs `pytest sensegame/fusion/tests` (cwd `.` under sar/). 2371 is `sensegame/fusion/combine.py` and its parent is 2370. 2330 is not reused. `registry.py --test-all` now reaches `sensegame/fusion/tests/test_fusion.py`.
- Merged Bedrock #41 @ c933dd7c5800404f64360bd5c277f967e21151c8. DEM golden paths in `test_dem_fixture_golden.py` are resolved from that file. M1_W_KM is None until a cited W exists.
- Counts: fusion 26 passed (cwd `sar/`, `pytest sensegame/fusion/tests`); `pytest sar/sensegame` 92 passed (repo root); `pytest sensegame` 92 passed (cwd `sar/`); language scan 16 passed (cwd `sar/`); registry coverage 3 passed (cwd `sar/`). `registry.py --test-all` still fails components 100, 700, and 900 on pre-existing gaps (missing `cryptography`, missing FastAPI/`pydantic_settings`, case config fixture). Those stay out of scope.

## 2371 — docs DEM mirror path — 2026-11-06
- `docs/sensecrew/bedrock/specs/tests/test_dem_fixture_golden.py` resolves DEM fixtures from `__file__` (sar-rooted), matching the dispatched test. This specs copy is not dispatched by `registry.py`. It originates on #41 (`8c98804`); #41 @ c933dd7 had not yet updated the mirror.
- GDD v0.5 §4 / §4a remains the coverage-model pointer. GDD v0.5 is not yet published; that is a known hold until Loam's draft lands. M1_W_KM is None until a cited W exists.
- Counts re-run: fusion 26 passed (cwd `sar/`); `pytest sar/sensegame` 92 passed (repo root); `pytest sensegame` 92 passed (cwd `sar/`); language scan 16 passed (cwd `sar/`); registry coverage 3 passed (cwd `sar/`). `registry.py --test-all` exit 1 only from pre-existing components 100, 700, and 900 (out of scope; Triage WR).

## 2371 — geo-key guard and seed drift — 2026-11-06
- `GEO_KEYS` now also rejects geohash, bbox, crs, epsg, easting, northing, polygon, point, location, geojson, x_coord, y_coord, utm, and mgrs, case-insensitively, including keys nested in dicts and lists. The rejection names the canonical key and does not include the field value. `test_rejects_geographic_fields` covers every key at the root, in a dict, and in a list. `test_rejects_mixed_case_geographic_fields` covers mixed case.
- `seeds.jsonl` stays append-only. A different hash for the same seed exits 1 and appends nothing. `--accept-drift` appends a record with `drift_from` set to the sha256 of the previous record. The same output hashes do not append. Covered by `test_seed_drift_refuses_to_append`, `test_seed_accept_drift_appends_with_drift_from`, and `test_seed_same_hash_does_not_append`.
- Follow-ups with issue links: raw bootstrap percentiles are https://github.com/midnghtsapphire/forensicfinders/issues/52 (seeded bytes; Verity delta). Dependency pins are https://github.com/midnghtsapphire/forensicfinders/issues/53. M1_W_KM is None until a cited W exists. GDD v0.5 §4 / §4a remains the coverage-model pointer.
- Counts: fusion 126 passed (cwd `sar/`, `pytest sensegame/fusion/tests`); `pytest sar/sensegame` 192 passed (repo root); language scan 16 passed (cwd `sar/`); registry coverage 3 passed (cwd `sar/`).

## 2371 — replay compares output fields only — 2026-11-06
- `--replay` uses the same `_outputs` view as `record_run`, so `drift_from` is not part of the comparison. An accepted drift, including two accepted drifts in a row, replays when the outputs match.
- A real mismatch exits nonzero, appends nothing, and prints `REPLAY_MISMATCH` with differing key names (at most 10) and SHA-256 digests of the normalized outputs. Field values are not printed.
- M1_W_KM is None until a cited W exists. GDD v0.5 §4 / §4a remains the coverage-model pointer.
- Counts: fusion 129 passed (cwd `sar/`, `pytest sensegame/fusion/tests`); `pytest sar/sensegame` 195 passed (repo root); language scan 16 passed (cwd `sar/`); registry coverage 3 passed (cwd `sar/`).

## 2371 — Strata seed 1003 replay regression — 2026-11-06
- `test_strata_seed_1003_accept_drift_then_replay` runs `python -m sensegame.fusion` from cwd `sar/` with seed 1003 and a temporary `seeds.jsonl`. It tampers the last hex digit of `fusion_1003.json`, accepts the drift, and replays successfully. A second tamper plus `--accept-drift` also replays. A further tamper replayed without that flag exits nonzero, appends nothing, and prints only `REPLAY_MISMATCH`, the differing key name, and SHA-256 digests.
- M1_W_KM is None until a cited W exists. GDD v0.5 §4 / §4a remains the coverage-model pointer.
- Counts: fusion 130 passed (cwd `sar/`, `pytest sensegame/fusion/tests`); `pytest sar/sensegame` 196 passed (repo root); language scan 16 passed (cwd `sar/`); registry coverage 3 passed (cwd `sar/`).

## 2371 — raw bootstrap percentiles (#52) — 2026-11-11
- `score_scene` now writes `ci_low`/`ci_high` as the raw 2.5 and 97.5 bootstrap percentiles. It no longer widens the band with `min(lo, p)` / `max(hi, p)` to force the calibrated probability inside.
- `check_banded` still refuses a missing, null, or inverted band and still requires `n_boot == 1000` and ECE ≤ 0.05. It no longer rejects a record solely because `p` sits outside the raw percentile band; that fact is published, not treated as a write error.
- Tests: `test_check_banded_accepts_p_outside_raw_percentiles`, `test_published_ci_are_raw_bootstrap_percentiles`. Seeded outputs are offered for a Verity delta check (issue #52 / TriageChief). On seed 1002 the pre-change widening was a no-op (every cell's `p` already lay in the raw band); other seeds may still differ.
- M1_W_KM is None until a cited W exists.
## 2371 — pin pytest and scipy (#53) — 2026-11-11
- `requirements-fusion.txt` now pins `pytest==9.2.0` and `scipy==1.18.1` (pyod and scikit-learn both import scipy on the anomaly path). Existing pins unchanged: numpy==2.2.6, scikit-learn==1.6.1, pyod==3.6.7, rasterio==1.4.3.
- `test_fusion_requirement_pins` fails if that pin set changes or if any listed requirement is unpinned.
- Versions recorded from the fusion/Verity review venvs on 2026-11-11; venv-fusion site-packages were refreshed 2026-11-10, so this is not a recovered 2026-11-05 pip freeze. M1_W_KM is None until a cited W exists.
