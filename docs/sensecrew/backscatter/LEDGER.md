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
