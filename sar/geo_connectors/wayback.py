"""Wayback Machine CDX query and content-digest diff.

The notebook's query_cdx() returned two invented rows ("SHA1_ORIGINAL_HASH_001"). This calls the CDX API."""
from . import netio as http

CDX = "https://web.archive.org/cdx/search/cdx"


def query_cdx(url, from_year=None, to_year=None, limit=500, collapse="digest", **kw):
    params = {"url": url, "output": "json", "limit": limit}
    if from_year:
        params["from"] = str(from_year)
    if to_year:
        params["to"] = str(to_year)
    if collapse:
        params["collapse"] = collapse
    rows = http.request_json(CDX, params=params, **kw)
    if not rows:
        return []
    head = rows[0]
    return [dict(zip(head, r)) for r in rows[1:]]


def digest_changes(snapshots):
    """Return snapshots where the content digest differs from the previous one (first included)."""
    out, prev = [], None
    for s in sorted(snapshots, key=lambda s: s["timestamp"]):
        if s.get("digest") != prev:
            out.append({"timestamp": s["timestamp"], "digest": s.get("digest"), "statuscode": s.get("statuscode"),
                        "replay": f"https://web.archive.org/web/{s['timestamp']}/{s.get('original')}"})
            prev = s.get("digest")
    return out
