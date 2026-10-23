"""ArcGIS REST FeatureServer/MapServer layer query with paging.

The notebook's query_arcgis_layer() returned a hard-coded "simulated_features" permit. This queries
the layer and pages with resultOffset while exceededTransferLimit is true. Add municipal hosts with
http.allow_host("gis.example-city.gov")."""
from . import netio as http


def query_layer(layer_url, where="1=1", out_fields="*", bbox=None, page_size=1000, max_features=10000, **kw):
    feats, offset = [], 0
    while len(feats) < max_features:
        params = {"where": where, "outFields": out_fields, "f": "geojson", "outSR": 4326,
                  "resultOffset": offset, "resultRecordCount": min(page_size, max_features - len(feats))}
        if bbox:
            w, s, e, n = bbox
            params.update({"geometry": f"{w},{s},{e},{n}", "geometryType": "esriGeometryEnvelope",
                           "inSR": 4326, "spatialRel": "esriSpatialRelIntersects"})
        page = http.request_json(layer_url.rstrip("/") + "/query", params=params, **kw)
        if "error" in page:
            raise http.ConnectorError(f"ArcGIS error: {page['error']}")
        got = page.get("features", [])
        feats += got
        more = page.get("exceededTransferLimit") or page.get("properties", {}).get("exceededTransferLimit")
        if not got or not more:
            break
        offset += len(got)
    return {"type": "FeatureCollection", "features": feats[:max_features]}
