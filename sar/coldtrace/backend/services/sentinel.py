# ════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-06
# Why:  fetch_sentinel_ndvi promised xarray DataArrays and returned the two raw GeoTIFF
#       response bodies as bytes. That is a live AttributeError on the production path,
#       not a documentation mismatch: routers/analysis.py:85 passes both values straight
#       into compute_ndvi_diff, and services/temporal.py:52 does
#       ndvi_before.values.astype(float) -- and bytes has no .values. The NDVI change
#       endpoint could never have returned an anomaly.
# What: the two response bodies are now parsed into DataArrays by _tiff_to_ndvi_array
#       below, whose docstring explains each step. The function SIGNATURE IS UNCHANGED;
#       this makes the implementation match a contract that was already written down
#       and already relied upon, rather than renegotiating it. xarray and rioxarray
#       were already declared in requirements.txt. They were missing from
#       requirements-test.txt, which is why component 700 could not exercise this path;
#       that file now lists them too.
# What Worked: run, not asserted. Component 700: 8 passed, against a baseline of 8
#       passed measured on this branch's parent with the same dependencies installed.
#       The new tests/test_sentinel_arrays.py drives fetch_sentinel_ndvi with a stubbed
#       transport over a real FLOAT32 GeoTIFF and asserts the three properties
#       _compute_ndvi_sync actually consumes, then feeds the result through
#       compute_ndvi_diff itself so the end-to-end path is proven and not inferred.
# Notes: CORRECTING MYSELF. The docstring paragraph preserved below is mine, from PR #9,
#       and one of its claims was wrong: it said converting needs rioxarray, which this
#       repository does not install. requirements.txt has declared xarray==2024.5.0 and
#       rioxarray==0.15.5 all along, and only requirements-test.txt omitted them. It
#       also called the return type a decision about the contract that needed an owner.
#       It did not: temporal.py had already decided it. The paragraph is kept verbatim
#       rather than quietly deleted, because a file that edits out its own wrong
#       reasoning teaches the next reader nothing.
#       NOT changed here, reported instead: routers/data.py:41 unpacks both returned
#       arrays and discards them, answering {date_start, date_end, status: computed}
#       while its docstring says it returns the difference. That is a second defect and
#       GREEN_MAIN_STANDARD.md asks for one fix per PR, so it is left alone.
# ════════════════════════════════════════════════════════════════════════════════════════
"""Sentinel Hub API client for NDVI time-series.

Free research tier: 30,000 processing units/month.
Register at https://www.sentinel-hub.com to get credentials.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from ..config import settings
from ..errors import NoDataError

_TOKEN_URL = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
_PROCESS_URL = "https://services.sentinel-hub.com/api/v1/process"

# The value evaluatePixel() writes for a pixel the scene classification calls cloud,
# cloud shadow, cirrus or snow (SCL 3, 8, 9, 10, 11). It is a sentinel value inside the
# band data, not a declared GeoTIFF nodata tag, so nothing masks it for us -- see
# _tiff_to_ndvi_array. Keep this equal to the literal in the evalscript below.
_CLOUD_SENTINEL = -9999.0


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


def _tiff_to_ndvi_array(payload: bytes):
    """Parse one Sentinel Hub GeoTIFF response body into a 2-D NDVI DataArray.

    Three steps, each of which the consumer in temporal.py depends on:

    1. MemoryFile wraps the bytes as a file rasterio can open without touching disk.
       open_rasterio is called with masked=True so that any nodata the file DOES
       declare arrives as NaN, and .load() is called INSIDE both context managers so
       the read happens while the buffer is still open. open_rasterio is lazy, so
       that placement is deliberate rather than incidental. Honest limit: moving the
       .load() call outside the two with-blocks does NOT fail on rasterio 1.3 here,
       and no test in tests/test_sentinel_arrays.py pins it -- it was tried as a
       mutation and the suite stayed green. It is kept inside because reading from a
       closed MemoryFile is not a guarantee rasterio makes, not because this file
       has proof that the alternative breaks.
    2. rasterio always reports a band dimension, even for the single-band output this
       evalscript requests. It is dropped, because _compute_ndvi_sync unpacks exactly
       two indices (ys, xs = np.where(mask)) and then indexes delta[y, x]; a leading
       band axis of length 1 would make both of those wrong.
    3. The evalscript writes _CLOUD_SENTINEL into the band itself for masked pixels
       and the response declares no nodata tag, so masked=True cannot know about it.
       Converting it to NaN here is what keeps np.nanmean/np.nanstd honest: -9999
       left in place would drag the mean down and inflate the standard deviation,
       which in a search-and-rescue tool means real vegetation change stops clearing
       the sigma threshold.
    """
    try:
        import rioxarray  # registers the .rio accessor temporal.py calls
        from rasterio.io import MemoryFile
    except ImportError as exc:  # pragma: no cover - dependency-level failure
        raise RuntimeError(
            "rasterio and rioxarray are required to read Sentinel Hub imagery; both "
            "are declared in coldtrace/backend/requirements.txt."
        ) from exc

    with MemoryFile(payload) as memfile:
        with memfile.open() as dataset:
            array = rioxarray.open_rasterio(dataset, masked=True).load()

    if "band" in array.dims:
        array = array.squeeze("band", drop=True)

    return array.where(array != _CLOUD_SENTINEL)


async def fetch_sentinel_ndvi(
    bbox: tuple[float, float, float, float],
    date_start: Any,
    date_end: Any,
) -> tuple[Any, Any]:
    """
    Fetch Sentinel-2 NDVI composites for two time windows surrounding date_start
    and date_end. Returns (ndvi_before, ndvi_after) as xarray DataArrays.

    Each array is 2-D (y, x) and float, carries its CRS and affine transform on
    the .rio accessor, and holds NaN wherever the scene classification masked the
    pixel. Those three properties are not decoration. temporal.py's
    _compute_ndvi_sync reads .values as a 2-D array, calls .rio.transform() to turn
    pixel indices back into coordinates, and uses np.nanmean/np.nanstd, which NaN
    skips and -9999 would wreck. _tiff_to_ndvi_array below produces all three.

    Without SENTINEL_HUB_CLIENT_ID this raises NoDataError. There is no demo or
    synthetic branch in this module and no caller supplies one.
    """
    # REVVEL-DISABLED | AGENT: claude-code | MODEL: claude-opus-5 | WR: UNASSIGNED | DATE: 2026-11-06 | STATUS: REPLACED
    # REASON: the paragraph below is mine, from PR #9, and it was wrong on the point
    #         that mattered. It said converting the response bodies needs rioxarray,
    #         which this repository does not install. requirements.txt has declared
    #         xarray==2024.5.0 and rioxarray==0.15.5 all along, and only
    #         requirements-test.txt omitted them. It also called the return type a
    #         decision about the contract that needed an owner. It did not:
    #         temporal.py already consumed .values and .rio.transform(), so bytes
    #         could only ever raise AttributeError, and the paragraph described a live
    #         defect as an open question. Kept verbatim: the error is part of the
    #         record of how this file got here.
    # PREVIOUS DOCSTRING PARAGRAPH, kept verbatim:
    #     What this returns today is the two raw GeoTIFF response bodies as bytes, NOT
    #     DataArrays -- see the comment at the return statement. Reported, not changed
    #     here: converting them needs rioxarray, which this repository does not
    #     install, and the two callers disagree about what they want back. analysis.py
    #     passes both into compute_ndvi_diff, while data.py unpacks them and discards
    #     them. Deciding between converting and changing the signature is a decision
    #     about the contract, not a transcription.
    # OWNER: @midnghtsapphire
    # REVVEL-DISABLED-END
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

    # REVVEL-DISABLED | AGENT: claude-code | MODEL: claude-opus-5 | WR: UNASSIGNED | DATE: 2026-11-06 | STATUS: REPLACED
    # REASON: the two lines below are the defect this change fixes. They returned the
    #         raw response bodies, so every caller received bytes where the signature,
    #         the docstring and temporal.py all expected a DataArray. The comment said
    #         the parsing belonged in production, but this IS the production path --
    #         the only other branch in this function raises NoDataError. Kept verbatim
    #         so the before state of the bug stays readable beside its fix.
    # PREVIOUS IMPLEMENTATION, kept verbatim:
    #     # In production, parse the TIFF bytes into xarray DataArrays via rioxarray
    #     return r_before.content, r_after.content
    # OWNER: @midnghtsapphire
    # REVVEL-DISABLED-END
    return _tiff_to_ndvi_array(r_before.content), _tiff_to_ndvi_array(r_after.content)


