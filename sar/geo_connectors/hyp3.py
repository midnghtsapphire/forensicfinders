#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════════════
# ASF HyP3 InSAR CONNECTOR
# Who: Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-10-24
# Why: InSAR measures ground displacement from Sentinel-1 phase, which is what detects
#      ongoing settlement of ground disturbed years ago. ASF HyP3 runs that processing in
#      NASA's cloud (free tier: 8000 credits/month, REST API + Python SDK), so this repo
#      does not need a local GMTSAR/ISCE toolchain to get interferograms.
# What: NEW FILE. Pair selection from the ASF search API, plus a thin submission wrapper
#       over hyp3_sdk.
# Notes: See docs/Q2_SUBRESOLUTION_PLAN.md for why InSAR rather than coherent change
#        detection, and for the terrain limits that decide whether it works at a site.
# ═══════════════════════════════════════════════════════════════════════════════════════
"""Sentinel-1 InSAR via ASF HyP3: find valid interferometric pairs, then submit them.

The two halves are deliberately separate.

**Pair selection** is the part with engineering content, and it runs offline against a
recorded fixture. A pair is only interferometric if both acquisitions were taken from the
same place in the sky. Granules must share:

  * path             relative orbit number
  * flightDirection  ASCENDING or DESCENDING
  * frame            which slice of the pass (see track_key for why this one matters)
  * beamMode         IW for the standard land mode
  * polarization     e.g. VV+VH

Why this is not pedantry: one six-week window over a single small bbox returns paths 85,
12 and 107, ascending and descending mixed (see fixtures/asf_slc_search.json). Pairing
across any of those compares two different viewing geometries, and the terrain then
appears to have moved when only the sensor did. That is the "wasn't illuminated before"
false positive, and this is where it is excluded.

**Submission** is a thin wrapper over hyp3_sdk, imported lazily so the rest of the module
works without it, and accepting an injected client so tests never reach the network.

Credentials: Earthdata Login, resolved from EARTHDATA_USERNAME / EARTHDATA_PASSWORD or the
urs.earthdata.nasa.gov entry in ~/.netrc. Never passed on the command line -- argv is
visible in ps and /proc to every user on the box (CLAUDE.md gotcha #4).

Troubleshooting: no pairs returned is a valid, common answer -- it usually means the date
window spans fewer than two passes on any single track. Widen the window before suspecting
a bug, and check summarise_tracks() to see which tracks actually cover the site.
"""
import argparse
import datetime as dt
import json
import netrc
import os
import sys

from . import netio as http

# ASF's search API. Public: searching needs no credentials. Only downloading and job
# submission do, which is why auth is resolved lazily at submit time rather than on import.
ASF_HOST = "api.daac.asf.alaska.edu"
ASF_SEARCH = f"https://{ASF_HOST}/services/search/param"
URS_HOST = "urs.earthdata.nasa.gov"
HYP3_BASIC = "https://hyp3-api.asf.alaska.edu"

# Sentinel-1 repeats its ground track every 6 days (two satellites) or 12 (one). Pairs
# shorter than ~5 days are not real repeats; much longer than ~48 days and C-band coherence
# over anything but bare rock is usually gone. Both are defaults, not laws -- widen them
# deliberately and expect more decorrelated pairs, not more signal.
DEFAULT_MIN_DAYS = 5
DEFAULT_MAX_DAYS = 48

# A floor that min_days cannot go under, whatever the caller passes. Two acquisitions less
# than half a day apart are the same pass, and an interferogram across zero temporal
# baseline measures nothing. Keyed on frame this should already be impossible; this is the
# belt to that braces, because the cost of silently returning a meaningless pair is that
# somebody spends credits on it and then believes the result.
MIN_SEPARATION_DAYS = 0.5


def allow_asf_hosts():
    """Add the ASF hosts to netio's allowlist. Call before search_slc()."""
    http.allow_host(ASF_HOST)


def _parse_time(value):
    """ASF returns e.g. '2024-07-14T12:53:09Z'. Returns an aware UTC datetime."""
    if not value:
        raise ValueError("granule has no startTime")
    return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def normalise(rec):
    """One ASF jsonlite record -> the fields pairing needs.

    Field names were read from a live jsonlite response recorded 2026-10-24 (see
    fixtures/asf_slc_search.json). Two of them are easy to get wrong from memory and are
    worth stating: the identifier is granuleName (sceneName is absent from jsonlite), and
    the InSAR flag is canInSAR with that capitalisation. If ASF renames a field this raises
    rather than silently pairing on None == None, which would match every granule with
    every other.
    """
    missing = [k for k in ("granuleName", "path", "flightDirection", "startTime")
               if rec.get(k) in (None, "")]
    if missing:
        raise http.ConnectorError(
            f"ASF record missing {missing}; jsonlite field names may have changed. "
            f"Keys present: {sorted(rec)[:12]}")
    return {
        "granule": rec["granuleName"],
        "path": int(rec["path"]),
        "direction": str(rec["flightDirection"]).upper(),
        "beam_mode": rec.get("beamMode"),
        "polarization": rec.get("polarization"),
        "frame": rec.get("frame"),
        "start": _parse_time(rec["startTime"]),
        "can_insar": bool(rec.get("canInSAR", True)),
    }


def search_slc(bbox, start, end, beam_mode="IW", max_results=200, **kw):
    """Sentinel-1 SLC granules intersecting bbox [w, s, e, n] between start and end.

    SLC, not GRD: GRD is detected and multi-looked, so its phase is gone and no
    interferogram can be formed from it. Raises rather than returning anything invented.
    """
    w, s, e, n = [float(v) for v in bbox]
    wkt = f"POLYGON(({w} {s},{e} {s},{e} {n},{w} {n},{w} {s}))"
    params = {"intersectsWith": wkt, "platform": "SENTINEL-1", "processingLevel": "SLC",
              "beamMode": beam_mode, "start": start, "end": end,
              "output": "jsonlite", "maxResults": int(max_results)}
    payload = http.request_json(ASF_SEARCH, params=params, **kw)
    records = payload.get("results", payload if isinstance(payload, list) else [])
    return [normalise(r) for r in records]


def track_key(g):
    """The identity a pair must share: same place in the sky, same instrument setup.

    frame is in here for a reason that is invisible until it bites. A single Sentinel-1
    pass is delivered as several consecutive SLC slices, seconds apart, distinguished only
    by frame. In the recorded fixture, path 107 carries frames 128 and 132 taken 25 seconds
    apart on the same pass. Keying without frame pairs those two with each other -- a
    "pair" with a temporal baseline of zero, covering different ground, which is not an
    interferogram at all. With frame in the key each frame pairs with itself across the
    12-day repeat, which is what was wanted.
    """
    return (g["path"], g["direction"], g["frame"], g["beam_mode"], g["polarization"])


def summarise_tracks(granules):
    """Count granules per track. The quickest way to see why a site yields no pairs."""
    out = {}
    for g in granules:
        out.setdefault(track_key(g), []).append(g)
    return {f"path{k[0]}_{k[1]}_frame{k[2]}_{k[3]}_{k[4]}": len(v)
            for k, v in sorted(out.items(), key=lambda kv: str(kv[0]))}


def interferometric_pairs(granules, min_days=DEFAULT_MIN_DAYS, max_days=DEFAULT_MAX_DAYS):
    """Consecutive same-track pairs, oldest first within each track.

    Returns [{reference, secondary, days, path, direction, ...}]. An empty list is a valid
    result and means no two acquisitions on one track fell inside the baseline window --
    not an error, and never padded out with cross-track pairs to look productive.

    Reference is the EARLIER acquisition and secondary the later, so displacement in the
    product reads as later minus earlier.
    """
    floor = max(min_days, MIN_SEPARATION_DAYS)
    usable = [g for g in granules if g["can_insar"]]
    by_track = {}
    for g in usable:
        by_track.setdefault(track_key(g), []).append(g)
    pairs = []
    for key, items in by_track.items():
        items.sort(key=lambda g: g["start"])
        for a, b in zip(items, items[1:]):
            days = (b["start"] - a["start"]).total_seconds() / 86400.0
            if floor <= days <= max_days:
                pairs.append({
                    "reference": a["granule"], "secondary": b["granule"],
                    "days": round(days, 3), "path": key[0], "direction": key[1],
                    "frame": key[2], "beam_mode": key[3], "polarization": key[4],
                    "reference_time": a["start"].isoformat(),
                    "secondary_time": b["start"].isoformat(),
                })
    pairs.sort(key=lambda p: (p["path"], p["reference_time"]))
    return pairs


def earthdata_auth(netrc_path=None):
    """(username, password) for Earthdata Login, from env or ~/.netrc. Never from argv.

    Mirrors the convention already used by blue-ocean-sar/opendata/cmr.py. argv is world
    readable through ps and /proc, so a --password flag is not offered here and must not
    be added.
    """
    user = os.environ.get("EARTHDATA_USERNAME")
    password = os.environ.get("EARTHDATA_PASSWORD")
    if user and password:
        return user, password
    path = netrc_path or os.path.expanduser("~/.netrc")
    try:
        creds = netrc.netrc(path).authenticators(URS_HOST)
    except (OSError, netrc.NetrcParseError):
        creds = None
    if creds and creds[0] and creds[2]:
        return creds[0], creds[2]
    raise http.ConnectorError(
        "HyP3 needs Earthdata Login: set EARTHDATA_USERNAME and EARTHDATA_PASSWORD, or add "
        f"a {URS_HOST} entry to ~/.netrc. Register free at https://urs.earthdata.nasa.gov/")


def connect(api_url=HYP3_BASIC, netrc_path=None):
    """A live hyp3_sdk client. Imported lazily: everything above works without the SDK."""
    try:
        import hyp3_sdk
    except ImportError as e:
        raise http.ConnectorError("hyp3_sdk not installed: pip install hyp3-sdk") from e
    user, password = earthdata_auth(netrc_path)
    return hyp3_sdk.HyP3(api_url, username=user, password=password)


def submit_insar(pairs, name, client, burst=False, limit=None):
    """Submit pairs to HyP3. `client` is injected -- pass connect() in production.

    burst=False -> submit_insar_job (full scene); burst=True -> submit_insar_isce_burst_job,
    which is cheaper in credits and the right choice for a small search area.

    Jobs are submitted, NOT waited on. HyP3 Basic runs a round-robin queue and products
    expire 14 days after completion, so the caller decides when to poll and download.
    Returns the submitted job objects paired with the geometry each came from, so a later
    download can be tied back to its track.
    """
    if limit is not None:
        pairs = pairs[:limit]
    submit = client.submit_insar_isce_burst_job if burst else client.submit_insar_job
    out = []
    for i, p in enumerate(pairs, 1):
        job = submit(p["reference"], p["secondary"], f"{name}-{i:03d}")
        out.append({"pair": p, "job": job})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Find Sentinel-1 InSAR pairs; optionally submit them to ASF HyP3.")
    ap.add_argument("--bbox", required=True, help="w,s,e,n in degrees")
    ap.add_argument("--start", required=True, help="ISO date or datetime")
    ap.add_argument("--end", required=True)
    ap.add_argument("--min-days", type=float, default=DEFAULT_MIN_DAYS)
    ap.add_argument("--max-days", type=float, default=DEFAULT_MAX_DAYS)
    ap.add_argument("--burst", action="store_true",
                    help="submit ISCE burst InSAR (cheaper, right for a small area)")
    ap.add_argument("--submit", action="store_true",
                    help="actually submit (needs Earthdata credentials)")
    ap.add_argument("--name", default="forensicfinders-insar")
    ap.add_argument("--limit", type=int, help="submit at most this many pairs")
    a = ap.parse_args(argv)

    allow_asf_hosts()
    granules = search_slc([float(v) for v in a.bbox.split(",")], a.start, a.end)
    pairs = interferometric_pairs(granules, a.min_days, a.max_days)
    report = {"granules": len(granules), "tracks": summarise_tracks(granules), "pairs": pairs}
    if a.submit:
        if not pairs:
            report["submitted"] = {"status": "no_data",
                                   "reason": "no same-track pair inside the baseline window"}
        else:
            jobs = submit_insar(pairs, a.name, connect(), burst=a.burst, limit=a.limit)
            report["submitted"] = [{"pair": j["pair"], "job_id": getattr(j["job"], "job_id", None)}
                                   for j in jobs]
    json.dump(report, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
