"""FUSION_SPEC v0.2 §3: seeded anomaly score + calibrated probability + 1000-resample bootstrap.

Placed in its own module (spec §2 scopes combine.py to the combiner; §3 names no module).
Detector: PyOD ECOD (deterministic, parameter-free). Calibration: isotonic (sklearn) fitted on
synthetic calibration scenes; ECE (15 equal-width bins) + Brier on disjoint synthetic holdouts.
Bootstrap: B=1000 resamples of the calibration set, replicate i seeded by SeedSequence([seed, i]).
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")

import json
import math
from dataclasses import dataclass

import numpy as np
from pyod.models.ecod import ECOD
from sklearn.isotonic import IsotonicRegression

from . import combine as C

N_BOOT = 1000
ECE_BINS = 15
ECE_GATE = 0.05
FUSION_EMBEDDINGS = 0  # no learned embeddings; no TerraMesh/TerraTorch
FusionError = C.FusionError
BAND_KEYS = ("anomaly_score", "p_anomaly_calibrated", "ci_low", "ci_high", "n_boot", "ece_holdout")


def ece(p, y, bins: int = ECE_BINS) -> float:
    p, y = np.asarray(p, float), np.asarray(y, float)
    idx = np.minimum((p * bins).astype(int), bins - 1)
    tot = 0.0
    for b in range(bins):
        m = idx == b
        if m.any():
            tot += m.sum() / len(p) * abs(p[m].mean() - y[m].mean())
    return float(tot)


def scene_to_cfg(cfg: dict, scene: dict) -> dict:
    c = {k: v for k, v in cfg.items() if k not in ("layers",)}
    c["grid"] = scene["grid"]
    c["layers"] = [dict(L, values=scene["layers"][L["name"]]) for L in cfg["layers"]]
    return C.validate_config(c)


def features(cfg: dict, scene: dict) -> np.ndarray:
    recs, meta = C.combine(scene_to_cfg(cfg, scene))
    # fixed column order across scenes; a degenerate (flagged) layer has normalised=None -> 0-column
    names = [L["name"] for L in cfg["layers"]]
    X = np.array([[0.0 if r["contributions"][n]["normalised"] is None else r["contributions"][n]["normalised"] for n in names] for r in recs], float)
    return X


def _load_scene(cfg_dir, name):
    p = C.guard_path(cfg_dir / name)
    s = json.loads(p.read_text())
    C._reject_geo(s, name)
    return s


@dataclass
class Calibrated:
    detector: ECOD
    iso: IsotonicRegression
    cal_s: np.ndarray
    cal_y: np.ndarray
    ece_holdout: float
    brier_holdout: float
    seed: int


def fit_calibrated(cfg: dict, seed: int, cfg_dir=None) -> Calibrated:
    from pathlib import Path
    cfg_dir = Path(cfg_dir) if cfg_dir else Path(__file__).resolve().parent / "fixtures"
    fmt = cfg["scenes"]
    cal = [_load_scene(cfg_dir, fmt["calibration"].format(seed=s)) for s in cfg["calibration_seeds"]]
    hold = [_load_scene(cfg_dir, fmt["holdout"].format(seed=s)) for s in cfg["holdout_seeds"]]
    Xc = np.vstack([features(cfg, s) for s in cal])
    yc = np.concatenate([np.asarray(s["labels"]).ravel() for s in cal])
    det = ECOD(contamination=0.08, n_jobs=1).fit(Xc)
    sc = det.decision_function(Xc)
    iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit(sc, yc)
    Xh = np.vstack([features(cfg, s) for s in hold])
    yh = np.concatenate([np.asarray(s["labels"]).ravel() for s in hold])
    ph = iso.predict(det.decision_function(Xh))
    return Calibrated(det, iso, sc, yc, ece(ph, yh), float(np.mean((ph - yh) ** 2)), seed)


def score_scene(model: Calibrated, X: np.ndarray) -> list[dict]:
    s = model.detector.decision_function(X)
    p = model.iso.predict(s)
    n = len(model.cal_s)
    boots = np.empty((N_BOOT, len(s)))
    for i in range(N_BOOT):
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([model.seed, i])))
        j = rng.integers(0, n, n)
        boots[i] = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit(model.cal_s[j], model.cal_y[j]).predict(s)
    lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
    out = []
    for k in range(len(s)):
        rec = {"anomaly_score": float(s[k]), "p_anomaly_calibrated": float(p[k]),
               "ci_low": float(min(lo[k], p[k])), "ci_high": float(max(hi[k], p[k])),
               "n_boot": N_BOOT, "ece_holdout": model.ece_holdout}
        out.append(check_banded(rec))
    return out


def check_banded(rec: dict) -> dict:
    """Writer guard: refuse any score lacking its uncertainty band."""
    for k in BAND_KEYS:
        if k not in rec or rec[k] is None:
            raise FusionError(f"anomaly record missing {k}; refusing unbanded score")
    if rec["n_boot"] != N_BOOT:
        raise FusionError("n_boot must be 1000")
    if not (rec["ci_low"] <= rec["p_anomaly_calibrated"] <= rec["ci_high"]):
        raise FusionError("calibrated p outside its CI")
    if not math.isfinite(rec["ece_holdout"]) or rec["ece_holdout"] > ECE_GATE:
        raise FusionError(f"ECE gate failed: {rec['ece_holdout']}")
    return rec
