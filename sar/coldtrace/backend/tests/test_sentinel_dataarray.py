"""Offline tests for WR #43: fetch_sentinel_ndvi returns xarray DataArrays.

Synthetic GeoTIFF fixtures only — never calls live Sentinel Hub.
Gates (Discussion #45 / Verity): DataArray + .rio CRS/transform; -9999→NaN;
missing CRS fails loud; golden values byte-stable across two runs.
"""

from __future__ import annotations

import io
from typing import Any

import numpy as np
import pytest
import rasterio
import xarray as xr
from rasterio.transform import from_origin

from coldtrace.backend.services import sentinel


# Deterministic synthetic NDVI grid (seeded construction; fixed literals).
# Row-major float32. Index (1, 1) is Sentinel Hub nodata sentinel -9999.
_GOLDEN_NDVI = np.array(
    [
        [0.10, 0.20, 0.30],
        [0.40, -9999.0, 0.50],
        [0.60, 0.70, 0.80],
    ],
    dtype=np.float32,
)
_GOLDEN_WEST = -105.05
_GOLDEN_NORTH = 40.05
_GOLDEN_RES = 0.01  # deg


def _synthetic_geotiff_bytes(
    data: np.ndarray,
    *,
    crs: str | None = "EPSG:4326",
    nodata: float = -9999.0,
    west: float = _GOLDEN_WEST,
    north: float = _GOLDEN_NORTH,
    res: float = _GOLDEN_RES,
) -> bytes:
    """Build a single-band FLOAT32 GeoTIFF in memory (name path uses 'synthetic')."""
    height, width = data.shape
    transform = from_origin(west, north, res, res)
    buf = io.BytesIO()
    profile: dict[str, Any] = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "transform": transform,
        "nodata": nodata,
    }
    if crs is not None:
        profile["crs"] = crs
    with rasterio.open(buf, "w", **profile) as dst:
        dst.write(data.astype(np.float32), 1)
    return buf.getvalue()


@pytest.fixture
def synthetic_ndvi_tiff_bytes() -> bytes:
    return _synthetic_geotiff_bytes(_GOLDEN_NDVI)


@pytest.fixture
def synthetic_ndvi_tiff_no_crs_bytes() -> bytes:
    return _synthetic_geotiff_bytes(_GOLDEN_NDVI, crs=None)


def test_geotiff_bytes_to_dataarray_returns_xarray(synthetic_ndvi_tiff_bytes: bytes):
    da = sentinel.geotiff_bytes_to_ndvi_dataarray(synthetic_ndvi_tiff_bytes)
    assert isinstance(da, xr.DataArray)


def test_geotiff_bytes_to_dataarray_has_crs_and_transform(synthetic_ndvi_tiff_bytes: bytes):
    da = sentinel.geotiff_bytes_to_ndvi_dataarray(synthetic_ndvi_tiff_bytes)
    assert da.rio.crs is not None
    assert str(da.rio.crs) in ("EPSG:4326", "epsg:4326") or da.rio.crs.to_epsg() == 4326
    transform = da.rio.transform()
    assert transform is not None
    # Non-identity affine: pixel size must match fixture
    assert transform.a == pytest.approx(_GOLDEN_RES)
    assert transform.e == pytest.approx(-_GOLDEN_RES)


def test_geotiff_bytes_to_dataarray_maps_nodata_minus9999_to_nan(
    synthetic_ndvi_tiff_bytes: bytes,
):
    da = sentinel.geotiff_bytes_to_ndvi_dataarray(synthetic_ndvi_tiff_bytes)
    values = np.asarray(da.values, dtype=float)
    assert values.shape == (3, 3)
    assert np.isnan(values[1, 1]), "Sentinel Hub nodata -9999 must become NaN"
    # Finite cells must not be poisoned
    assert values[0, 0] == pytest.approx(0.10, abs=1e-6)
    assert values[2, 2] == pytest.approx(0.80, abs=1e-6)
    assert not np.any(values == -9999.0)


def test_geotiff_bytes_to_dataarray_missing_crs_raises(
    synthetic_ndvi_tiff_no_crs_bytes: bytes,
):
    with pytest.raises(ValueError, match=r"(?i)crs"):
        sentinel.geotiff_bytes_to_ndvi_dataarray(synthetic_ndvi_tiff_no_crs_bytes)


def test_geotiff_bytes_to_dataarray_identity_transform_raises():
    """Fail loud when GeoTIFF has CRS but only an identity transform (no georef)."""
    import rasterio
    from affine import Affine
    from rasterio.io import MemoryFile

    data = _GOLDEN_NDVI.copy()
    profile = {
        "driver": "GTiff",
        "height": 3,
        "width": 3,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": Affine.identity(),
        "nodata": -9999.0,
    }
    with MemoryFile() as mem:
        with mem.open(**profile) as dst:
            dst.write(data, 1)
        tiff_bytes = mem.read()
    with pytest.raises(ValueError, match=r"(?i)transform"):
        sentinel.geotiff_bytes_to_ndvi_dataarray(tiff_bytes)


def test_golden_values_byte_identical_run_a(synthetic_ndvi_tiff_bytes: bytes):
    """Golden run A: fixed synthetic TIFF → fixed float32 payload bytes."""
    da = sentinel.geotiff_bytes_to_ndvi_dataarray(synthetic_ndvi_tiff_bytes)
    payload = np.asarray(da.values, dtype=np.float32).tobytes()
    # Expected: same layout as _GOLDEN_NDVI with -9999 replaced by NaN
    expected = _GOLDEN_NDVI.copy()
    expected[1, 1] = np.nan
    assert payload == expected.astype(np.float32).tobytes()


def test_golden_values_byte_identical_run_b(synthetic_ndvi_tiff_bytes: bytes):
    """Golden run B: second independent conversion of the same input must match run A."""
    da_a = sentinel.geotiff_bytes_to_ndvi_dataarray(synthetic_ndvi_tiff_bytes)
    da_b = sentinel.geotiff_bytes_to_ndvi_dataarray(synthetic_ndvi_tiff_bytes)
    assert np.asarray(da_a.values, dtype=np.float32).tobytes() == np.asarray(
        da_b.values, dtype=np.float32
    ).tobytes()
    expected = _GOLDEN_NDVI.copy()
    expected[1, 1] = np.nan
    assert np.asarray(da_b.values, dtype=np.float32).tobytes() == expected.astype(
        np.float32
    ).tobytes()


@pytest.mark.asyncio
async def test_fetch_sentinel_ndvi_returns_dataarrays_with_mocked_hub(
    mocker, synthetic_ndvi_tiff_bytes: bytes
):
    """End-to-end fetch path with HTTP mocked — no live Sentinel Hub."""
    mocker.patch.object(sentinel.settings, "sentinel_hub_client_id", "test-client")
    mocker.patch.object(sentinel.settings, "sentinel_hub_client_secret", "test-secret")
    mocker.patch.object(sentinel, "_get_token", return_value="fake-token")

    class _FakeResp:
        def __init__(self, content: bytes):
            self.content = content

        def raise_for_status(self) -> None:
            return None

    class _FakeClient:
        def __init__(self, *args: Any, **kwargs: Any):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args: Any):
            return None

        async def post(self, url: str, **kwargs: Any):
            assert "sentinel-hub.com" in url or url.endswith("/process") or True
            # Never hit the network; return synthetic TIFF for both epochs
            return _FakeResp(synthetic_ndvi_tiff_bytes)

    mocker.patch.object(sentinel.httpx, "AsyncClient", _FakeClient)

    before, after = await sentinel.fetch_sentinel_ndvi(
        ( -105.06, 40.02, -105.02, 40.06),
        "2020-01-01",
        "2020-02-01",
    )
    assert isinstance(before, xr.DataArray)
    assert isinstance(after, xr.DataArray)
    assert before.rio.crs is not None
    assert after.rio.transform() is not None
    assert np.isnan(np.asarray(before.values)[1, 1])
    assert np.isnan(np.asarray(after.values)[1, 1])
