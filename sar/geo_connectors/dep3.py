"""USGS 3DEP bare-earth DTM via the 3DEPElevation ImageServer.

The notebook's query_usgs_3dep_lidar() made no request at all: it returned a dict that said
"status": "Active" and "smrf_filter": "Applied" and handed back an unfetched URL. This module
actually calls exportImage (and getSamples for point elevations)."""
import json
from . import netio as http

IMAGESERVER = "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer"


def export_dtm(bbox, size=(256, 256), out_path=None, **kw):
    """exportImage -> GeoTIFF (float32 metres). Returns {"href","width","height","extent", "path"?}."""
    w, s, e, n = bbox
    meta = http.request_json(f"{IMAGESERVER}/exportImage", params={
        "bbox": f"{w},{s},{e},{n}", "bboxSR": 4326, "size": f"{size[0]},{size[1]}",
        "format": "tiff", "pixelType": "F32", "interpolation": "RSP_BilinearInterpolation", "f": "json"}, **kw)
    if "error" in meta or "href" not in meta:
        raise http.ConnectorError(f"3DEP exportImage error: {json.dumps(meta)[:300]}")
    out = {k: meta.get(k) for k in ("href", "width", "height", "extent")}
    if out_path:
        open(out_path, "wb").write(http.request(meta["href"], **kw))
        out["path"] = out_path
    return out


def sample_elevations(points, **kw):
    """getSamples for [(lon, lat), ...] -> [{"lon","lat","elevation_m"}]. NoData comes back as None."""
    geom = {"points": [[float(x), float(y)] for x, y in points], "spatialReference": {"wkid": 4326}}
    r = http.request_json(f"{IMAGESERVER}/getSamples", params={
        "geometry": json.dumps(geom), "geometryType": "esriGeometryMultipoint", "returnFirstValueOnly": "true", "f": "json"}, **kw)
    if "error" in r:
        raise http.ConnectorError(f"3DEP getSamples error: {r['error']}")
    out = []
    for smp in sorted(r.get("samples", []), key=lambda s: s.get("locationId", 0)):
        v = smp.get("value")
        try:
            val = float(v)
        except (TypeError, ValueError):
            val = None
        if val is not None and val < -1e30:
            val = None
        loc = smp.get("location", {})
        out.append({"lon": loc.get("x"), "lat": loc.get("y"), "elevation_m": val})
    return out


def dtm_difference(a, b):
    """Elevation change b - a for two co-registered DTM arrays (metres)."""
    import numpy as np
    a, b = np.asarray(a, dtype="float64"), np.asarray(b, dtype="float64")
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch {a.shape} vs {b.shape}")
    return b - a
