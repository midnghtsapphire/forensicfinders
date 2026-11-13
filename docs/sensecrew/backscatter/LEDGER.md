# SenseCrew Backscatter LEDGER (append-only)

## 2026-11-05 12:02 MST — Sense-Backscatter (Backscatter-D / Backscatter-N, Grok Bot) — WR #43 option B (Discussion #45)

- **Actor:** Sense-Backscatter (Backscatter-D drive, Backscatter-N review)
- **Requested by:** Proofy decide on Discussion #45 (option B with Verity gates), for Audrey Evans / Sense-Strata WR #43
- **Role:** executed (code + offline tests on branch; draft PR only; not merged)
- **Why:** WR #43 / Discussion #45 decide — convert `fetch_sentinel_ndvi` from `tuple[bytes, bytes]` to `tuple[DataArray, DataArray]` via already-pinned rioxarray so `analysis.py` → `temporal.compute_ndvi_diff` (`.values` / `.rio.transform()` / `nanmean`) works.
- **Sources:**
  - Issue https://github.com/midnghtsapphire/forensicfinders/issues/43
  - Discussion decide https://github.com/midnghtsapphire/forensicfinders/discussions/45#discussioncomment-19424762
  - Verity 3 gates https://github.com/midnghtsapphire/forensicfinders/discussions/45#discussioncomment-19424753
  - rioxarray Apache-2.0: https://pypi.org/project/rioxarray/ · https://raw.githubusercontent.com/corteva/rioxarray/master/LICENSE
  - xarray Apache-2.0: https://pypi.org/project/xarray/ · https://raw.githubusercontent.com/pydata/xarray/main/LICENSE
  - rasterio BSD-3-Clause: https://pypi.org/project/rasterio/ · https://raw.githubusercontent.com/rasterio/rasterio/main/LICENSE.txt
- **Files (branch `sensecrew/backscatter/wr43-sentinel-dataarray`):**
  - `sar/coldtrace/backend/services/sentinel.py` (changed — `geotiff_bytes_to_ndvi_dataarray`; DataArray return; docstring fixes #9 false “rioxarray not installed”; NoDataError path unchanged)
  - `sar/coldtrace/backend/tests/test_sentinel_dataarray.py` (added — offline unit tests; mock Hub HTTP)
  - `sar/coldtrace/backend/tests/fixtures/ndvi_3x3_synthetic.tif` (added — synthetic FLOAT32 NDVI GeoTIFF; name contains `synthetic`)
  - `docs/sensecrew/backscatter/LEDGER.md`, `docs/sensecrew/backscatter/CHANGELOG.md` (added — this crew ledger; main has no root LEDGER)
- **Gates met:**
  1. `BytesIO` + `rioxarray.open_rasterio(..., masked=True)` + squeeze; ValueError if CRS missing or transform missing/identity
  2. `-9999` → NaN in sentinel return path (`masked=True` + explicit `where`)
  3. Offline synthetic TIFF tests (DataArray, `.rio`, nodata, golden ×2, missing CRS, identity transform, mocked Hub fetch); no live Sentinel Hub
- **Commands / tools:** `gh` (auth midnghtsapphire), `git`, `python -m pytest` with venv (`--system-site-packages`; host Python 3.13 could not install exact pins `rasterio==1.3.10` / `rioxarray==0.15.5` / `xarray==2024.5.0` — ran against available wheels rasterio 1.5.2 / rioxarray 0.24.0 / xarray 2026.9.0; requirements.txt pins unchanged), Cursor GitHub MCP reads for Discussion #45 comments. No Discussion/issue comments posted.
- **Not accessed:** case/, hfmr/, dossier.py, evidence/, public_records_engine.py, Ultralytics, GPL-linked code
- **Licence:** UNLICENSED (private repo; licence pending Audrey). Runtime deps used: rioxarray Apache-2.0, xarray Apache-2.0, rasterio BSD-3-Clause (already in ColdTrace requirements.txt; no new dep class).
- **Approval:** Backscatter-N APPROVE sentinel.py+tests DataArray conversion (gates 1-3, nodata, determinism, licences) — reviewed: gates 1-3, tests, licences
- **Credit note:** drafted and implemented entirely by Grok Bot (Backscatter pair). Draft PR only — awaiting Verity re-check; no self-merge.

- **Tip commit (post-commit):** Backscatter-N APPROVE ec2fc25 — reviewed: gates 1-3, tests, licences

## 2026-11-12 18:29 MST — Sense-Backscatter (Backscatter-D / Backscatter-N, Grok Bot) — WR #62 sentinel cleanup (follow-up to PR #60)

- **Actor:** Sense-Backscatter (Backscatter-D drive, Backscatter-N review)
- **Requested by:** Sense-Strata, for Audrey Evans — WR #62 (Verity post-merge review of #60: process FAIL 0.75, code PASS-with-notes 0.70)
- **Role:** executed (code + offline tests + CI config on branch; draft PR only; not merged; #60 NOT reverted)
- **Why:** WR #62 — (1) unreachable `return` at sentinel.py L286 (SonarCloud python:S1763 = the Quality Gate failure on #60: new_reliability_rating C, required A; it was the only open Sonar issue on PR #60); (2) duplicate GeoTIFF/NDVI parser (`geotiff_bytes_to_ndvi_dataarray` + `_tiff_to_ndvi_array`); (3) tests never ran on the pins in requirements.txt (rasterio 1.3.10 / rioxarray 0.15.5 / xarray 2024.5.0); (4) Sonar gate triage.
- **Provenance of #60 (GitHub API):** opened 2026-11-12T20:54:36Z by `midnghtsapphire`, merged 20:54:59Z by `midnghtsapphire` (merge commit d3c75696). Both are Audrey's shared account/token; the API cannot say which agent or person acted. Not Backscatter's action; Backscatter did not merge it.
- **Branch note:** `daily/2026-11-12` did not exist. Created from current `main` (8bcce8ed) as a new ref via the GitHub git-refs API (no force, no commit pushed to it), on the parent agent's instruction, then `sensecrew/backscatter/wr62-sentinel-cleanup` was branched from it.
- **Sources:**
  - Issue https://github.com/midnghtsapphire/forensicfinders/issues/62 · PR https://github.com/midnghtsapphire/forensicfinders/pull/60 · earlier draft https://github.com/midnghtsapphire/forensicfinders/pull/46
  - SonarCloud public API (project midnghtsapphire_forensicfinders, pullRequest=60): `qualitygates/project_status` and `issues/search`
  - revvel-standards AGENTS.md (owner rule: never delete, never rewrite; retire by commenting out in place with a dated note)
  - Licences: rasterio BSD-3-Clause, rioxarray Apache-2.0, xarray Apache-2.0, numpy/scipy/shapely/pandas BSD-3-Clause, fastapi/pydantic/pydantic-settings/whitebox MIT, httpx BSD-3-Clause, pytest MIT, pytest-asyncio Apache-2.0 (all already in requirements.txt except the pytest trio; no new dependency class; no Ultralytics, no GPL)
- **Files:**
  - `sar/coldtrace/backend/services/sentinel.py` (changed — one shared parser; `_tiff_to_ndvi_array` kept as DeprecationWarning alias; L286 return and old parser body COMMENTED OUT in place with REVVEL-DISABLED notes; shared parser now `.load()`s and squeezes only the `band` axis; docstring references fixed)
  - `sar/coldtrace/backend/tests/test_sentinel_parser_consolidation.py` (added — 16 offline tests, synthetic only; of the first 13, 6 failed before the fix, 3 further guards were added afterwards)
  - `sar/coldtrace/backend/requirements-test-pinned.txt` (added — exact pins copied from requirements.txt for the packages the tests import; requirements.txt itself not installable on plain CI: gdal/pdal need native builds)
  - `.circleci/config.yml` (changed, additive — new job `coldtrace-pinned` on python:3.12-bookworm; existing `test` job untouched)
  - `docs/sensecrew/backscatter/LEDGER.md`, `CHANGELOG.md` (appended)
- **Commands / tools:** `gh` (auth midnghtsapphire; REST reads, one `git/refs` create for daily/2026-11-12), `git`, `curl` to the public SonarCloud API, `uv` venvs, `pytest`. No Discussion/issue comments posted.
- **Test results (pinned stack, offline, synthetic):**
  - Baseline of #60 code on pins (before edits): `python -m pytest -q -p no:warnings coldtrace/backend/tests` = 24 passed.
  - RED before fix: new file 6 failed / 6 passed / 1 skipped.
  - AFTER fix, CPython 3.12.16, numpy 1.26.4, rasterio 1.3.10, rioxarray 0.15.5, xarray 2024.5.0, scipy 1.13.1, shapely 2.0.4, pandas 2.2.2, fastapi 0.111.0, pydantic 2.7.1, pydantic-settings 2.3.0, httpx 0.27.0, whitebox 2.3.4, pytest 9.2.0, pytest-asyncio 1.5.0, pytest-mock 3.17.0, COLDTRACE_PINNED_ENV=1: **40 passed, 0 failed, 0 skipped**.
  - Also CPython 3.11.18 on the same pins: 40 passed.
  - NOT run: the CircleCI job itself inside the python:3.12-bookworm image (local docker out of disk); see PR body for the real CircleCI result.
- **Not accessed:** case/, hfmr/, dossier.py, evidence/, public_records_engine.py, Ultralytics, GPL-linked code
- **Licence:** UNLICENSED (private repo; licence pending Audrey).
- **Approval:** Backscatter-N APPROVE line is appended below as its own entry once the reviewed commit SHA exists (the SHA cannot be inside the commit it names).
- **Credit note:** drafted and implemented by Grok Bot (Backscatter pair). Draft PR only — no self-merge; Verity re-check requested.

## 2026-11-12 18:30 MST — Backscatter-N Navigator review — WR #62 (append-only; separate pass over the full diff of 0f92628)

- **Reviewed:** full diff of commit 0f9262830eef17cd3a2021532c614a548724d990 (sentinel.py, new tests, requirements-test-pinned.txt, .circleci/config.yml, LEDGER, CHANGELOG), read as a separate pass after the drive pass; pyflakes clean on sentinel.py and the new test file; `git diff --check` clean; tests re-run on the committed tree: 40 passed on the pinned stack (CPython 3.12.16).
- **Findings:** no deletions (only commented-out blocks with dated REVVEL-DISABLED notes, original text preserved verbatim); no file under case/, hfmr/, dossier.py, evidence/, public_records_engine.py touched; no live Sentinel Hub calls; no new dependency class; CircleCI change is additive. Residual risks stated in the PR: Sonar re-analysis and the CircleCI run happen on GitHub, not here; commented-out code may raise a Sonar maintainability smell (not part of the failed Reliability condition).
- Backscatter-N APPROVE 0f92628 — reviewed: L286 dead return, parser dedupe, pinned tests, Sonar

## 2026-11-12 18:33 MST — Sense-Backscatter — WR #62 follow-up fixes on PR #64 (append-only)

- **Why:** two real findings after opening the draft PR, both from the PR's own checks:
  1. **CircleCI config error** (CircleCI `list_runs`, runs on 28f9b51 and 5933296: `Unclosed '<<' tag`; no job ran). My `python3 - <<'PY'` heredoc must be escaped in config v2.1. Replaced with a `python3 -c` one-liner, no heredoc. Validated with CircleCI `validate_config` (valid). Additive change to the same `coldtrace-pinned` job only.
  2. **Sonar on PR #64:** Quality Gate PASSED (the #60 failure condition is gone). 3 new code smells in my new test file (python:S9088, S9073, S5778: more than one call inside `pytest.warns`/`pytest.raises`, composite assert). Fixed in commit 5933296 by building the payload before the `with` block and splitting the assert; no behaviour change, 40 passed.
- **Commands / tools:** CircleCI MCP (read-only list_runs, validate_config), SonarCloud public API (read), `pytest`.
- **Test results:** after both fixes, CPython 3.12.16 on the pins (rasterio 1.3.10, rioxarray 0.15.5, xarray 2024.5.0, numpy 1.26.4): 40 passed. The version-assert one-liner was also run locally and passed.
