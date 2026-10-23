#!/usr/bin/env python3
"""Minimal MCP server (stdio, JSON-RPC 2.0, newline-delimited) exposing the geo connectors.

Run: python3 -m geo_connectors.mcp_server   (from sar/)
Tools: search_stac_satellite, query_usgs_lidar, sample_usgs_elevation, wayback_cdx_diff, arcgis_query.
No LLM is involved. The notebook's calculate_taphonomic_kinetics tool is not exposed: its constants
were never sourced (see the PR's left-out table)."""
import json
import sys
from . import arcgis, dep3, stac, wayback
from . import netio as http

PROTOCOL = "2024-11-05"
BBOX = {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4, "description": "[west, south, east, north] WGS84"}
TOOLS = {
    "search_stac_satellite": ({"type": "object", "required": ["bbox", "datetime"], "properties": {
        "bbox": BBOX, "datetime": {"type": "string", "description": "YYYY-MM-DD/YYYY-MM-DD or RFC3339 range"},
        "collections": {"type": "array", "items": {"type": "string"}, "default": ["sentinel-2-l2a"]},
        "endpoint": {"type": "string", "enum": ["earth-search", "cmr-lpcloud"], "default": "earth-search"},
        "max_items": {"type": "integer", "default": 10, "maximum": 100}}},
        "Search Sentinel-1/2 (Earth Search) or HLS (NASA CMR LPCLOUD) STAC items."),
    "query_usgs_lidar": ({"type": "object", "required": ["bbox"], "properties": {"bbox": BBOX,
        "size": {"type": "array", "items": {"type": "integer"}, "default": [256, 256]}}},
        "USGS 3DEP bare-earth DTM exportImage: returns the GeoTIFF href and extent."),
    "sample_usgs_elevation": ({"type": "object", "required": ["points"], "properties": {
        "points": {"type": "array", "items": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2}, "maxItems": 500}}},
        "USGS 3DEP point elevations (metres) for [[lon, lat], ...]."),
    "wayback_cdx_diff": ({"type": "object", "required": ["url"], "properties": {"url": {"type": "string"},
        "from_year": {"type": "integer"}, "to_year": {"type": "integer"}}},
        "Wayback Machine snapshots where the page content digest changed."),
    "arcgis_query": ({"type": "object", "required": ["layer_url"], "properties": {"layer_url": {"type": "string"},
        "where": {"type": "string", "default": "1=1"}, "bbox": BBOX, "max_features": {"type": "integer", "default": 1000}}},
        "Query an allowlisted ArcGIS REST layer (paged) as GeoJSON."),
}


def call(name, a, **kw):
    if name == "search_stac_satellite":
        ep = stac.CMR_LPCLOUD if a.get("endpoint") == "cmr-lpcloud" else stac.EARTH_SEARCH
        return stac.search(a["bbox"], a["datetime"], a.get("collections") or ["sentinel-2-l2a"], endpoint=ep,
                           max_items=min(int(a.get("max_items", 10)), 100), **kw)
    if name == "query_usgs_lidar":
        return dep3.export_dtm(a["bbox"], size=tuple(a.get("size", (256, 256))), **kw)
    if name == "sample_usgs_elevation":
        return dep3.sample_elevations(a["points"][:500], **kw)
    if name == "wayback_cdx_diff":
        return wayback.digest_changes(wayback.query_cdx(a["url"], a.get("from_year"), a.get("to_year"), **kw))
    if name == "arcgis_query":
        return arcgis.query_layer(a["layer_url"], where=a.get("where", "1=1"), bbox=a.get("bbox"),
                                  max_features=int(a.get("max_features", 1000)), **kw)
    raise KeyError(name)


def handle(msg, **kw):
    mid, method = msg.get("id"), msg.get("method")
    if mid is None:
        return None  # notification
    if method == "initialize":
        res = {"protocolVersion": PROTOCOL, "capabilities": {"tools": {}}, "serverInfo": {"name": "forensicfinders-geo", "version": "1.0.0"}}
    elif method == "ping":
        res = {}
    elif method == "tools/list":
        res = {"tools": [{"name": n, "description": d, "inputSchema": s} for n, (s, d) in TOOLS.items()]}
    elif method == "tools/call":
        p = msg.get("params", {})
        if p.get("name") not in TOOLS:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"unknown tool {p.get('name')}"}}
        try:
            out = call(p["name"], p.get("arguments") or {}, **kw)
            res = {"content": [{"type": "text", "text": json.dumps(out)}], "isError": False}
        except (http.ConnectorError, ValueError, KeyError, TypeError) as e:
            res = {"content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}], "isError": True}
    else:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": mid, "result": res}


def main(stdin=sys.stdin, stdout=sys.stdout):
    for line in stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            out = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            out = handle(msg)
        if out is not None:
            stdout.write(json.dumps(out) + "\n")
            stdout.flush()


if __name__ == "__main__":
    main()
