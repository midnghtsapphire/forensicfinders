# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Grok Bot as Sense-Quartz pair (Quartz-N navigator, Quartz-D driver) for Audrey Evans
# When: 2026-11-04
# Why:  Offline, deterministic comparison of our constrained_nnls_unmix against HySUPP
#       (MIT, github.com/BehnoodRasti/HySUPP @ cb7d633a) as a *reference only*.
#       Component / registry 2360 (Verity: NEW-22 → 2360).
# What: Seeded synthetic mixtures (splib07 PD reference-oracle endmembers, else Gaussians) ->
#       abundance RMSE (+ mean SAM) table as a JSON-serialisable dict.
# Notes: HySUPP is NOT a dependency. It is not pip-packaged; it is run only OFFLINE as a
#       separate CLI process in its own venv outside the repo (Strata ruling, hard rule 5),
#       gated by HYSUPP_ROOT; only result JSON comes back. GPL-3.0 spams is never imported,
#       vendored, pinned or shipped here. Our code: UNLICENSED (private repo;
#       licence pending Audrey).
# ══════════════════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
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
    """Return (E as B x K, names, source). splib07 reference oracle if present, else Gaussians."""
    try:
        from .splib07_endmembers import load_endmembers
        _wl, E, got = load_endmembers(names, as_matrix=True)
        if names is None:
            E, got = E[:, :n_end], list(got)[:n_end]
        E = np.asarray(E, dtype=float)
        if np.all(np.isfinite(E)):
            return E, list(got), "usgs_splib07_pd_reference_oracle"
    except Exception:  # oracle missing -> fall back
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


def load_hysupp_fcls(root: Optional[str] = None, *, workdir: Optional[str] = None) -> Callable:
    """Strata ruling (hard rule 5): GPL spams runs OFFLINE only, as a SEPARATE CLI process in
    its own venv OUTSIDE this repo, and may only write comparison result data back. This
    function never imports HySUPP or spams. It returns a callable that writes (Y, E) to an
    .npz, runs the external command, and reads back a JSON result file.

    Gated by HYSUPP_ROOT (external HySUPP checkout). The command is SPAMS_COMPARE_CMD
    (an executable script outside the repo; called as `CMD IN.npz OUT.json`), or
    `$HYSUPP_VENV/bin/python $HYSUPP_ROOT/hysupp_fcls_cli.py IN.npz OUT.json`.
    Output JSON: {"A": [[...K rows of N...]]}. Raises HySUPPUnavailable if not configured."""
    root = root or os.environ.get("HYSUPP_ROOT")
    if not root:
        raise HySUPPUnavailable(
            "HySUPP not configured: set HYSUPP_ROOT (external checkout of "
            f"{HYSUPP_URL} at {HYSUPP_PINNED_COMMIT}) plus SPAMS_COMPARE_CMD or HYSUPP_VENV; "
            "spams runs only out-of-process (Strata ruling).")
    cmd = os.environ.get("SPAMS_COMPARE_CMD")
    if cmd:
        argv = shlex.split(cmd)
    else:
        venv = os.environ.get("HYSUPP_VENV")
        if not venv:
            raise HySUPPUnavailable("HYSUPP_ROOT set but neither SPAMS_COMPARE_CMD nor HYSUPP_VENV")
        argv = [str(Path(venv) / "bin" / "python"), str(Path(root) / "hysupp_fcls_cli.py")]
    repo = Path(__file__).resolve().parents[3]
    for a in argv[:2]:
        ap = Path(a).expanduser()
        if ap.is_absolute() and repo in ap.resolve().parents:
            raise HySUPPUnavailable(f"external runner must live outside the repo: {a}")
    results = Path(workdir or os.environ.get("HYSUPP_RESULTS_DIR")
                   or tempfile.mkdtemp(prefix="hysupp_results_"))
    results.mkdir(parents=True, exist_ok=True)

    def _run(Y: np.ndarray, E: np.ndarray) -> np.ndarray:
        inp, outp = results / "hysupp_input.npz", results / "hysupp_fcls_result.json"
        np.savez(inp, Y=Y, E=E)
        try:
            subprocess.run(argv + [str(inp), str(outp)], check=True, timeout=600,
                           capture_output=True, text=True)
        except (OSError, subprocess.SubprocessError) as exc:
            raise HySUPPUnavailable(f"external HySUPP runner failed: {exc}") from exc
        return np.asarray(json.loads(outp.read_text())["A"], dtype=float)

    return _run


# ── harness ─────────────────────────────────────────────────────────────────────────────
def compare(*, seed: int = DEFAULT_SEED, n_pixels: int = 64, noise_std: float = 0.005,
            names=None, include_hysupp: bool = True) -> dict:
    """Run baseline (always) and HySUPP FCLS (if loadable). JSON-serialisable result."""
    E, got, source = load_reference_endmembers(names, seed=seed)
    Y, A = make_mixtures(E, n_pixels, noise_std=noise_std, seed=seed)
    out = {
        "component": "2360", "registry": 2360, "seed": seed, "n_pixels": n_pixels,
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
