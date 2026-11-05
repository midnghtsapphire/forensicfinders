"""Sentinel Hub API client for NDVI time-series.

Free research tier: 30,000 processing units/month.
Register at https://www.sentinel-hub.com to get credentials.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from affine import Affine

import httpx
import rioxarray
import xarray as xr

from ..config import settings
from ..errors import NoDataError

_TOKEN_URL = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
_PROCESS_URL = "https://services.sentinel-hub.com/api/v1/process"

# Sentinel Hub evalscript nodata for masked SCL classes (cloud/shadow/snow/etc.).
_SENTINEL_NODATA = -9999.0


async def _get_token() -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.sentinel_hub_client_id,
                "client_secret": settings.sentinel_hub_client_secret,
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


def geotiff_bytes_to_ndvi_dataarray(tiff_bytes: bytes) -> xr.DataArray:
    """Parse a single-band Sentinel Hub GeoTIFF body into a 2-D NDVI DataArray.

    Opens in-memory bytes only (no temp path). Uses already-pinned rioxarray
    (Apache-2.0) + rasterio (BSD-3-Clause) + xarray (Apache-2.0).

    - ``masked=True`` so TIFF nodata becomes masked/NaN.
    - Explicit ``where(!= -9999)`` so evalscript nodata is NaN even if the
      TIFF tag is missing (temporal.compute_ndvi_diff uses nanmean/nanstd).
    - Squeezes the band dimension to 2-D for callers that use ``.values``.
    - Raises ``ValueError`` if CRS or affine transform is missing.
    """
    da = rioxarray.open_rasterio(BytesIO(tiff_bytes), masked=True)
    da = da.squeeze(drop=True)

    if da.rio.crs is None:
        raise ValueError(
            "Sentinel NDVI GeoTIFF is missing CRS; cannot return a georeferenced DataArray."
        )
    try:
        transform = da.rio.transform()
    except Exception as exc:
        raise ValueError(
            "Sentinel NDVI GeoTIFF is missing affine transform; cannot georeference."
        ) from exc
    if transform is None or transform == Affine.identity():
        raise ValueError(
            "Sentinel NDVI GeoTIFF is missing a non-identity affine transform; "
            "cannot georeference."
        )

    # Map Sentinel Hub evalscript nodata to NaN for every caller.
    da = da.where(da != _SENTINEL_NODATA)
    return da


async def fetch_sentinel_ndvi(
    bbox: tuple[float, float, float, float],
    date_start: Any,
    date_end: Any,
) -> tuple[xr.DataArray, xr.DataArray]:
    """
    Fetch Sentinel-2 NDVI composites for two time windows surrounding date_start
    and date_end. Returns (ndvi_before, ndvi_after) as xarray DataArrays with
    CRS/transform set and Sentinel Hub nodata (-9999) mapped to NaN.

    Without SENTINEL_HUB_CLIENT_ID this raises NoDataError. There is no demo or
    synthetic branch in this module and no caller supplies one.

    GeoTIFF response bodies are parsed in-memory via ``rioxarray.open_rasterio``
    (ColdTrace already pins rioxarray, xarray, and rasterio in requirements.txt).
    """
    # REVVEL-DISABLED | AGENT: claude-code | MODEL: claude-opus-5 | WR: UNASSIGNED | DATE: 2026-11-04 | STATUS: REPLACED
    # REASON: stale docstring line, not a code defect. It described a demo mode that does
    #         not exist -- there is no synthetic branch anywhere in this file, and
    #         coldtrace/backend/tests/test_no_data.py asserts the NoDataError raise below
    #         is the intended answer when credentials are absent. A reader trusting the
    #         line would go looking for a fallback nobody ever wrote.
    # PREVIOUS DOCSTRING LINE, kept verbatim:
    #     Demo mode returns synthetic placeholder arrays.
    # OWNER: @midnghtsapphire
    # REVVEL-DISABLED-END
    if not settings.sentinel_hub_client_id:
        raise NoDataError("Sentinel Hub credentials not set (SENTINEL_HUB_CLIENT_ID); no imagery fetched.")

    token = await _get_token()
    west, south, east, north = bbox

    evalscript = """
    //VERSION=3
    function setup() {
      return { input: ["B04","B08","SCL"], output: { bands: 1, sampleType: "FLOAT32" } };
    }
    function evaluatePixel(sample) {
      if ([3,8,9,10,11].includes(sample.SCL)) return [-9999];
      var ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
      return [ndvi];
    }
    """

    def _build_request(time_from: str, time_to: str) -> dict:
        return {
            "input": {
                "bounds": {
                    "bbox": [west, south, east, north],
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
                },
                "data": [{
                    "dataFilter": {"timeRange": {"from": f"{time_from}T00:00:00Z", "to": f"{time_to}T23:59:59Z"}},
                    "type": "sentinel-2-l2a",
                }],
            },
            "output": {
                "width": 512, "height": 512,
                "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}],
            },
            "evalscript": evalscript,
        }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=120) as client:
        r_before = await client.post(_PROCESS_URL, json=_build_request(str(date_start), str(date_start)), headers=headers)
        r_after = await client.post(_PROCESS_URL, json=_build_request(str(date_end), str(date_end)), headers=headers)
        r_before.raise_for_status()
        r_after.raise_for_status()

    ndvi_before = geotiff_bytes_to_ndvi_dataarray(r_before.content)
    ndvi_after = geotiff_bytes_to_ndvi_dataarray(r_after.content)
    return ndvi_before, ndvi_after
