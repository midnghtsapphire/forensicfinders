"""Fetch free DEM and spectral stacks for the private multi-proxy pipeline.
One step: get real data into the engines.
"""
# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  fetch_sentinel2 returned None on every call. It printed signup instructions and a
#       bbox, then returned None unconditionally, so a caller could not tell "no scenes
#       match" from "this function was never written". VISITING_AGENTS.md section 1 forbids
#       shipping that, and the Anti-Scaffolding Enforcer flags its docstring by pattern.
# What: Implemented it against the STAC search this repository already owns. Only
#       fetch_sentinel2 changed; fetch_dem_3dep and simple_coherence_diff are untouched,
#       byte for byte, and the original fetch_sentinel2 is preserved in full below.
#       The Copernicus Data Space account the original asked for is not needed: Element84
#       Earth Search serves sentinel-2-l2a openly, and sar/geo_connectors/stac.py already
#       talks to it with retry, pagination and date normalisation, and already raises
#       instead of inventing a scene when the endpoint answers 400. Per VISITING_AGENTS.md
#       section 2 -- "Do not re-scaffold existing tooling ... Extend them; don't clone them
#       under a new name" -- this delegates there rather than adding a second HTTP client
#       and a credential path.
# What Worked: nothing is downloaded, and that is the design, not a shortfall. Earth Search
#       returns asset hrefs that loader.load_geotiff reads a window from directly through
#       GDAL vsicurl, so pulling whole products to disk would cost gigabytes to produce
#       bytes the pipeline never reads. fetch_sentinel2 therefore writes the scene manifest
#       -- ids, datetimes, cloud cover, every asset href -- and returns its path, which is
#       the same contract fetch_dem_3dep has: a path on disk, or None.
# Notes: Choosing WHICH bands to pull for ash and mineral proxies is a judgement about the
#       products and the cases, so this does not make it. The manifest hands every href to
#       the caller and lets that decision stay where it belongs.
# ══════════════════════════════════════════════════════════════════════════════════════════
import json
import os
import sys
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

# sar/ is the directory every registry component runs from, not an importable package, so it
# goes on sys.path and geo_connectors is imported by plain name. Same device, same reason, as
# sar/geo_connectors/stac.py and sar/instrument_input/instrument_input.py use for decode_hooks.
_SAR_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _SAR_ROOT not in sys.path:
    sys.path.insert(0, _SAR_ROOT)


def _stac():
    """Import geo_connectors.stac on first use, not at module import.

    Keeps `import multi_proxy.data_fetcher` free of the sar/ layout dependency for a caller
    that only wants simple_coherence_diff, which is pure numpy.
    """
    from geo_connectors import stac
    return stac


def fetch_dem_3dep(bbox: Tuple[float, float, float, float], out_dir: str = "data/dem") -> Optional[str]:
    """Download a 3DEP DEM for the bounding box (west, south, east, north).
    Uses seamless-3dep if available, otherwise prints the National Map URL.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    try:
        import seamless_3dep as s3dep
        files = s3dep.get_dem(bbox, out_dir, resolution="10m")
        return files[0] if files else None
    except ImportError:
        print("Install: pip install seamless-3dep")
        print("Or download manually: https://apps.nationalmap.gov/downloader/")
        print(f"BBox: {bbox}")
        return None


def find_sentinel2(bbox: Tuple[float, float, float, float], date_range: Tuple[str, str],
                   limit: int = 10, max_items: int = 50, endpoint: Optional[str] = None, **kw):
    """Sentinel-2 L2A scenes intersecting bbox within date_range.

    Returns a list of stac.summarize() dicts: id, collection, datetime, cloud_cover, bbox,
    and assets as {band_name: href}. No account and no credentials -- Element84 Earth Search
    is open. Raises rather than returning an empty list when the endpoint rejects the query,
    because a silent [] reads identically to "nothing matched" and that ambiguity is what
    sent the previous version of this module back to printing instructions.

    No cloud-cover threshold is applied here on purpose. Every scene carries its own
    cloud_cover, so the caller filters on a number it chose; a default buried in a fetcher
    would quietly drop scenes a case might need.
    """
    stac = _stac()
    return stac.search(
        bbox,
        f"{date_range[0]}/{date_range[1]}",
        ["sentinel-2-l2a"],
        endpoint=endpoint or stac.EARTH_SEARCH,
        limit=limit,
        max_items=max_items,
        **kw)


def _manifest_name(bbox, date_range) -> str:
    w, s, e, n = (float(v) for v in bbox)
    start = str(date_range[0]).replace("/", "").replace(":", "")
    end = str(date_range[1]).replace("/", "").replace(":", "")
    return f"sentinel2_{w:.4f}_{s:.4f}_{e:.4f}_{n:.4f}_{start}_{end}.json"


# REVVEL-DISABLED | AGENT: claude-code | MODEL: claude-opus-5 | WR: UNASSIGNED | DATE: 2026-11-04 | STATUS: REPLACED
# REASON: returned None on every call, printing signup instructions instead of searching.
#         Replaced by the implementation below, which searches Earth Search through
#         sar/geo_connectors/stac.py and writes a scene manifest. The signature is unchanged
#         except for two new keyword arguments that both default, so any existing call keeps
#         working -- and now gets a path or a reasoned None instead of an unconditional None.
# PREVIOUS FUNCTION, kept verbatim:
# def fetch_sentinel2(bbox: Tuple[float, float, float, float], date_range: Tuple[str, str], out_dir: str = "data/s2") -> Optional[str]:
#     """Placeholder for Sentinel-2 L2A download via cdse-client or CDSETool.
#     Returns path to a downloaded product or None.
#     """
#     Path(out_dir).mkdir(parents=True, exist_ok=True)
#     print("For real Sentinel-2:")
#     print("  pip install cdse-client")
#     print("  Register free account at https://dataspace.copernicus.eu/")
#     print(f"  BBox {bbox}, dates {date_range}")
#     # Stub returns None until credentials are set
#     return None
# OWNER: @midnghtsapphire
# REVVEL-DISABLED-END
def fetch_sentinel2(bbox: Tuple[float, float, float, float], date_range: Tuple[str, str],
                    out_dir: str = "data/s2", limit: int = 10, max_items: int = 50) -> Optional[str]:
    """Find Sentinel-2 L2A scenes and write their manifest to out_dir.

    Returns the manifest path, or None when no scene intersects bbox in date_range -- and
    None now means exactly that, nothing else.

    The manifest holds every asset href for every matching scene. Pixels stay where they
    are: loader.load_geotiff reads a window from an href directly, so the manifest is the
    whole handoff. Read it back with json.load; its "scenes" key is what find_sentinel2
    returned.
    """
    scenes = find_sentinel2(bbox, date_range, limit=limit, max_items=max_items)
    if not scenes:
        return None
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    path = Path(out_dir) / _manifest_name(bbox, date_range)
    payload = {
        "collection": "sentinel-2-l2a",
        "endpoint": _stac().EARTH_SEARCH,
        "bbox": [float(v) for v in bbox],
        "date_range": [str(date_range[0]), str(date_range[1])],
        "scene_count": len(scenes),
        "scenes": scenes,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    return str(path)


def simple_coherence_diff(pre: np.ndarray, post: np.ndarray) -> np.ndarray:
    """Simple coherence difference map for disturbance detection.
    pre/post are coherence rasters [0,1]. Low values after an event flag potential change.
    """
    diff = pre - post
    return np.clip(diff, 0, 1)
