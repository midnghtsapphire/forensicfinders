# SenseCrew Backscatter CHANGELOG

## WR #43 — sentinel.fetch_sentinel_ndvi → DataArrays (Discussion #45 option B) — 2026-11-05

- `sar/coldtrace/backend/services/sentinel.py`: parse Process API GeoTIFF bodies with `io.BytesIO` + `rioxarray.open_rasterio(masked=True)`, squeeze to 2-D, map nodata `-9999` → NaN, fail loud on missing CRS or identity/missing transform; return `tuple[xr.DataArray, xr.DataArray]`. Docstring no longer claims rioxarray is absent (#9 correction). `NoDataError` path unchanged.
- Added `geotiff_bytes_to_ndvi_dataarray` helper for offline unit testing without live Sentinel Hub.
- Tests: `sar/coldtrace/backend/tests/test_sentinel_dataarray.py` + synthetic fixture `tests/fixtures/ndvi_3x3_synthetic.tif`. Assert DataArray, `.rio.crs` / `.rio.transform()`, `-9999`→NaN, missing CRS raises, identity transform raises, golden values byte-identical across two runs, mocked Hub fetch returns DataArrays.
- ColdTrace backend pytest: 16 passed (including `tests/test_no_data.py`).
- Sources / decide: Discussion #45 decide comment + Verity gates; issue #43.
- Licences cited: rioxarray Apache-2.0, xarray Apache-2.0, rasterio BSD-3-Clause.

## WR #62 — sentinel parser cleanup, pinned-version tests, Sonar triage (follow-up to #60) — 2026-11-12

- `sar/coldtrace/backend/services/sentinel.py`: removed (commented out in place, not deleted) the unreachable `return _tiff_to_ndvi_array(...)` after the real return in `fetch_sentinel_ndvi` — the SonarCloud python:S1763 finding that failed #60's Quality Gate (C Reliability on new code).
- Same file: one parser. `geotiff_bytes_to_ndvi_dataarray` is canonical and now `.load()`s while opening and squeezes only the `band` axis; `_tiff_to_ndvi_array` remains as a thin DeprecationWarning alias; its old body is kept commented out. Docstring references updated.
- Added `sar/coldtrace/backend/requirements-test-pinned.txt` and CircleCI job `coldtrace-pinned` (python:3.12-bookworm) so ColdTrace backend tests run on rasterio 1.3.10 / rioxarray 0.15.5 / xarray 2024.5.0 / numpy 1.26.4.
- Added `tests/test_sentinel_parser_consolidation.py` (16 tests, synthetic only).
- ColdTrace backend pytest on the pins (CPython 3.12.16): 40 passed (24 existing + 16 new; full versions in LEDGER); also 40 passed on 3.11.18.
- #60 was not reverted.
