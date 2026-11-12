# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Humus-D (driver) / Humus-N (navigator), Grok Bot, for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  SenseCrew Humus owns soil dielectric/moisture. Extend the existing Topp forward
#       map with the Topp inverse, Mironov (2009) mineralogy-based complex permittivity
#       (clay %), and a seeded Topp↔Mironov cross-check over a synthetic moisture/clay grid.
# What: ADDITIVE. topp_dielectric kept byte-compatible for test_engines.test_topp.
# Units: theta_v / soil_moisture [m3 m^-3]; clay_pct [mass % 0–100]; eps relative [-];
#        freq_hz [Hz]. Never treat theta_v as percent.
# Citations:
#   Topp et al. 1980 — DOI 10.1029/WR016i003p00574
#   Mironov et al. 2009 — DOI 10.1109/TGRS.2008.2011631
#   Mironov correction 2009 — DOI 10.1109/TGRS.2009.2023842
# Notes: Synthetic/procedural only. No LUCAS. No case/hfmr/evidence/public_records.
# ══════════════════════════════════════════════════════════════════════════════════════════
"""Soil dielectric models: Topp (1980) and Mironov (2009), plus seeded cross-check."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Mapping

import numpy as np

# Free-space permittivity (F/m) — Mironov Debye conductivity term.
_E0 = 8.854e-12
_E_INF = 4.9  # high-frequency limit for bound/free soil water (Mironov 2009)


def topp_dielectric(soil_moisture: np.ndarray) -> np.ndarray:
    """Topp et al. cubic empirical model for real dielectric from volumetric moisture.

    Parameters
    ----------
    soil_moisture :
        Volumetric water content theta_v in m3/m3 (fraction). Clipped to [0, 0.6].

    Returns
    -------
    Real relative permittivity eps' (dimensionless), Topp 1980 eq.
    DOI 10.1029/WR016i003p00574
    """
    m = np.clip(soil_moisture, 0.0, 0.6)
    return 3.03 + 9.3 * m + 146.0 * m**2 - 76.7 * m**3


def topp_volumetric_water(permittivity: np.ndarray) -> np.ndarray:
    """Topp (1980) inverse: volumetric water content from real relative permittivity.

    Parameters
    ----------
    permittivity :
        Real relative permittivity eps' (dimensionless). Must be >= 0.

    Returns
    -------
    theta_v in m3/m3 (fraction), not percent.
    DOI 10.1029/WR016i003p00574
    """
    eps = np.asarray(permittivity, dtype=float)
    if np.any(eps < 0.0):
        raise ValueError("permittivity must be >= 0 (relative dielectric constant)")
    # Topp 1980 inverse cubic (their eq. relating theta_v to eps).
    return (
        -5.3e-2
        + 2.92e-2 * eps
        - 5.5e-4 * eps**2
        + 4.3e-6 * eps**3
    )


def _as_float_array(x: Any) -> np.ndarray:
    return np.asarray(x, dtype=float)


def mironov_dielectric(
    theta_v: Any,
    clay_pct: float,
    freq_hz: float = 1.4e9,
) -> np.ndarray:
    """Mironov (2009) mineralogy-based complex relative permittivity.

    Parameters
    ----------
    theta_v :
        Volumetric water content [m3/m3] (scalar or array).
    clay_pct :
        Clay mass fraction in percent [0, 100]. Required (mineralogy input).
    freq_hz :
        Frequency in Hz (default 1.4e9, L-band).

    Returns
    -------
    Complex relative permittivity eps = eps' - j eps'' (NumPy complex array).

    Citations
    ---------
    Mironov et al., IEEE TGRS 2009, DOI 10.1109/TGRS.2008.2011631
    Correction DOI 10.1109/TGRS.2009.2023842
    """
    if clay_pct is None:
        raise TypeError("clay_pct is required (clay mass percent 0–100)")
    c = float(clay_pct)
    if not (0.0 <= c <= 100.0):
        raise ValueError("clay_pct must be in [0, 100] mass percent")
    mv = np.clip(_as_float_array(theta_v), 0.0, 0.6)
    f = float(freq_hz)
    if f <= 0.0:
        raise ValueError("freq_hz must be > 0")

    # Empirical clay fits (Mironov 2009 eqs. 17–25 region).
    sigma_b = 0.3112 + 0.467e-2 * c
    sigma_u = 0.3631 + 1.217e-2 * c
    e0_b = 79.8 - 85.4e-2 * c + 32.7e-4 * c**2
    e0_u = 100.0
    tau_b = 1.062e-11 + 3.450e-14 * c
    tau_u = 8.5e-12

    def debye_real(e0: float, tau: float) -> float:
        w = 2.0 * np.pi * f * tau
        return _E_INF + (e0 - _E_INF) / (1.0 + w**2)

    def debye_imag(e0: float, tau: float, sigma: float) -> float:
        w = 2.0 * np.pi * f * tau
        return (e0 - _E_INF) * w / (1.0 + w**2) + sigma / (2.0 * np.pi * _E0 * f)

    dc_b = debye_real(e0_b, tau_b)
    dc_u = debye_real(e0_u, tau_u)
    lf_b = debye_imag(e0_b, tau_b, sigma_b)
    lf_u = debye_imag(e0_u, tau_u, sigma_u)

    def n_of(dc: float, lf: float) -> float:
        return float(np.sqrt(np.sqrt(dc**2 + lf**2) + dc) / np.sqrt(2.0))

    def k_of(dc: float, lf: float) -> float:
        return float(np.sqrt(np.sqrt(dc**2 + lf**2) - dc) / np.sqrt(2.0))

    n_d = 1.634 - 0.539e-2 * c + 0.2748e-4 * c**2
    k_d = 0.03952 - 0.04038e-2 * c
    n_b, k_b = n_of(dc_b, lf_b), k_of(dc_b, lf_b)
    n_u, k_u = n_of(dc_u, lf_u), k_of(dc_u, lf_u)

    # Maximum bound-water fraction (volumetric).
    m_vt = 0.02863 + 0.30673e-2 * c

    # Refractive mixing (Mironov eqs. 12–13).
    below = mv <= m_vt
    n_m = np.where(
        below,
        n_d + (n_b - 1.0) * mv,
        n_d + (n_b - 1.0) * m_vt + (n_u - 1.0) * (mv - m_vt),
    )
    k_m = np.where(
        below,
        k_d + k_b * mv,
        k_d + k_b * m_vt + k_u * (mv - m_vt),
    )

    eps_real = n_m**2 - k_m**2
    eps_imag = 2.0 * n_m * k_m
    out = eps_real - 1j * eps_imag
    if np.ndim(theta_v) == 0:
        return np.asarray(out.item() if hasattr(out, "item") else complex(out))
    return out


def _round_list(xs: np.ndarray, nd: int = 12) -> list[float]:
    return [round(float(v), nd) for v in np.asarray(xs).ravel()]


def cross_check_topp_mironov(
    seed: int,
    n_theta: int = 8,
    n_clay: int = 6,
    freq_hz: float = 1.4e9,
) -> dict[str, Any]:
    """Seeded Topp vs Mironov disagreement over a synthetic moisture/clay grid.

    Same seed -> byte-identical JSON (sort_keys, fixed rounding). Synthetic only.

    Returns a JSON-serializable dict with theta_v [m3/m3], clay_pct [mass %],
    Topp eps', Mironov Re(eps), abs diffs, RMSE, max abs diff, and DOIs.
    """
    if n_theta < 1 or n_clay < 1:
        raise ValueError("n_theta and n_clay must be >= 1")
    rng = np.random.default_rng(int(seed))
    # Seeded synthetic sample points (sorted for stable mesh order).
    theta = np.sort(rng.uniform(0.02, 0.45, size=int(n_theta)))
    clay = np.sort(rng.uniform(5.0, 60.0, size=int(n_clay)))

    eps_topp = np.empty((n_theta, n_clay), dtype=float)
    eps_mir = np.empty((n_theta, n_clay), dtype=float)
    for i, th in enumerate(theta):
        eps_topp[i, :] = float(topp_dielectric(np.array([th]))[0])
        for j, cl in enumerate(clay):
            eps_mir[i, j] = float(np.real(mironov_dielectric(th, float(cl), freq_hz)))

    # Broadcast Topp (depends only on theta) across clay axis already filled.
    abs_diff = np.abs(eps_topp - eps_mir)
    rmse = float(np.sqrt(np.mean(abs_diff**2)))
    max_abs = float(np.max(abs_diff))

    report: dict[str, Any] = {
        "seed": int(seed),
        "freq_hz": float(freq_hz),
        "n_theta": int(n_theta),
        "n_clay": int(n_clay),
        "theta_v_m3m3": _round_list(theta),
        "clay_pct": _round_list(clay),
        "eps_topp": _round_list(eps_topp),
        "eps_mironov_real": _round_list(eps_mir),
        "abs_diff": _round_list(abs_diff),
        "rmse": round(rmse, 12),
        "max_abs_diff": round(max_abs, 12),
        "units": {
            "theta_v": "m3/m3",
            "clay_pct": "mass_percent",
            "eps": "relative_permittivity",
            "freq_hz": "Hz",
        },
        "citations": {
            "topp_1980": "10.1029/WR016i003p00574",
            "mironov_2009": "10.1109/TGRS.2008.2011631",
            "mironov_2009_correction": "10.1109/TGRS.2009.2023842",
        },
    }
    return report


def report_to_canonical_json(report: Mapping[str, Any]) -> str:
    """Canonical JSON bytes for deterministic comparisons."""
    return json.dumps(report, sort_keys=True, separators=(",", ":"))


def main(argv: list[str] | None = None) -> int:
    """CLI: python -m multi_proxy.dielectric --seed N [--write PATH]."""
    p = argparse.ArgumentParser(
        description=(
            "Topp (1980) / Mironov (2009) dielectric cross-check "
            "(synthetic seeded grid; Humus SenseCrew)."
        )
    )
    p.add_argument("--seed", type=int, default=20261104)
    p.add_argument("--n-theta", type=int, default=8)
    p.add_argument("--n-clay", type=int, default=6)
    p.add_argument("--freq-hz", type=float, default=1.4e9)
    p.add_argument(
        "--write",
        type=str,
        default="",
        help="Optional path to write canonical JSON report",
    )
    args = p.parse_args(argv)
    report = cross_check_topp_mironov(
        seed=args.seed,
        n_theta=args.n_theta,
        n_clay=args.n_clay,
        freq_hz=args.freq_hz,
    )
    text = report_to_canonical_json(report)
    # Pretty print for humans; canonical form used for --write / tests.
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.write:
        with open(args.write, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
