# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Grok Bot as Sense-Quartz pair (Quartz-N navigator, Quartz-D driver) for Audrey Evans
# When: 2026-11-04
# Why:  Offline, deterministic comparison of our constrained_nnls_unmix against HySUPP
#       (MIT, github.com/BehnoodRasti/HySUPP @ cb7d633a) as a *reference only*.
#       Component NEW-22 / registry 2360.
# What: Seeded synthetic mixtures (splib07 PD fixture endmembers, else Gaussians) ->
#       abundance RMSE (+ mean SAM) table as a JSON-serialisable dict.
# Notes: HySUPP is NOT a dependency. It is not pip-packaged; it is loaded only if the env
#       var HYSUPP_ROOT points at a local checkout. HySUPP's FCLS imports `spams`, which is
#       GPL-3.0 -> we never install or vendor it. Our code: UNLICENSED (private repo;
#       licence pending Audrey).
# ══════════════════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import importlib.util
import json
import os
import sys
import types
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from .nnls_unmix import constrained_nnls_unmix

HYSUPP_PINNED_COMMIT = "cb7d633a3b4a458504e31d1e5fcd3f6a00be688d"
HYSUPP_URL = "https://github.com/BehnoodRasti/HySUPP"
DEFAULT_SEED = 20261104


class HySUPPUnavailable(RuntimeError):
    """Raised when the optional HySUPP reference cannot be loaded."""


# ── data ────────────────────────────────────────────────────────────────────────────────
def _gaussian_endmembers(n_end: int, n_bands: int, rng: np.random.Generator):
    x = np.linspace(0.0, 1.0, n_bands)
    E = np.empty((n_bands, n_end))
    for k in range(n_end):
        mu = (k + 0.5) / n_end
        E[:, k] = 0.1 + 0.8 * np.exp(-((x - mu) ** 2) / (2 * 0.08**2))
    return E, [f"gauss{k}" for k in range(n_end)]


def load_reference_endmembers(names=None, *, n_end: int = 3, n_bands: int = 200,
                              seed: int = DEFAULT_SEED):
    """Return (E as B x K, names, source). splib07 fixture if present, else Gaussians."""
    try:
        from .splib07_endmembers import load_endmembers
        _wl, E, got = load_endmembers(names, as_matrix=True)
        if names is None:
            E, got = E[:, :n_end], list(got)[:n_end]
        E = np.asarray(E, dtype=float)
        if np.all(np.isfinite(E)):
            return E, list(got), "usgs_splib07_pd_fixture"
    except Exception:  # fixture branch not merged / file missing -> fall back
        pass
    E, got = _gaussian_endmembers(n_end, n_bands, np.random.default_rng(seed))
    return E, got, "synthetic_gaussian"


def make_mixtures(E: np.ndarray, n_pixels: int = 64, *, noise_std: float = 0.0,
                  seed: int = DEFAULT_SEED):
    """Dirichlet abundances (K x N) and pixels Y = E @ A + noise (B x N). Deterministic."""
    rng = np.random.default_rng(seed)
    K = E.shape[1]
    A = rng.dirichlet(np.ones(K), size=n_pixels).T
    Y = E @ A
    if noise_std > 0:
        Y = Y + rng.normal(0.0, noise_std, Y.shape)
    return Y, A


# ── metrics ─────────────────────────────────────────────────────────────────────────────
def abundance_rmse(A_true: np.ndarray, A_est: np.ndarray) -> float:
    return float(np.sqrt(np.mean((A_true - A_est) ** 2)))


def mean_sam_deg(Y: np.ndarray, Y_hat: np.ndarray) -> float:
    num = np.sum(Y * Y_hat, axis=0)
    den = np.linalg.norm(Y, axis=0) * np.linalg.norm(Y_hat, axis=0)
    cos = np.clip(num / np.where(den == 0, 1, den), -1.0, 1.0)
    return float(np.degrees(np.mean(np.arccos(cos))))


# ── methods ─────────────────────────────────────────────────────────────────────────────
def run_baseline_nnls(Y: np.ndarray, E: np.ndarray, names) -> np.ndarray:
    """Our constrained_nnls_unmix on a 1 x N 'image'. Returns K x N."""
    cube = Y.T[np.newaxis, :, :]
    fracs, _ = constrained_nnls_unmix(cube, {n: E[:, i] for i, n in enumerate(names)})
    return np.stack([fracs[n][0] for n in names], axis=0)


def load_hysupp_fcls(root: Optional[str] = None) -> Callable:
    """Load HySUPP's FCLS from a local checkout (HYSUPP_ROOT) without importing its
    torch-heavy package __init__. Raises HySUPPUnavailable with a clear message."""
    root = root or os.environ.get("HYSUPP_ROOT")
    if not root:
        raise HySUPPUnavailable(
            "HySUPP not configured: set HYSUPP_ROOT to a checkout of "
            f"{HYSUPP_URL} at {HYSUPP_PINNED_COMMIT} (comparison reference only).")
    sup = Path(root) / "src" / "model" / "supervised"
    if not (sup / "FCLS.py").is_file():
        raise HySUPPUnavailable(f"HYSUPP_ROOT={root} has no src/model/supervised/FCLS.py")
    if str(root) not in sys.path:  # base.py uses absolute `src.` imports
        sys.path.insert(0, str(root))
    pkg = "_hysupp_supervised"
    try:
        mod = types.ModuleType(pkg)
        mod.__path__ = [str(sup)]
        sys.modules[pkg] = mod
        for name in ("base", "FCLS"):
            spec = importlib.util.spec_from_file_location(f"{pkg}.{name}", sup / f"{name}.py")
            m = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = m
            spec.loader.exec_module(m)
        model = sys.modules[f"{pkg}.FCLS"].FCLS()
    except ImportError as exc:  # cvxopt / spams (GPL-3.0) missing
        raise HySUPPUnavailable(f"HySUPP FCLS import failed: {exc}") from exc
    return lambda Y, E: np.asarray(model.compute_abundances(Y, E))


# ── harness ─────────────────────────────────────────────────────────────────────────────
def compare(*, seed: int = DEFAULT_SEED, n_pixels: int = 64, noise_std: float = 0.005,
            names=None, include_hysupp: bool = True) -> dict:
    """Run baseline (always) and HySUPP FCLS (if loadable). JSON-serialisable result."""
    E, got, source = load_reference_endmembers(names, seed=seed)
    Y, A = make_mixtures(E, n_pixels, noise_std=noise_std, seed=seed)
    out = {
        "component": "NEW-22", "registry": 2360, "seed": seed, "n_pixels": n_pixels,
        "noise_std": noise_std, "endmember_source": source, "endmembers": got,
        "n_bands": int(E.shape[0]), "hysupp_commit": HYSUPP_PINNED_COMMIT, "results": {},
    }
    A_b = run_baseline_nnls(Y, E, got)
    out["results"]["nnls_baseline"] = {
        "status": "ok", "abundance_rmse": abundance_rmse(A, A_b),
        "mean_sam_deg": mean_sam_deg(Y, E @ A_b)}
    if include_hysupp:
        try:
            A_h = load_hysupp_fcls()(Y, E)
            out["results"]["hysupp_fcls"] = {
                "status": "ok", "abundance_rmse": abundance_rmse(A, A_h),
                "mean_sam_deg": mean_sam_deg(Y, E @ A_h)}
        except HySUPPUnavailable as exc:
            out["results"]["hysupp_fcls"] = {"status": "skipped", "reason": str(exc)}
    return out


if __name__ == "__main__":
    print(json.dumps(compare(), indent=2))
