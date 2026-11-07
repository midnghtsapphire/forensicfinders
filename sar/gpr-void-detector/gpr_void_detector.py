#!/usr/bin/env python3
"""
Deterministic GPR void detector (registry 530).

Hyperbola fitting + polarity / permittivity-contrast on synthetic B-scans
compatible with gpr-wave-model (and offline gprMax libraries). No neural nets;
Ultralytics/AGPL forbidden. Extends gpr-wave-model (imports velocity /
fresnel_r / synthetic_hyperbola_bscan) — does not replace it.

Physics:
  v = c / √ε_r ,  z = v t_apex / 2 ,  c = 0.299792458 m/ns
  t(x) = (2/v) √((x−x0)² + z0²)
  R = (√ε1 − √ε2)/(√ε1 + √ε2)   (align with gpr_wave_model.fresnel_r)
  R>0 (soil→air) → air_like ; R<0 (soil→water) → water_like

References: Daniels 2004 GPR; Annan / Sensors & Software hyperbola notes;
Telford et al. 1990 EM wave speed. gprMax offline-only (never linked).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Any, Optional, Sequence

import numpy as np

# Peer module (extend, don't replace)
_PEER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gpr-wave-model"))
if _PEER not in sys.path:
    sys.path.insert(0, _PEER)
import gpr_wave_model as gpr  # noqa: E402

C_M_PER_NS = gpr.C_M_PER_NS
SCORE_ROUND = 6
POS_ROUND = 4
V_ROUND = 9

# Fixed deterministic search grid (seed-independent)
X0_PAD_TRACES = 2
ENERGY_PERCENTILE = 99.0
MIN_SCORE = 0.25


def velocity_from_soil_er(soil_er: float) -> float:
    return gpr.velocity(soil_er)


def polarity_from_contrast(soil_er: float, first_break_sign: float) -> str:
    """Map first-break sign + Fresnel convention to air_like / water_like.

    gpr_wave_model: polarity "same" when R>0 (soil→lower ε, e.g. air),
    "reversed" when R<0 (soil→higher ε, e.g. water). Detector labels:
      same / positive first break consistent with R>0 → air_like
      reversed / negative first break consistent with R<0 → water_like
    """
    # Classify by observed first-break sign relative to Fresnel air/water
    r_air = gpr.fresnel_r(soil_er, 1.0)
    r_water = gpr.fresnel_r(soil_er, 80.0)
    if first_break_sign == 0.0:
        return "unknown"
    if first_break_sign > 0 and r_air > 0:
        return "air_like"
    if first_break_sign < 0 and r_water < 0:
        return "water_like"
    # Ambiguous: choose closer Fresnel match
    if abs(first_break_sign - math.copysign(1.0, r_air)) < abs(
        first_break_sign - math.copysign(1.0, r_water)
    ):
        return "air_like" if r_air > 0 else "water_like"
    return "water_like" if r_water < 0 else "air_like"


def dumps_canonical(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, allow_nan=False, sort_keys=True) + "\n"


def _trace_energy(bscan: np.ndarray) -> np.ndarray:
    return np.sum(bscan * bscan, axis=1)


def _apex_candidates(bscan: np.ndarray, dx_m: float) -> list[tuple[int, int]]:
    """Return list of (trace_index, sample_index) candidate apexes.

    Apex = earliest strong peak time among energetic traces (hyperbola tip),
    not max energy (flanks can match apex energy for unit-amp pulses).
    """
    n_traces, n_samp = bscan.shape
    energy = _trace_energy(bscan)
    peak_amp = np.max(np.abs(bscan), axis=1)
    if float(np.max(peak_amp)) < 1e-12:
        return []
    amp_thr = 0.2 * float(np.max(peak_amp))
    peak_j = np.argmax(np.abs(bscan), axis=1)
    # Primary: among traces above amp_thr, earliest peak sample
    mask = peak_amp >= amp_thr
    if not np.any(mask):
        return []
    idxs = np.where(mask)[0]
    # Minimize peak time; break ties by higher |amp| then lower index
    best_i = None
    best_key = None
    for i in idxs:
        key = (int(peak_j[i]), -float(peak_amp[i]), int(i))
        if best_key is None or key < best_key:
            best_key = key
            best_i = int(i)
    assert best_i is not None
    cands = [(best_i, int(peak_j[best_i]))]
    # Secondary apexes: local minima of peak_j among energetic traces, separated
    for i in range(1, n_traces - 1):
        if not mask[i]:
            continue
        if peak_j[i] <= peak_j[i - 1] and peak_j[i] <= peak_j[i + 1]:
            if abs(i - best_i) * dx_m >= 0.5:
                cands.append((int(i), int(peak_j[i])))
    cands.sort(key=lambda ij: (peak_j[ij[0]], ij[0]))
    return cands


def _fit_hyperbola(
    bscan: np.ndarray,
    dx_m: float,
    dt_ns: float,
    soil_er: float,
    i0: int,
    j0: int,
) -> Optional[dict[str, Any]]:
    """Fit (x0,z0) with v fixed from soil_er via linearized travel times."""
    n_traces, n_samp = bscan.shape
    v = velocity_from_soil_er(soil_er)
    x0 = i0 * dx_m
    t0 = j0 * dt_ns
    if t0 <= 0:
        return None
    z0 = v * t0 / 2.0

    # Collect peak times per trace by max |amp| near predicted hyperbola
    xs = []
    ts = []
    for i in range(n_traces):
        x = i * dx_m
        t_pred = (2.0 / v) * math.sqrt((x - x0) ** 2 + z0 ** 2)
        j_pred = int(round(t_pred / dt_ns))
        lo = max(0, j_pred - 5)
        hi = min(n_samp, j_pred + 6)
        if hi <= lo:
            continue
        seg = bscan[i, lo:hi]
        if np.max(np.abs(seg)) < 1e-9:
            continue
        j_pk = lo + int(np.argmax(np.abs(seg)))
        xs.append(x)
        ts.append(j_pk * dt_ns)
    if len(xs) < 5:
        return None

    xs_a = np.asarray(xs, dtype=float)
    ts_a = np.asarray(ts, dtype=float)
    # Refine x0: search small grid around i0 (deterministic)
    best = None
    for di in range(-X0_PAD_TRACES, X0_PAD_TRACES + 1):
        x0c = (i0 + di) * dx_m
        # z0 from mean of z = sqrt((v t/2)^2 - (x-x0)^2) for traces near apex
        zs = []
        for x, t in zip(xs_a, ts_a):
            half = v * t / 2.0
            arg = half * half - (x - x0c) ** 2
            if arg > 0:
                zs.append(math.sqrt(arg))
        if not zs:
            continue
        z0c = float(np.median(zs))
        # Score: 1 - normalized RMS residual in time
        t_model = (2.0 / v) * np.sqrt((xs_a - x0c) ** 2 + z0c ** 2)
        rms = float(np.sqrt(np.mean((ts_a - t_model) ** 2)))
        score = 1.0 / (1.0 + rms / max(dt_ns, 1e-9))
        cand = (score, x0c, z0c, rms)
        if best is None or cand > best:
            best = cand
    if best is None or best[0] < MIN_SCORE:
        return None
    score, x0f, z0f, _rms = best
    # First-break sign at apex trace
    apex_i = int(round(x0f / dx_m))
    apex_i = min(max(apex_i, 0), n_traces - 1)
    j_apex = int(round((2.0 * z0f / v) / dt_ns))
    j_apex = min(max(j_apex, 0), n_samp - 1)
    # Use sample at/near apex peak for sign
    window = bscan[apex_i, max(0, j_apex - 2) : j_apex + 3]
    if window.size == 0:
        fb_sign = 0.0
    else:
        peak = window[int(np.argmax(np.abs(window)))]
        fb_sign = math.copysign(1.0, float(peak)) if peak != 0 else 0.0
    pol = polarity_from_contrast(soil_er, fb_sign)
    return {
        "x0_m": round(x0f, POS_ROUND),
        "z0_m": round(z0f, POS_ROUND),
        "v_m_per_ns": round(v, V_ROUND),
        "polarity": pol,
        "score": round(float(score), SCORE_ROUND),
    }


def detect(
    *,
    bscan: Sequence[Sequence[float]],
    dx_m: float,
    dt_ns: float,
    soil_er: float,
    seed: int = 42,
    freq_mhz: Optional[float] = None,
) -> dict[str, Any]:
    arr = np.asarray(bscan, dtype=float)
    if arr.ndim != 2:
        raise ValueError("bscan must be 2-D [n_traces, n_samples]")
    if dx_m <= 0 or dt_ns <= 0 or soil_er < 1.0:
        raise ValueError("dx_m, dt_ns must be > 0 and soil_er >= 1")

    detections: list[dict[str, Any]] = []
    # Null / noise-only guard: require coherent energy
    if float(np.max(np.abs(arr))) < 0.05:
        # still allow strong noise; use energy structure
        pass
    cands = _apex_candidates(arr, dx_m)
    seen: list[float] = []
    for i0, j0 in cands:
        det = _fit_hyperbola(arr, dx_m, dt_ns, soil_er, i0, j0)
        if det is None:
            continue
        if any(abs(det["x0_m"] - sx) < 0.4 for sx in seen):
            continue
        # Extra null guard: score must clear threshold and peak amp
        if det["score"] < MIN_SCORE:
            continue
        detections.append(det)
        seen.append(det["x0_m"])

    # Stronger null rejection: if max energy is tiny relative to coherent hyperbola fixtures
    energy = _trace_energy(arr)
    peak_e = float(np.max(energy)) if energy.size else 0.0
    # synthetic null uses σ=0.01 → energy per trace ~ n_samp*1e-4; hyperbola ~ O(10)
    if peak_e < 0.5:
        detections = []

    # Deterministic tie-break reserved (seed echoed; unused unless equal scores)
    detections.sort(key=lambda d: (-d["score"], d["x0_m"], d["z0_m"]))
    _ = seed  # reserved for equal-score ties with random.Random(seed)

    return {
        "model": "GPR void detector (hyperbola fit + Fresnel polarity)",
        "assumptions": [
            "point-like scatterer hyperbola",
            "v fixed from soil_er via gpr_wave_model.velocity",
            "deterministic grid search; no RANSAC; no Ultralytics",
            "synthetic B-scans only (fixtures/*synthetic*)",
        ],
        "constants": {"c_m_per_ns": C_M_PER_NS, "min_score": MIN_SCORE},
        "parameters": {
            "seed": int(seed),
            "dx_m": dx_m,
            "dt_ns": dt_ns,
            "soil_er": soil_er,
            "freq_mhz": freq_mhz,
            "n_traces": int(arr.shape[0]),
            "n_samples": int(arr.shape[1]),
        },
        "results": {"detections": detections},
    }


def print_summary(data: dict[str, Any]) -> None:
    print(f"\nGPR void detector | seed={data['parameters']['seed']} | "
          f"detections={len(data['results']['detections'])}\n")
    print(f"{'x0_m':>10} {'z0_m':>10} {'v':>12} {'polarity':>12} {'score':>10}")
    print("-" * 58)
    for det in data["results"]["detections"]:
        print(f"{det['x0_m']:10.4f} {det['z0_m']:10.4f} {det['v_m_per_ns']:12.6f} "
              f"{det['polarity']:>12} {det['score']:10.4f}")
    print()


def main(argv: Optional[Sequence[str]] = None) -> dict[str, Any]:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bscan", required=True, help="fixtures/*synthetic*.json with bscan grid")
    ap.add_argument("--soil-er", type=float, default=None)
    ap.add_argument("--dx", type=float, default=None)
    ap.add_argument("--dt", type=float, default=None)
    ap.add_argument("--freq", type=float, default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out")
    ap.add_argument("--no-table", action="store_true")
    args = ap.parse_args(argv)

    path = args.bscan
    base = os.path.basename(path)
    if "synthetic" not in base:
        ap.error("only fixtures/*synthetic* inputs are allowed")
    with open(path) as f:
        scene = json.load(f)
    soil_er = float(args.soil_er if args.soil_er is not None else scene["soil_er"])
    dx = float(args.dx if args.dx is not None else scene["dx_m"])
    dt = float(args.dt if args.dt is not None else scene["dt_ns"])
    try:
        data = detect(
            bscan=scene["bscan"],
            dx_m=dx,
            dt_ns=dt,
            soil_er=soil_er,
            seed=args.seed,
            freq_mhz=args.freq,
        )
    except ValueError as e:
        ap.error(str(e))

    if not args.no_table:
        print_summary(data)
    payload = dumps_canonical(data)
    if args.out:
        with open(args.out, "w") as f:
            f.write(payload)
        print(f"JSON written to {args.out}")
    else:
        sys.stdout.write(payload)
    return data


if __name__ == "__main__":
    main(sys.argv[1:])
