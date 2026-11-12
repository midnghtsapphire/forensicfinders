"""Run fusion for one seed: combine + anomaly, deterministic byte output (no timestamps)."""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ["GDAL_PAM_ENABLED"] = "NO"  # no .aux.xml side-car

import hashlib
import json
import math
from pathlib import Path

import numpy as np

from . import anomaly as A
from . import combine as C

SPEC = "FUSION_SPEC v0.2 (PR #18 @ 6fb9960); registry 2371 provisional"


def _fmt(o):
    if isinstance(o, float):
        if not math.isfinite(o):
            raise C.FusionError("non-finite float in output")
        return "%.17g" % o
    if isinstance(o, bool) or o is None:
        return json.dumps(o)
    if isinstance(o, (int, str)):
        return json.dumps(o)
    if isinstance(o, dict):
        return "{" + ",".join(json.dumps(str(k)) + ":" + _fmt(o[k]) for k in sorted(o)) + "}"
    if isinstance(o, (list, tuple)):
        return "[" + ",".join(_fmt(v) for v in o) + "]"
    raise TypeError(type(o))


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _write_tif(path: Path, cells, rows, cols):
    import rasterio
    p = np.zeros((rows, cols), "float64")
    w = np.zeros((rows, cols), "float64")
    for r in cells:
        a = r["anomaly"]
        p[r["row"], r["col"]] = a["p_anomaly_calibrated"]
        w[r["row"], r["col"]] = a["ci_high"] - a["ci_low"]
    with rasterio.open(path, "w", driver="GTiff", width=cols, height=rows, count=2, dtype="float64") as ds:  # fixture-local grid: no CRS, no geotransform
        ds.write(p, 1)
        ds.write(w, 2)
        ds.set_band_description(1, "p_anomaly_calibrated")
        ds.set_band_description(2, "ci_width_95")


def run(seed: int, config, out) -> dict:
    cfg_path = C.guard_path(config)
    cfg = C.load_config(cfg_path)
    scene = A._load_scene(cfg_path.parent, cfg["scenes"]["run"].format(seed=seed))
    scfg = A.scene_to_cfg(cfg, scene)
    cells, meta = C.combine(scfg)
    model = A.fit_calibrated(cfg, seed=seed, cfg_dir=cfg_path.parent)
    if model.ece_holdout > A.ECE_GATE:
        raise C.FusionError(f"ECE gate failed on synthetic holdouts: {model.ece_holdout}")
    for rec, an in zip(cells, A.score_scene(model, A.features(cfg, scene))):
        rec["anomaly"] = an
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    doc = {"spec": SPEC, "seed": seed, "config_sha256": _sha(cfg_path), "meta": meta, "cells": cells,
           "anomaly": {"detector": "pyod.ECOD", "calibration": "isotonic", "n_boot": A.N_BOOT,
                       "ece_bins": A.ECE_BINS, "ece_holdout": model.ece_holdout, "brier_holdout": model.brier_holdout,
                       "ci": "percentile 95%", "embeddings": A.FUSION_EMBEDDINGS},
           "note": "hint layer only; does not change POA (only CleanScorer.update does)"}
    jp = out / f"fusion_{seed}.json"
    jp.write_text(_fmt(doc) + "\n")
    tp = out / f"uncertainty_map_{seed}.tif"
    _write_tif(tp, cells, scfg["grid"]["rows"], scfg["grid"]["cols"])
    return {"seed": seed, "config_sha256": doc["config_sha256"], jp.name: _sha(jp), tp.name: _sha(tp)}
