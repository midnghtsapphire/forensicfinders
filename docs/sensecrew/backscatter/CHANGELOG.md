# SenseCrew Backscatter CHANGELOG

## WR #43 — sentinel.fetch_sentinel_ndvi → DataArrays (Discussion #45 option B) — 2026-11-05

- `sar/coldtrace/backend/services/sentinel.py`: parse Process API GeoTIFF bodies with `io.BytesIO` + `rioxarray.open_rasterio(masked=True)`, squeeze to 2-D, map nodata `-9999` → NaN, fail loud on missing CRS or identity/missing transform; return `tuple[xr.DataArray, xr.DataArray]`. Docstring no longer claims rioxarray is absent (#9 correction). `NoDataError` path unchanged.
- Added `geotiff_bytes_to_ndvi_dataarray` helper for offline unit testing without live Sentinel Hub.
- Tests: `sar/coldtrace/backend/tests/test_sentinel_dataarray.py` + synthetic fixture `tests/fixtures/ndvi_3x3_synthetic.tif`. Assert DataArray, `.rio.crs` / `.rio.transform()`, `-9999`→NaN, missing CRS raises, identity transform raises, golden values byte-identical across two runs, mocked Hub fetch returns DataArrays.
- ColdTrace backend pytest: 16 passed (including `tests/test_no_data.py`).
- Sources / decide: Discussion #45 decide comment + Verity gates; issue #43.
- Licences cited: rioxarray Apache-2.0, xarray Apache-2.0, rasterio BSD-3-Clause.
