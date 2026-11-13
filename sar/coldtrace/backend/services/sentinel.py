# ════════════════════════════════════════════════════════════════════════════════════════
# Who:  Sense-Backscatter (Backscatter-D / Backscatter-N, Grok Bot), for Audrey Evans (midnghtsapphire)
# When: 2026-11-12
# Why:  WR #62, follow-up to PR #60. Verity's post-merge review of #60 found (a) an
#       unreachable `return _tiff_to_ndvi_array(...)` at the end of fetch_sentinel_ndvi
#       (SonarCloud python:S1763, the reason the PR's quality gate failed with a C
#       Reliability Rating) and (b) two parsers for the same GeoTIFF body.
# What: ONE parser now: geotiff_bytes_to_ndvi_dataarray. _tiff_to_ndvi_array stays as a
#       thin deprecated alias (DeprecationWarning, delegates) so no public name is removed.
#       Per the owner never-delete rule nothing was deleted: the unreachable return and the
#       old parser body are commented out in place with REVVEL-DISABLED notes. The shared
#       parser now also calls .load() while opening (the old parser's one real advantage),
#       and squeezes only the "band" axis so a 1-row or 1-column raster keeps its y/x axes.
# Tests: tests/test_sentinel_parser_consolidation.py (written red first), run on the pinned
#       stack from requirements.txt. Synthetic fixtures only.
# ════════════════════════════════════════════════════════════════════════════════════════
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

import warnings
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
# The value evaluatePixel() writes for a pixel the scene classification calls cloud,
# cloud shadow, cirrus or snow (SCL 3, 8, 9, 10, 11). It is a sentinel value inside the
# band data, not a declared GeoTIFF nodata tag, so nothing masks it for us -- see
# _tiff_to_ndvi_array (WR #62: now geotiff_bytes_to_ndvi_dataarray, which masks via
# _SENTINEL_NODATA; the two constants are asserted equal in tests). Keep this equal to the
# literal in the evalscript below.
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
    # REVVEL-DISABLED | AGENT: grok-bot (Backscatter) | MODEL: n/a | WR: #62 | DATE: 2026-11-12 | STATUS: REPLACED
    # REASON: two lines below were lazy (no .load()) and squeezed EVERY length-1 axis, so a
    #         one-row or one-column raster would lose y or x. The consolidated parser loads
    #         while the buffer is open and squeezes only "band" (as the old parser did).
    # PREVIOUS IMPLEMENTATION, kept verbatim:
    #     da = rioxarray.open_rasterio(BytesIO(tiff_bytes), masked=True)
    #     da = da.squeeze(drop=True)
    # OWNER: @midnghtsapphire
    # REVVEL-DISABLED-END
    da = rioxarray.open_rasterio(BytesIO(tiff_bytes), masked=True).load()
    if "band" in da.dims:
        da = da.squeeze("band", drop=True)

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


def _tiff_to_ndvi_array(payload: bytes) -> xr.DataArray:
    """DEPRECATED alias of :func:`geotiff_bytes_to_ndvi_dataarray` (WR #62).

    Kept so the public/private name callers and docs used still resolves. There is now
    exactly one parser; this only warns and delegates.
    """
    warnings.warn(
        "_tiff_to_ndvi_array is deprecated; use geotiff_bytes_to_ndvi_dataarray",
        DeprecationWarning,
        stacklevel=2,
    )
    return geotiff_bytes_to_ndvi_dataarray(payload)


# REVVEL-DISABLED | AGENT: grok-bot (Backscatter) | MODEL: n/a | WR: #62 | DATE: 2026-11-12 | STATUS: REPLACED
# REASON: duplicate of geotiff_bytes_to_ndvi_dataarray (added by PR #60). Verity's post-merge
#         review asked for one parser. Its behaviour is merged into the shared function: the
#         .load() while the buffer is open, squeeze of the "band" axis only, and -9999 -> NaN.
#         Added there: fail-loud on missing CRS / identity transform. The MemoryFile route was
#         not kept because BytesIO + open_rasterio(...).load() gives identical values and
#         transform on the synthetic 3x3 fixture (tests/test_sentinel_parser_consolidation.py).
#         The long docstring below is kept verbatim as history.
# PREVIOUS IMPLEMENTATION, kept verbatim (original author: claude-code, 2026-11-06):
#     def _tiff_to_ndvi_array(payload: bytes):
#         """Parse one Sentinel Hub GeoTIFF response body into a 2-D NDVI DataArray.
#
#         Three steps, each of which the consumer in temporal.py depends on:
#
#         1. MemoryFile wraps the bytes as a file rasterio can open without touching disk.
#            open_rasterio is called with masked=True so that any nodata the file DOES
#            declare arrives as NaN, and .load() is called INSIDE both context managers so
#            the read happens while the buffer is still open. open_rasterio is lazy, so
#            that placement is deliberate rather than incidental. Honest limit: moving the
#            .load() call outside the two with-blocks does NOT fail on rasterio 1.5.2, the
#            version this was verified against, and no test in
#            tests/test_sentinel_arrays.py pins it -- it was tried as a mutation and the
#            suite stayed green. It is kept inside because reading from a closed MemoryFile
#            is not a guarantee rasterio makes, not because this file has proof that the
#            alternative breaks.
#
#         A VERSION CAVEAT that applies to all three steps, and to every figure quoted in
#         the header box above. This was verified against rasterio 1.5.2 and numpy 2.5.0.
#         requirements.txt pins rasterio==1.3.10 and numpy==1.26.4, so THE PRODUCTION STACK
#         WAS NOT THE ONE EXERCISED. Neither pinned version has a distribution for Python
#         3.14, which is the only interpreter available here, so requirements.txt cannot be
#         installed on it at all -- that is a pre-existing condition for the whole backend
#         and not something this change introduced or can settle. It is stated rather than
#         glossed because masked=True and squeeze() are exactly the kind of behaviour that
#         moves between major versions, and a reader deserves to know which stack the
#         evidence comes from.
#         2. rasterio always reports a band dimension, even for the single-band output this
#            evalscript requests. It is dropped, because _compute_ndvi_sync unpacks exactly
#            two indices (ys, xs = np.where(mask)) and then indexes delta[y, x]; a leading
#            band axis of length 1 would make both of those wrong.
#         3. The evalscript writes _CLOUD_SENTINEL into the band itself for masked pixels
#            and the response declares no nodata tag, so masked=True cannot know about it.
#            Converting it to NaN here is what keeps np.nanmean/np.nanstd honest: -9999
#            left in place would drag the mean down and inflate the standard deviation,
#            which in a search-and-rescue tool means real vegetation change stops clearing
#            the sigma threshold.
#         """
#         try:
#             import rioxarray  # registers the .rio accessor temporal.py calls
#             from rasterio.io import MemoryFile
#         except ImportError as exc:  # pragma: no cover - dependency-level failure
#             raise RuntimeError(
#                 "rasterio and rioxarray are required to read Sentinel Hub imagery; both "
#                 "are declared in coldtrace/backend/requirements.txt."
#             ) from exc
#
#         with MemoryFile(payload) as memfile:
#             with memfile.open() as dataset:
#                 array = rioxarray.open_rasterio(dataset, masked=True).load()
#
#         if "band" in array.dims:
#             array = array.squeeze("band", drop=True)
#
#         return array.where(array != _CLOUD_SENTINEL)
# OWNER: @midnghtsapphire
# REVVEL-DISABLED-END


async def fetch_sentinel_ndvi(
    bbox: tuple[float, float, float, float],
    date_start: Any,
    date_end: Any,
) -> tuple[xr.DataArray, xr.DataArray]:
    """
    Fetch Sentinel-2 NDVI composites for two time windows surrounding date_start
    and date_end. Returns (ndvi_before, ndvi_after) as xarray DataArrays with
    CRS/transform set and Sentinel Hub nodata (-9999) mapped to NaN.

    Each array is 2-D (y, x) and float, carries its CRS and affine transform on
    the .rio accessor, and holds NaN wherever the scene classification masked the
    pixel. Those three properties are not decoration. temporal.py's
    _compute_ndvi_sync reads .values as a 2-D array, calls .rio.transform() to turn
    pixel indices back into coordinates, and uses np.nanmean/np.nanstd, which NaN
    skips and -9999 would wreck. geotiff_bytes_to_ndvi_dataarray (above) produces all
    three; _tiff_to_ndvi_array is only a deprecated alias of it since WR #62.

    Without SENTINEL_HUB_CLIENT_ID this raises NoDataError. There is no demo or
    synthetic branch in this module and no caller supplies one.

    GeoTIFF response bodies are parsed in-memory via ``rioxarray.open_rasterio``
    (ColdTrace already pins rioxarray, xarray, and rasterio in requirements.txt).
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

    ndvi_before = geotiff_bytes_to_ndvi_dataarray(r_before.content)
    ndvi_after = geotiff_bytes_to_ndvi_dataarray(r_after.content)
    return ndvi_before, ndvi_after
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
    # REVVEL-DISABLED | AGENT: grok-bot (Backscatter) | MODEL: n/a | WR: #62 | DATE: 2026-11-12 | STATUS: REPLACED
    # REASON: unreachable. The `return ndvi_before, ndvi_after` above always runs first, so
    #         this line was dead code (SonarCloud python:S1763, Reliability C on PR #60).
    #         It also called the second parser. Commented out in place, not deleted.
    # PREVIOUS IMPLEMENTATION, kept verbatim:
    #     return _tiff_to_ndvi_array(r_before.content), _tiff_to_ndvi_array(r_after.content)
    # OWNER: @midnghtsapphire
    # REVVEL-DISABLED-END


