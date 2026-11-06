"""Registry 2371 (provisional): robust per-layer combiner, FUSION_SPEC v0.2 §2.

Clean-room. Robust z = (v - median) / (1.4826 * MAD) (Hampel 1974; Rousseeuw & Croux 1993).
Cells are addressed by integer grid index only; no geographic fields are accepted.
Output score is a relative ranking under configured weights; not a probability.
"""
from __future__ import annotations

import json
import math
import re
from fnmatch import fnmatch
from pathlib import Path
from statistics import median

MAD_K = 1.4826
SCORE_KIND = "relative ranking under configured weights; not a probability"
GEO_KEYS = {
    "lat", "lon", "lng", "long", "latitude", "longitude", "address", "addr",
    "geom", "geometry", "wkt", "coordinates", "geohash", "bbox", "crs", "epsg",
    "easting", "northing", "polygon", "point", "location", "geojson",
    "x_coord", "y_coord", "utm", "mgrs",
}
SITE_RE = re.compile(r"^cell_(\d+)_(\d+)$")


class FusionError(ValueError):
    pass


def guard_path(path) -> Path:
    """Only fixtures/*synthetic* files are valid inputs (Rule 7)."""
    p = Path(path).resolve()
    if p.parent.name != "fixtures" or not fnmatch(p.name, "*synthetic*"):
        raise FusionError(f"refusing non-synthetic input: {p}")
    if any(part in {"case", "hfmr", "evidence", "realdata"} for part in p.parts):
        raise FusionError(f"refusing quarantined path: {p}")
    return p


def parse_site_id(site_id: str) -> tuple[int, int]:
    m = SITE_RE.match(site_id)
    if not m:
        raise FusionError(f"site_id must be cell_<r>_<c>: {site_id!r}")
    return int(m.group(1)), int(m.group(2))


def _reject_geo(obj, where="config"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in GEO_KEYS:
                # Name the canonical key only. Never include the field's value.
                raise FusionError(f"geographic field {str(k).lower()} rejected")
            if k == "site_id":
                parse_site_id(v)
            _reject_geo(v, f"{where}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _reject_geo(v, f"{where}[{i}]")


def validate_config(cfg: dict) -> dict:
    _reject_geo(cfg)
    g = cfg.get("grid") or {}
    rows, cols = int(g.get("rows", 0)), int(g.get("cols", 0))
    if rows <= 0 or cols <= 0 or not float(g.get("cell_m", 0)) > 0:
        raise FusionError("grid needs positive rows, cols, cell_m (fixture-local metres)")
    if cfg.get("missing_policy") not in ("zero", "renormalise"):
        raise FusionError("missing_policy must be 'zero' or 'renormalise'")
    names = set()
    for L in cfg.get("layers", []):
        if L.get("name") in names or not L.get("name"):
            raise FusionError("layer names must be unique and non-empty")
        names.add(L["name"])
        w = float(L.get("weight", -1))
        if not (math.isfinite(w) and w > 0):
            raise FusionError(f"layer {L['name']}: weight must be > 0")
        if L.get("direction") not in ("higher", "lower"):
            raise FusionError(f"layer {L['name']}: direction must be higher|lower")
        vals = L.get("values")
        if vals is not None:
            if len(vals) != rows or any(len(r) != cols for r in vals):
                raise FusionError(f"layer {L['name']}: values shape != grid")
            for r in vals:
                for v in r:
                    if v is not None and not math.isfinite(float(v)):
                        raise FusionError(f"layer {L['name']}: non-finite value")
    if not names:
        raise FusionError("no layers")
    return cfg


def load_config(path) -> dict:
    p = guard_path(path)
    return validate_config(json.loads(p.read_text()))


def robust_z(values):
    """Return (z list with None preserved, degenerate flag). MAD == 0 -> degenerate (flagged, not zeroed)."""
    xs = [float(v) for v in values if v is not None]
    if len(xs) < 2:
        return [None] * len(values), True
    med = median(xs)
    mad = median(abs(x - med) for x in xs)
    if mad == 0.0:
        return [None] * len(values), True
    s = MAD_K * mad
    return [None if v is None else (float(v) - med) / s for v in values], False


def _rank_pct(values):
    xs = sorted(float(v) for v in values if v is not None)
    n = len(xs)
    out = []
    for v in values:
        if v is None:
            out.append(None)
            continue
        lo = sum(1 for x in xs if x < v)
        eq = sum(1 for x in xs if x == v)
        out.append((lo + 0.5 * eq) / n)
    return out


def combine(cfg: dict):
    rows, cols = cfg["grid"]["rows"], cfg["grid"]["cols"]
    n = rows * cols
    policy = cfg["missing_policy"]
    meta = {"layers": {}, "score_kind": SCORE_KIND, "missing_policy": policy, "mad_k": MAD_K}
    norm = {}
    for L in cfg["layers"]:
        flat = [v for r in L["values"] for v in r]
        z, deg = robust_z(flat)
        sign = -1.0 if L["direction"] == "lower" else 1.0
        z = [None if v is None else sign * v for v in z]
        if L.get("normalise") == "rank" and not deg:
            z = [None if v is None else sign * (v - 0.5) for v in _rank_pct(flat)]
        norm[L["name"]] = (flat, z)
        meta["layers"][L["name"]] = {"weight": float(L["weight"]), "direction": L["direction"],
                                      "degenerate": deg, "excluded": deg,
                                      "normalise": L.get("normalise", "robust_z")}
    active = [L for L in cfg["layers"] if not meta["layers"][L["name"]]["degenerate"]]
    wsum_all = math.fsum(float(L["weight"]) for L in active)
    recs = []
    for i in range(n):
        r, c = divmod(i, cols)
        present = [L for L in active if norm[L["name"]][1][i] is not None]
        denom = wsum_all if policy == "zero" else math.fsum(float(L["weight"]) for L in present)
        contribs = {}
        for L in cfg["layers"]:
            raw, z = norm[L["name"]][0][i], norm[L["name"]][1][i]
            w = float(L["weight"])
            contrib = None if (z is None or denom == 0) else w * z / denom
            contribs[L["name"]] = {"raw": None if raw is None else float(raw), "normalised": z,
                                   "weight": w, "contribution": contrib}
        score = None if denom == 0 else math.fsum(v["contribution"] for v in contribs.values() if v["contribution"] is not None)
        recs.append({"site_id": f"cell_{r}_{c}", "row": r, "col": c, "score": score,
                     "score_kind": SCORE_KIND, "contributions": contribs})
    return recs, meta


def segment_hints(cells, cell_to_segment: dict, segments) -> dict:
    """Aggregate per-segment hints (mean score, max calibrated p). Read-only: never touches POA."""
    names = {s.name for s in segments}
    acc: dict = {}
    for rec in cells:
        seg = cell_to_segment.get(rec["site_id"])
        if seg is None:
            continue
        if seg not in names:
            raise FusionError(f"unknown segment {seg!r}")
        a = acc.setdefault(seg, {"scores": [], "p": []})
        if rec.get("score") is not None:
            a["scores"].append(rec["score"])
        if "anomaly" in rec:
            a["p"].append(rec["anomaly"]["p_anomaly_calibrated"])
    return {k: {"mean_score": math.fsum(v["scores"]) / len(v["scores"]) if v["scores"] else None,
                "max_p_anomaly": max(v["p"]) if v["p"] else None, "n_cells": len(v["scores"]),
                "kind": "hint; does not change POA"} for k, v in sorted(acc.items())}
