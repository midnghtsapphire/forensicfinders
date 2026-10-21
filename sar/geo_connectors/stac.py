"""STAC search (Element84 Earth Search, NASA CMR-STAC LPCLOUD) and COG band math.

Fixes vs. the notebook's OpenGeospatialClient.search_sentinel_stac:
  * dates like "2025-06-01/2025-06-30" were sent raw; Earth Search answers 400, and the
    notebook then silently returned a hard-coded fake scene. Dates are now normalised to
    RFC 3339 and failures raise instead of inventing results.
  * pagination via the STAC "next" link; retry/backoff via http.request.
"""
import math
import re
from . import netio as http

EARTH_SEARCH = "https://earth-search.aws.element84.com/v1"
CMR_LPCLOUD = "https://cmr.earthdata.nasa.gov/stac/LPCLOUD"
_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def normalize_datetime(dt):
    parts = dt.split("/")
    if len(parts) not in (1, 2):
        raise ValueError(f"bad datetime range {dt!r}")
    out = []
    for i, p in enumerate(parts):
        if p in ("..", ""):
            out.append("..")
        elif _DAY.match(p):
            out.append(p + ("T00:00:00Z" if i == 0 else "T23:59:59Z"))
        else:
            out.append(p)
    return "/".join(out)


def validate_bbox(b):
    if len(b) != 4:
        raise ValueError("bbox must be [west, south, east, north]")
    w, s, e, n = map(float, b)
    if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
        raise ValueError(f"bad bbox {b}")
    return [w, s, e, n]


def summarize(feat):
    p = feat.get("properties", {})
    return {"id": feat.get("id"), "collection": feat.get("collection"), "datetime": p.get("datetime"),
            "cloud_cover": p.get("eo:cloud_cover"), "bbox": feat.get("bbox"),
            "assets": {k: v.get("href") for k, v in feat.get("assets", {}).items()}}


def search(bbox, datetime, collections, endpoint=EARTH_SEARCH, limit=10, max_items=50, query=None, **kw):
    body = {"bbox": validate_bbox(bbox), "datetime": normalize_datetime(datetime), "collections": list(collections), "limit": limit}
    if query:
        body["query"] = query
    url, items = f"{endpoint}/search", []
    while url and len(items) < max_items:
        page = http.request_json(url, body=body, **kw)
        items += [summarize(f) for f in page.get("features", [])]
        nxt = next((l for l in page.get("links", []) if l.get("rel") == "next"), None)
        if not nxt:
            break
        url = nxt["href"]
        body = nxt.get("body", body) if nxt.get("method", "GET").upper() == "POST" else None
        if body is None:
            break  # GET-style next links: stop rather than guess
    return items[:max_items]


# ---- band math (numpy) ----
def ndvi(red, nir):
    import numpy as np
    red, nir = np.asarray(red, dtype="float64"), np.asarray(nir, dtype="float64")
    den = nir + red
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(den == 0, np.nan, (nir - red) / den)
    return out


def delta_ndvi(red0, nir0, red1, nir1):
    """ΔNDVI = NDVI(after) − NDVI(before). Negative = vegetation loss."""
    return ndvi(red1, nir1) - ndvi(red0, nir0)


def log_ratio_db(before, after, eps=1e-6):
    """Sentinel-1 backscatter change: 10·log10(after/before) in dB (linear-power inputs)."""
    import numpy as np
    b, a = np.asarray(before, dtype="float64"), np.asarray(after, dtype="float64")
    return 10.0 * np.log10((a + eps) / (b + eps))


def anomalies(delta, sigma=2.0):
    """Cells where |delta - mean| > sigma*std. Returns (rows, cols, threshold)."""
    import numpy as np
    d = np.asarray(delta, dtype="float64")
    m, s = np.nanmean(d), np.nanstd(d)
    thr = sigma * s
    r, c = np.where(np.abs(d - m) > thr)
    return r.tolist(), c.tolist(), float(thr)


def read_cog_window(href, bbox, out_shape=None):
    """Read a COG band over a lon/lat bbox (rasterio optional dependency). Works with https:// hrefs via GDAL vsicurl."""
    try:
        import rasterio
        from rasterio.warp import transform_bounds
        from rasterio.windows import from_bounds
    except ImportError as e:
        raise http.ConnectorError("rasterio not installed: pip install rasterio") from e
    with rasterio.open(href) as ds:
        b = transform_bounds("EPSG:4326", ds.crs, *validate_bbox(bbox))
        win = from_bounds(*b, transform=ds.transform)
        return ds.read(1, window=win, out_shape=out_shape, boundless=True, fill_value=0).astype("float64")
