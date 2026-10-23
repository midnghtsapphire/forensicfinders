"""Gaussian decomposition of a 1-D full-waveform lidar return (registry 985).

Fits a sum of Gaussians A*exp(-(t-mu)^2/(2*sigma^2)) to a waveform after
baseline (noise floor) removal. The last return in time (largest mu) is taken
as the ground candidate, which is the usual convention for GEDI L1B
waveforms (see docs/research/full-waveform-lidar.md, registry 2060).
Synthetic tests only; no claim of accuracy on real data.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import curve_fit
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks


@dataclass(frozen=True)
class Peak:
    amplitude: float
    center: float   # same units as t (e.g. ns or bin index)
    sigma: float


def gaussian_sum(t: np.ndarray, *p: float) -> np.ndarray:
    t = np.asarray(t, dtype=float)
    out = np.zeros_like(t)
    for a, mu, s in zip(p[0::3], p[1::3], p[2::3]):
        out += a * np.exp(-((t - mu) ** 2) / (2.0 * s * s))
    return out


def decompose(wf, t=None, *, noise_sigmas: float = 4.0, min_distance: int = 3, smooth: float = 1.5,
              max_peaks: int = 8) -> dict:
    """Return {"peaks": [Peak...] sorted by center, "ground": Peak|None,
    "baseline": float, "noise": float}."""
    y = np.asarray(wf, dtype=float)
    if y.ndim != 1 or y.size < 5:
        raise ValueError("waveform must be 1-D with at least 5 samples")
    t = np.arange(y.size, dtype=float) if t is None else np.asarray(t, dtype=float)
    if t.shape != y.shape:
        raise ValueError("t and waveform must have the same shape")
    baseline = float(np.median(y))
    noise = float(1.4826 * np.median(np.abs(y - baseline))) or 1e-12
    r = y - baseline
    rs = gaussian_filter1d(r, smooth) if smooth > 0 else r
    thr = noise_sigmas * noise
    idx, props = find_peaks(rs, height=thr, prominence=thr, distance=min_distance)
    if idx.size == 0:
        return {"peaks": [], "ground": None, "baseline": baseline, "noise": noise}
    keep = np.argsort(props["peak_heights"])[::-1][:max_peaks]
    idx = np.sort(idx[keep])
    dt = float(np.median(np.diff(t))) if t.size > 1 else 1.0
    p0, lo, hi = [], [], []
    for i in idx:
        p0 += [r[i], t[i], 2.0 * dt]
        lo += [0.0, t[0], 0.5 * dt]
        hi += [np.inf, t[-1], (t[-1] - t[0])]
    try:
        p, _ = curve_fit(gaussian_sum, t, r, p0=p0, bounds=(lo, hi), maxfev=20000)
    except RuntimeError:
        p = np.asarray(p0)
    peaks = sorted((Peak(float(a), float(mu), float(abs(s)))
                    for a, mu, s in zip(p[0::3], p[1::3], p[2::3])),
                   key=lambda k: k.center)
    return {"peaks": peaks, "ground": peaks[-1], "baseline": baseline, "noise": noise}
