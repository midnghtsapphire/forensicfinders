"""
Data-driven lost-person-behavior (LPB) distance lookup.

Ported from universal-sar-app server/algorithms/sar-engine.ts getMovementProfile().
The original hard-coded a switch of distance percentiles labelled "Koester data"
with no citation. Here the numbers live in a JSON table you supply, and every
table must name its source. Tables marked "verified": false are refused unless
you pass allow_unverified=True, so un-sourced numbers can't reach an operator
silently.

Table format:
{"source": {"citation": "...", "verified": true},
 "profiles": [{"key": "human/hiker", "when": {"experience_level": "expert"},
               "speed_kmh": 4.0, "p25_km": 2.0, "p50_km": 5.0, "p75_km": 10.0, "p95_km": 20.0}, ...],
 "default": {...same fields...}}
The first profile whose key matches and whose "when" conditions all hold wins.
"when" supports equality and {"max": n} / {"min": n} numeric bounds.
"""
import json
import math
import os

FIELDS = ("speed_kmh", "p25_km", "p50_km", "p75_km", "p95_km")


class UnverifiedTable(ValueError):
    pass


def load_table(path_or_obj, allow_unverified=False):
    t = json.load(open(path_or_obj)) if isinstance(path_or_obj, str) else path_or_obj
    src = t.get("source") or {}
    if not str(src.get("citation", "")).strip():
        raise UnverifiedTable("table has no source.citation")
    if not src.get("verified") and not allow_unverified:
        raise UnverifiedTable(f"table source not verified: {src.get('citation')}")
    for p in t.get("profiles", []) + ([t["default"]] if "default" in t else []):
        vals = [p.get(f) if f != "speed_kmh" else (p.get(f) or 0) for f in FIELDS]
        if any(v < 0 for v in vals) or vals[1:] != sorted(vals[1:]):
            raise ValueError(f"bad profile {p.get('key', 'default')}: percentiles must be >=0 and non-decreasing")
    return t


def _holds(cond, attrs):
    for k, v in cond.items():
        a = attrs.get(k)
        if isinstance(v, dict):
            if a is None:
                return False
            if "max" in v and not a <= v["max"]:
                return False
            if "min" in v and not a >= v["min"]:
                return False
        elif a != v:
            return False
    return True


def profile(table, subject_type, subtype=None, attrs=None):
    key = f"{subject_type}/{subtype or 'default'}"
    attrs = attrs or {}
    for p in table.get("profiles", []):
        if p["key"] == key and _holds(p.get("when", {}), attrs):
            return {f: p.get(f) for f in FIELDS} | {"matched": key, "citation": table["source"]["citation"]}
    if "default" in table:
        return {f: table["default"][f] for f in FIELDS} | {"matched": "default", "citation": table["source"]["citation"]}
    return None  # no data: caller must not invent a radius


def rings(prof):
    """Distance rings (km) for p25/p50/p75/p95, or [] when there is no profile."""
    if not prof:
        return []
    return [{"percentile": int(f[1:3]), "radius_km": prof[f]} for f in FIELDS[1:]]


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    dl, dp = math.radians(lon2 - lon1), math.radians(lat2 - lat1)
    a = math.sin(dp / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


ISRID_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "isrid_distances.json")


def load_isrid(path=ISRID_PATH):
    """Load sar/data/isrid_distances.json (Koester 2008, printed ISRID tables) as an lpb table.

    Profiles are keyed "human/<category>" with when={"ecoregion", "terrain"}; urban rows use
    terrain "any". Each profile keeps n, page and url. speed_kmh is None (not in the tables).
    There is no default: an unlisted category returns None, so no radius is invented."""
    d = json.load(open(path))
    profiles = []
    for r in d["distances"]:
        when = {"ecoregion": r["ecoregion"]}
        if r["terrain"] != "any":
            when["terrain"] = r["terrain"]
        profiles.append({"key": f"human/{r['category']}", "when": when, "speed_kmh": None,
                         **{f: r[f] for f in FIELDS[1:]}, "n": r["n"], "page": r["page"], "url": r["url"]})
    return load_table({"source": d["source"], "profiles": profiles})
