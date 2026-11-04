# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  Every callable in this file raised NotImplementedError, so the module could not be
#       used as committed -- it was four lines of intent and one raise. VISITING_AGENTS.md
#       section 1 forbids shipping that: "Ship working code, not plans. No TODO stubs, no
#       'this would do X' placeholders, no scaffolding language." Three of the seven original
#       lines are also flagged by pattern by .github/workflows/anti-scaffolding-enforcer.yml.
# What: Implemented the loader for real, and deliberately NOT by opening rasterio here.
#       VISITING_AGENTS.md section 2: "Do not re-scaffold existing tooling ... Extend them;
#       don't clone them under a new name." sar/geo_connectors/stac.py:read_cog_window is
#       already this repository's rasterio read path: tested, and routed through the decode
#       seam (sar/decode_hooks.py) so a registered correction cannot be skipped. This file
#       delegates to it, which is why it adds no new name to decode_hooks.KNOWN_DECODERS --
#       a second ingress would be a decode point no scoped hook could target, and the whole
#       point of the seam is that there is one place where bytes become an array.
# What Worked: writing a 4x5 EPSG:4326 GeoTIFF with rasterio and reading it back through
#       load_geotiff returns the exact values written, and meta comes back carrying the
#       decode receipt. Measured on Python 3.14.3 with rasterio installed; see
#       test_loader_and_fetcher.py, which is the regression test for this change.
# Notes: Two real limits, documented rather than hidden. (1) A GeoTIFF with no CRS cannot
#       go through this path at all, because read_cog_window addresses a window in lon/lat
#       and there is nothing to transform from; load_geotiff raises rather than guessing a
#       CRS, and test_raster_without_crs_is_refused_by_name holds it to that. (2) When bbox
#       is omitted the raster's own bounds are transformed to EPSG:4326 and windowed back,
#       so the returned grid is not guaranteed identical to the native grid. Measured: a
#       4x5 EPSG:4326 raster and a 4x5 EPSG:3857 raster both came back exact, shape and
#       values. That is a measurement on two small rasters, not a proof for every CRS and
#       size, so pass bbox explicitly when the exact native window matters.
# ══════════════════════════════════════════════════════════════════════════════════════════
# REVVEL-DISABLED | AGENT: claude-code | MODEL: claude-opus-5 | WR: UNASSIGNED | DATE: 2026-11-04 | STATUS: REPLACED
# REASON: the entire original file. It raised NotImplementedError on its only call path, so
#         importing it succeeded and using it could not. Replaced by the working
#         implementation below; the original name load_geotiff_stub is kept as a live alias
#         further down, so nothing that imported it can break.
# PREVIOUS FILE, kept verbatim:
# """Minimal real-data loader stub. Replace with full rasterio/laspy paths."""
# import numpy as np
#
# def load_geotiff_stub(path: str) -> tuple[np.ndarray, dict]:
#     """Placeholder. Wire to rasterio.open when ready."""
#     # TODO: real rasterio path
#     raise NotImplementedError(f"wire rasterio for {path}")
# OWNER: @midnghtsapphire
# REVVEL-DISABLED-END
"""Real-data loader for the private multi-proxy pipeline.

Reads a GeoTIFF into a float64 array plus a metadata receipt, by delegating to
sar/geo_connectors/stac.py:read_cog_window -- the repository's single raster ingress.
Local paths and https:// hrefs both work, because rasterio reaches remote COGs through
GDAL's vsicurl, so a scene found by data_fetcher.fetch_sentinel2 can be read here without
being downloaded first.

laspy point-cloud loading is NOT in this file and is not missing from it: point clouds
already have their ingress at sar/instrument_input/instrument_input.py:read_points, which
is likewise routed through the decode seam. Call that directly.
"""
import os as _os
import sys as _sys

import numpy as np

# geo_connectors is a package but its parent sar/ is not, so sar/ goes on sys.path and the
# package is imported by plain name. sar/geo_connectors/stac.py and
# sar/instrument_input/instrument_input.py both do exactly this for decode_hooks; the
# comment there explains why importing one file under two names would split the registry.
_SAR_ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
if _SAR_ROOT not in _sys.path:
    _sys.path.insert(0, _SAR_ROOT)


def _stac():
    """Import geo_connectors.stac on first use, not at module import.

    Deliberate: the other modules in this package (dielectric, twi, nnls_unmix, consensus,
    sam) are pure numpy and must stay importable on a bare runner. Importing stac here at
    module level would make `import multi_proxy.loader` depend on the sar/ directory layout
    even for a caller that only wanted the engines.
    """
    from geo_connectors import stac
    return stac


def bounds_4326(path):
    """The raster's own extent as [west, south, east, north] in EPSG:4326.

    Raises ValueError for a raster with no CRS: there is no defensible lon/lat extent for
    an ungeoreferenced grid, and inventing one (assuming 4326, assuming a UTM zone) would
    put a window somewhere arbitrary on the planet and return pixels with confidence.
    """
    import rasterio
    from rasterio.warp import transform_bounds
    with rasterio.open(path) as ds:
        if ds.crs is None:
            raise ValueError(
                f"{path} has no CRS, so its extent cannot be expressed in lon/lat. "
                f"read_cog_window addresses windows in EPSG:4326; pass an explicit bbox "
                f"only if the file really is lon/lat and simply lacks the tag.")
        return list(transform_bounds(ds.crs, "EPSG:4326", *ds.bounds))


def load_geotiff(path, bbox=None, out_shape=None, meta=None):
    """Read band 1 of a GeoTIFF as float64, with a metadata receipt.

    path      local path or https:// href.
    bbox      [west, south, east, north] in EPSG:4326. Omitted, the raster's own extent is
              used -- see the edge-pixel note in this file's header.
    out_shape (rows, cols) to resample to, passed straight through to rasterio.
    meta      optional dict to receive the receipt. One is created if not supplied.

    Returns (band, meta). meta carries what read_cog_window records -- decoder, href,
    bbox, crs, out_shape -- and, once any hook is registered, decode_hooks_applied naming
    the corrections that actually ran, in order. Band 1 and float64 are not a choice made
    here; they are read_cog_window's existing contract, and matching it is the point.
    """
    if meta is None:
        meta = {}
    if bbox is None:
        bbox = bounds_4326(path)
    band = _stac().read_cog_window(path, bbox, out_shape=out_shape, meta=meta)
    return np.asarray(band), meta


def load_geotiff_stub(path: str) -> tuple[np.ndarray, dict]:
    """Deprecated name for load_geotiff. Works; call load_geotiff in new code.

    Kept only because nothing in this repository is deleted -- it is the repository's
    historical record. The name is now wrong in two ways: it is no longer a stub, and it
    takes no bbox. It forwards, so any caller that existed keeps working and gets real
    pixels instead of an exception. There were no such callers when this was written.
    """
    return load_geotiff(path)
