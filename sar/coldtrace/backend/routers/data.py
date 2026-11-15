# ════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-14
# Why:  GET /ndvi-diff fetched both NDVI composites, bound them to ndvi_before and
#       ndvi_after, and then THREW BOTH AWAY, answering
#       {date_start, date_end, status: "computed"}. Its docstring said it returns the
#       difference. Nothing was ever differenced. Reported in PR #54 and left alone
#       there because GREEN_MAIN_STANDARD.md asks for one fix per PR; Audrey asked for
#       it next.
#       Worth saying plainly: the endpoint got WORSE when #54 landed, not better. While
#       fetch_sentinel_ndvi returned bytes this endpoint was merely useless -- it
#       discarded two values nobody could have used anyway. Now that the fetch returns
#       real DataArrays it discards real data and still answers "computed", so a client
#       asking where the ground changed gets a 200 and silence.
# What: the two arrays now go into services.temporal.compute_ndvi_diff -- the same
#       function routers/analysis.py already uses for exactly this -- and the anomalies
#       are returned under a new "anomalies" key. The three existing keys are kept
#       untouched so no client that reads them breaks; "computed" is simply true now.
#       The sigma threshold is deliberately NOT passed: compute_ndvi_diff documents a
#       default of 1.5, analysis.py passes that same number explicitly, and a third
#       copy of it here would be one more place to forget. Omitting it leaves the
#       service owning its own default.
# What Worked: run, not asserted. Component 700: 24 passed on this branch's parent,
#       28 passed after. The new tests/test_ndvi_diff_endpoint.py drives the endpoint
#       through FastAPI's TestClient over a real FLOAT32 GeoTIFF with only the network
#       stubbed, and asserts the returned anomaly's coordinates against the GeoTIFF's
#       own affine transform -- so the difference is checked for being CORRECT, not
#       merely present.
# Notes: NOT changed here, reported instead -- services/sentinel.py currently holds TWO
#       parallel implementations of the same GeoTIFF conversion, and one of them is
#       unreachable. fetch_sentinel_ndvi returns after calling
#       geotiff_bytes_to_ndvi_dataarray, and a second `return` calling
#       _tiff_to_ndvi_array sits below it as dead code, along with two constants
#       (_SENTINEL_NODATA and _CLOUD_SENTINEL, both -9999.0) and two test files. That
#       is the result of PR #54, PR #46 and PR #60 all fixing the same defect, mine
#       among them. It needs one implementation and a decision about which, which is a
#       separate change to a file three PRs just touched -- not something to fold into
#       this one.
# ════════════════════════════════════════════════════════════════════════════════════════
"""Data router — DEM, LiDAR, satellite data retrieval."""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from ..services.opentopo import fetch_dem
from ..services.sentinel import fetch_sentinel_ndvi
from ..services.temporal import compute_ndvi_diff

router = APIRouter()


@router.get("/dem")
async def get_dem(
    west: float = Query(..., description="West longitude"),
    south: float = Query(..., description="South latitude"),
    east: float = Query(..., description="East longitude"),
    north: float = Query(..., description="North latitude"),
    dataset: str = Query("SRTMGL1", description="DEM dataset (SRTMGL1, COP30, USGS1m)"),
) -> FileResponse:
    """Fetch a DEM tile for the given bounding box."""
    path = await fetch_dem(bbox=(west, south, east, north), dataset=dataset)
    return FileResponse(
        path=path,
        filename=path.name,
        media_type="application/octet-stream",
    )


@router.get("/ndvi-diff")
async def get_ndvi_diff(
    west: float = Query(...),
    south: float = Query(...),
    east: float = Query(...),
    north: float = Query(...),
    date_start: str = Query(..., description="ISO date e.g. 2023-01-01"),
    date_end: str = Query(..., description="ISO date e.g. 2024-01-01"),
) -> dict:
    """Fetch Sentinel-2 NDVI for two dates and return the difference.

    The difference is returned as the list of anomalous pixels: every pixel whose
    NDVI delta between the two dates lies further than compute_ndvi_diff's default
    sigma threshold from the mean delta, each carrying its coordinates, its sigma
    and its before/after/delta NDVI values.

    An empty "anomalies" list is a real answer, not a failure: it means the two
    scenes differ by nothing that stands out from their own variation. Absent
    credentials raise NoDataError and the handler answers 424, as elsewhere in this
    backend -- that path is unchanged.
    """
    # REVVEL-DISABLED | AGENT: claude-code | MODEL: claude-opus-5 | WR: UNASSIGNED | DATE: 2026-11-14 | STATUS: REPLACED
    # REASON: the docstring above replaces a one-line docstring. The sentence
    #         survives as its summary line, but the line itself does not, because
    #         the closing quotes moved. It is kept here so the original wording and
    #         shape stay readable: it is the sentence the endpoint did not honour.
    # PREVIOUS DOCSTRING, kept verbatim:
    #     """Fetch Sentinel-2 NDVI for two dates and return the difference."""
    # OWNER: @midnghtsapphire
    # REVVEL-DISABLED-END
    ndvi_before, ndvi_after = await fetch_sentinel_ndvi(
        bbox=(west, south, east, north),
        date_start=date_start,
        date_end=date_end,
    )
    anomalies = await compute_ndvi_diff(ndvi_before, ndvi_after)
    # REVVEL-DISABLED | AGENT: claude-code | MODEL: claude-opus-5 | WR: UNASSIGNED | DATE: 2026-11-14 | STATUS: REPLACED
    # REASON: the line below is the defect. It bound both composites and returned
    #         without differencing them, so the endpoint answered "computed" having
    #         computed nothing. The three keys it returned are kept in the new
    #         response unchanged, so this is purely additive for any client already
    #         reading them. Kept verbatim because the shape of the lie is worth
    #         being able to read next to the fix.
    # PREVIOUS IMPLEMENTATION, kept verbatim:
    #     return {"date_start": date_start, "date_end": date_end, "status": "computed"}
    # OWNER: @midnghtsapphire
    # REVVEL-DISABLED-END
    return {
        "date_start": date_start,
        "date_end": date_end,
        "status": "computed",
        "anomalies": anomalies,
    }


@router.get("/sources")
async def list_sources() -> dict:
    """List available free data sources."""
    return {
        "dem_sources": [
            {"id": "SRTMGL1", "name": "SRTM 30m", "provider": "NASA/USGS", "free": True},
            {"id": "COP30", "name": "Copernicus DEM 30m", "provider": "ESA", "free": True},
            {"id": "USGS1m", "name": "USGS 3DEP 1m", "provider": "USGS", "free": True, "usa_only": True},
        ],
        "satellite_sources": [
            {"id": "sentinel2", "name": "Sentinel-2 10m", "provider": "ESA/Copernicus", "free_tier": True},
            {"id": "landsat9", "name": "Landsat 9 30m", "provider": "USGS", "free": True},
        ],
        "lidar_sources": [
            {"id": "opentopo", "name": "OpenTopography", "provider": "NSF", "free_tier": True},
            {"id": "usgs3dep", "name": "USGS 3DEP LiDAR", "provider": "USGS", "free": True, "usa_only": True},
        ],
    }
