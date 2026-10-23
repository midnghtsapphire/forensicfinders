#!/usr/bin/env python3
"""Terrain anomaly detector, replacing the notebook's run_county.py.

  validate CONFIG   schema check only, no data pulled
  run CONFIG        real DEMs (file paths, or a bbox fetched from USGS 3DEP via registry 920) ->
                    plane-detrended residual (or epoch difference) -> Getis-Ord Gi* -> cells with |z| >= z_min
  demo              synthetic DEM (local metres, no coordinates) with one known depression
  curve LABELS.csv  ROC and AUC from YOUR labelled data (columns: score,label with label 0/1). No built-in AUC.

Output is candidate cells with their Gi* z and coordinates computed from the DEM geotransform. Nothing is typed in.
The notebook's p_grave score (an unsourced weighted sum) and its hard-coded ROC curve and AUC are gone."""
import argparse, csv, json, os, sys
import numpy as np
from .gistar import gi_star

REQUIRED = ("name", "tiles")


def validate(cfg):
    errs = [f"missing key {k}" for k in REQUIRED if k not in cfg]
    if "tiles" in cfg and not cfg["tiles"]:
        errs.append("tiles must contain at least one tile")
    for i, t in enumerate(cfg.get("tiles", [])):
        if not (t.get("dem_path") or t.get("bbox")):
            errs.append(f"tile {i}: needs dem_path or bbox")
        if t.get("bbox") and len(t["bbox"]) != 4:
            errs.append(f"tile {i}: bbox must be [w,s,e,n]")
    return errs


def detrend_plane(z):
    R, C = z.shape
    yy, xx = np.mgrid[0:R, 0:C]
    m = np.isfinite(z)
    A = np.c_[xx[m], yy[m], np.ones(m.sum())]
    coef, *_ = np.linalg.lstsq(A, z[m], rcond=None)
    return z - (coef[0] * xx + coef[1] * yy + coef[2])


def read_dem(path):
    try:
        import rasterio
    except ImportError as e:
        raise RuntimeError("rasterio needed to read DEM files: pip install rasterio") from e
    with rasterio.open(path) as ds:
        z = ds.read(1, masked=True).astype("float64").filled(np.nan)
        return z, ds.transform, str(ds.crs)


def detect(z, z_min=1.96, transform=None, crs=None, sign="both"):
    z = np.where(np.isfinite(z), z, np.nanmean(z))
    g = gi_star(z)
    sel = np.abs(g) >= z_min if sign == "both" else (g <= -z_min if sign == "low" else g >= z_min)
    out = []
    for r, c in zip(*np.where(sel)):
        cell = {"row": int(r), "col": int(c), "gi_star_z": round(float(g[r, c]), 3), "value": round(float(z[r, c]), 4)}
        if transform is not None:
            x, y = transform * (c + 0.5, r + 0.5)
            cell.update({"x": float(x), "y": float(y), "crs": crs})
        out.append(cell)
    return sorted(out, key=lambda d: -abs(d["gi_star_z"]))


def run_tile(t, out_dir, z_min, fetch=None):
    if t.get("dem_path"):
        z, tr, crs = read_dem(t["dem_path"])
    else:
        from geo_connectors import dep3
        p = os.path.join(out_dir, f"{t.get('id', 'tile')}_dtm.tif")
        (fetch or dep3.export_dtm)(t["bbox"], size=tuple(t.get("size", (256, 256))), out_path=p)
        z, tr, crs = read_dem(p)
    if t.get("baseline_dem_path"):
        z0, _, _ = read_dem(t["baseline_dem_path"])
        resid, basis = z - z0, "epoch_difference"
    else:
        resid, basis = detrend_plane(z), "plane_detrended_residual"
    return {"tile": t.get("id"), "basis": basis, "z_min": z_min, "cells": detect(resid, z_min, tr, crs, t.get("sign", "both"))}


def roc(scores, labels):
    s, y = np.asarray(scores, float), np.asarray(labels, int)
    if set(np.unique(y)) - {0, 1} or y.min() == y.max():
        raise ValueError("labels must contain both 0 and 1")
    order = np.argsort(-s, kind="mergesort")
    s, y = s[order], y[order]
    P, N = y.sum(), (1 - y).sum()
    tpr, fpr, tp, fp = [0.0], [0.0], 0, 0
    for i in range(len(s)):
        tp += y[i]; fp += 1 - y[i]
        if i == len(s) - 1 or s[i] != s[i + 1]:
            tpr.append(tp / P); fpr.append(fp / N)
    auc = float(sum((fpr[i] - fpr[i - 1]) * (tpr[i] + tpr[i - 1]) / 2 for i in range(1, len(fpr))))
    return fpr, tpr, auc


def synthetic_dem(n=40, seed=0, depth=0.3, centre=(20, 20), radius=3):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:n, 0:n]
    z = 100 + 0.05 * xx + 0.02 * yy + rng.normal(0, 0.01, (n, n))
    d = np.hypot(yy - centre[0], xx - centre[1])
    return z - np.where(d < radius, depth * (1 - d / radius), 0)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "run"):
        p = sp.add_parser(name); p.add_argument("config")
        if name == "run":
            p.add_argument("--out-dir", default="out"); p.add_argument("--z-min", type=float, default=1.96)
    sp.add_parser("demo")
    p = sp.add_parser("curve"); p.add_argument("labels_csv"); p.add_argument("--png")
    a = ap.parse_args(argv)
    if a.cmd in ("validate", "run"):
        cfg = json.load(open(a.config))
        errs = validate(cfg)
        if errs:
            print("\n".join(errs), file=sys.stderr); return 1
        if a.cmd == "validate":
            print(f"OK: {cfg['name']} ({len(cfg['tiles'])} tiles)"); return 0
        os.makedirs(a.out_dir, exist_ok=True)
        res = {"name": cfg["name"], "tiles": [run_tile(t, a.out_dir, a.z_min) for t in cfg["tiles"]]}
        p = os.path.join(a.out_dir, f"{cfg['name']}_anomalies.json"); json.dump(res, open(p, "w"), indent=2); print(p); return 0
    if a.cmd == "demo":
        cells = detect(detrend_plane(synthetic_dem()), sign="low")
        print(json.dumps({"synthetic": True, "known_depression": [20, 20], "top": cells[:5]}, indent=2)); return 0
    rows = list(csv.DictReader(open(a.labels_csv)))
    fpr, tpr, auc = roc([float(r["score"]) for r in rows], [int(r["label"]) for r in rows])
    print(json.dumps({"n": len(rows), "auc": round(auc, 4), "fpr": fpr, "tpr": tpr}))
    if a.png:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        plt.plot(fpr, tpr, marker="o", label=f"your labels (AUC={auc:.3f}, n={len(rows)})"); plt.plot([0, 1], [0, 1], "--")
        plt.xlabel("FPR"); plt.ylabel("TPR"); plt.legend(); plt.savefig(a.png, dpi=120); print(a.png)
    return 0


if __name__ == "__main__":
    sys.exit(main())
