#!/usr/bin/env python3
"""
Analytic total-field magnetometry forward model (registry 520).

Buried magnetic dipole / induced sphere and thin dyke, with seeded Gaussian
noise. numpy (BSD-3) + stdlib only. No forensic_pipeline import.

Physics (Blakely, Potential Theory in Gravity and Magnetic Applications,
Cambridge, 1995, DOI 10.1017/CBO9780511549816):

  B(r) = (μ0/4π) [ 3(m·r̂)r̂ − m ] / r³

  Sphere (SI, demagnetization N=1/3):
    m = (4π R³ / μ0) · (κ/(3+κ)) · B0

  Total-field anomaly (first order): ΔT ≈ B̂0 · Banom

  Thin dyke (2-D, infinite strike; profile perpendicular to strike):
    classic even/odd forms with dip & magnetization direction
    (Blakely 1995 thin-sheet / thin-dyke ideal bodies).

Units: internal SI; outputs in nT. Axial check: m=1 A·m², z=10 m →
Bz = 0.2 nT (spec v0 mistyped 2.0 nT).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, Optional, Sequence

import numpy as np

MU0 = 4.0e-7 * math.pi
MU0_OVER_4PI = 1.0e-7
NT_PER_T = 1.0e9
T_ROUND = 6  # 0.001 nT → use 6 decimals for sub-pT margin on identity


def _unit_field(inc_deg: float, dec_deg: float) -> tuple[float, float, float]:
    """Ambient field unit vector in (north, east, down) ≈ (x, y, z) with z down."""
    inc = math.radians(inc_deg)
    dec = math.radians(dec_deg)
    bx = math.cos(inc) * math.cos(dec)
    by = math.cos(inc) * math.sin(dec)
    bz = math.sin(inc)
    return bx, by, bz


def dipole_B_nT(
    m_A_m2: tuple[float, float, float],
    r_m: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Magnetic field (nT) of a dipole at vector r from the source."""
    mx, my, mz = m_A_m2
    rx, ry, rz = r_m
    r2 = rx * rx + ry * ry + rz * rz
    if r2 <= 0.0:
        raise ValueError("observation coincides with dipole")
    r = math.sqrt(r2)
    r5 = r2 * r2 * r
    mdotr = mx * rx + my * ry + mz * rz
    bx = MU0_OVER_4PI * (3.0 * mdotr * rx - mx * r2) / r5
    by = MU0_OVER_4PI * (3.0 * mdotr * ry - my * r2) / r5
    bz = MU0_OVER_4PI * (3.0 * mdotr * rz - mz * r2) / r5
    return bx * NT_PER_T, by * NT_PER_T, bz * NT_PER_T


def total_field_anomaly_nT(
    Banom_nT: tuple[float, float, float],
    inc_deg: float,
    dec_deg: float,
) -> float:
    ux, uy, uz = _unit_field(inc_deg, dec_deg)
    return ux * Banom_nT[0] + uy * Banom_nT[1] + uz * Banom_nT[2]


def sphere_moment_A_m2(
    radius_m: float,
    kappa: float,
    B0_nT: float,
    inc_deg: float,
    dec_deg: float,
) -> tuple[float, float, float]:
    if radius_m <= 0:
        raise ValueError("radius must be > 0")
    B0_T = B0_nT / NT_PER_T
    ux, uy, uz = _unit_field(inc_deg, dec_deg)
    factor = (4.0 * math.pi * radius_m**3 / MU0) * (kappa / (3.0 + kappa)) * B0_T
    return factor * ux, factor * uy, factor * uz


def _parse_profile(spec: str | Sequence[float]) -> list[float]:
    if isinstance(spec, (list, tuple)):
        return [float(x) for x in spec]
    s = str(spec)
    if ":" in s:
        parts = s.split(":")
        if len(parts) != 3:
            raise ValueError(f"profile range must be start:stop:step, got {s!r}")
        start, stop, step = map(float, parts)
        if step == 0:
            raise ValueError("profile step must be non-zero")
        n = int(math.floor((stop - start) / step + 1e-12)) + 1
        return [round(start + i * step, 10) for i in range(n)]
    return [float(s)]


def thin_dyke_delta_T_nT(
    x_m: float,
    depth_m: float,
    dip_deg: float,
    thickness_m: float,
    susceptibility: float,
    B0_nT: float,
    inc_deg: float,
    dec_deg: float,
    strike_deg: float = 90.0,
) -> float:
    """2-D thin-dyke total-field anomaly on a profile perpendicular to strike.

    Uses the classic form (Blakely 1995 / Telford thin sheet):
      ΔT = 2 C t (d sinβ + x cosβ) / (x² + d²)
    with β = 2I − dip − 90° style effective angle reduced for vertical
    magnetization + vertical dyke to the even kernel d/(x²+d²).

    Profile x is measured from the epicentre, positive across strike.
    Strike is recorded for metadata; profile is assumed already strike-normal.
    """
    del strike_deg, dec_deg  # profile assumed strike-normal; dec absorbed in F
    if depth_m <= 0 or thickness_m <= 0:
        raise ValueError("depth and thickness must be > 0")
    # Effective magnetization amplitude (induced, SI thin-sheet factor)
    # J = κ H = κ B0/μ0 ; 2-D thin sheet constant C ~ (μ0/2) J in SI → nT via B0*κ
    # Amplitude chosen so vertical/vertical case is even and scales with κ B0 t.
    amp = susceptibility * B0_nT * thickness_m  # nT·m scale
    # Effective angle α = I − dip (degrees→rad). Vertical dyke + vertical
    # magnetization → α=0 → even kernel d/(x²+d²) (Blakely thin-sheet form).
    alpha = math.radians(inc_deg - dip_deg)
    d = depth_m
    num = d * math.cos(alpha) + x_m * math.sin(alpha)
    return 2.0 * amp * num / (x_m * x_m + d * d)


def dumps_canonical(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, allow_nan=False, sort_keys=True) + "\n"


def model(
    *,
    model_kind: str = "sphere",
    B0_nT: float = 50000.0,
    inc_deg: float = 65.0,
    dec_deg: float = 10.0,
    susceptibility: float = 0.1,
    m_A_m2: Optional[tuple[float, float, float]] = None,
    center_m: Optional[tuple[float, float, float]] = None,
    depth_m: Optional[float] = None,
    radius_m: float = 1.0,
    dyke_strike_deg: float = 90.0,
    dip_deg: float = 90.0,
    thickness_m: float = 2.0,
    profile_x_m: Optional[Sequence[float]] = None,
    noise_nT: float = 0.0,
    seed: int = 42,
) -> dict[str, Any]:
    if model_kind not in ("sphere", "dipole", "thin_dyke"):
        raise ValueError(f"unknown model_kind {model_kind!r}")
    profile = list(profile_x_m) if profile_x_m is not None else list(range(-20, 21))

    if depth_m is None and center_m is not None:
        depth_m = float(center_m[2])
    if center_m is None and depth_m is not None:
        center_m = (0.0, 0.0, float(depth_m))
    if center_m is None:
        center_m = (0.0, 0.0, 5.0)
        depth_m = 5.0

    bx_l: list[float] = []
    by_l: list[float] = []
    bz_l: list[float] = []
    dt_l: list[float] = []

    moment: Optional[tuple[float, float, float]] = None
    if model_kind == "sphere":
        moment = sphere_moment_A_m2(radius_m, susceptibility, B0_nT, inc_deg, dec_deg)
    elif model_kind == "dipole":
        if m_A_m2 is None:
            raise ValueError("dipole mode requires m_A_m2")
        moment = (float(m_A_m2[0]), float(m_A_m2[1]), float(m_A_m2[2]))

    for x in profile:
        if model_kind in ("sphere", "dipole"):
            assert moment is not None
            # Observation on surface z=0; source at center (z down positive)
            r_vec = (x - center_m[0], 0.0 - center_m[1], 0.0 - center_m[2])
            # Our dipole formula uses r from source to obs; z_obs-z_src = -depth
            Banom = dipole_B_nT(moment, r_vec)
            dT = total_field_anomaly_nT(Banom, inc_deg, dec_deg)
        else:
            dT = thin_dyke_delta_T_nT(
                x_m=float(x),
                depth_m=float(depth_m),
                dip_deg=dip_deg,
                thickness_m=thickness_m,
                susceptibility=susceptibility,
                B0_nT=B0_nT,
                inc_deg=inc_deg,
                dec_deg=dec_deg,
                strike_deg=dyke_strike_deg,
            )
            Banom = (0.0, 0.0, dT)  # vector optional; dyke gives ΔT directly
        bx_l.append(Banom[0])
        by_l.append(Banom[1])
        bz_l.append(Banom[2])
        dt_l.append(dT)

    if noise_nT and noise_nT != 0.0:
        rng = np.random.default_rng(seed)
        noise = rng.standard_normal(len(dt_l))
        dt_l = [d + noise_nT * float(e) for d, e in zip(dt_l, noise)]

    def rnd(vals: list[float]) -> list[float]:
        return [round(v, T_ROUND) for v in vals]

    return {
        "model": "Magnetometry total-field forward (dipole/sphere/thin_dyke)",
        "assumptions": [
            "SI units; outputs in nT",
            "first-order total-field anomaly ΔT ≈ B̂0 · Banom",
            "sphere demagnetization factor N=1/3 (induced only)",
            "thin dyke: 2-D infinite strike; profile strike-normal",
            "z positive down; surface observations at z=0",
        ],
        "constants": {"mu0": MU0, "mu0_over_4pi": MU0_OVER_4PI},
        "parameters": {
            "seed": int(seed),
            "model_kind": model_kind,
            "B0_nT": B0_nT,
            "inc_deg": inc_deg,
            "dec_deg": dec_deg,
            "susceptibility": susceptibility,
            "m_A_m2": list(moment) if moment is not None and model_kind == "dipole" else (
                list(moment) if model_kind == "sphere" else None
            ),
            "center_m": list(center_m),
            "depth_m": float(depth_m) if depth_m is not None else None,
            "radius_m": radius_m if model_kind == "sphere" else None,
            "dyke_strike_deg": dyke_strike_deg if model_kind == "thin_dyke" else None,
            "dip_deg": dip_deg if model_kind == "thin_dyke" else None,
            "thickness_m": thickness_m if model_kind == "thin_dyke" else None,
            "profile_x_m": profile,
            "noise_nT": float(noise_nT),
        },
        "results": {
            "delta_T_nT": rnd(dt_l),
            "Bx_nT": rnd(bx_l),
            "By_nT": rnd(by_l),
            "Bz_nT": rnd(bz_l),
        },
    }


def print_summary(data: dict[str, Any]) -> None:
    p = data["parameters"]
    print(f"\nMagnetometry | kind={p['model_kind']} | B0={p['B0_nT']} nT | seed={p['seed']}\n")
    print(f"{'x_m':>10} {'dT_nT':>14}")
    print("-" * 26)
    for x, dT in zip(p["profile_x_m"], data["results"]["delta_T_nT"]):
        print(f"{x:10.3f} {dT:14.6f}")
    print()


def main(argv: Optional[Sequence[str]] = None) -> dict[str, Any]:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind", dest="model_kind", choices=["sphere", "dipole", "thin_dyke"], default="sphere")
    ap.add_argument("--B0", dest="B0_nT", type=float, default=50000.0)
    ap.add_argument("--inc", dest="inc_deg", type=float, default=65.0)
    ap.add_argument("--dec", dest="dec_deg", type=float, default=10.0)
    ap.add_argument("--kappa", dest="susceptibility", type=float, default=0.1)
    ap.add_argument("--m", dest="m_A_m2", type=float, nargs=3, default=None)
    ap.add_argument("--center", type=float, nargs=3, default=None)
    ap.add_argument("--depth", type=float, default=None)
    ap.add_argument("--radius", type=float, default=1.0)
    ap.add_argument("--dyke-strike", type=float, default=90.0)
    ap.add_argument("--dip", type=float, default=90.0)
    ap.add_argument("--thickness", type=float, default=2.0)
    ap.add_argument(
        "--profile",
        default=["-20:20:1"],
        nargs="+",
        help="start:stop:step (prefer --profile=-20:20:0.5) or explicit x list",
    )
    ap.add_argument("--noise-nT", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out")
    ap.add_argument("--no-table", action="store_true")
    args = ap.parse_args(argv)

    if len(args.profile) == 1 and ":" in args.profile[0]:
        profile = _parse_profile(args.profile[0])
    else:
        profile = [float(x) for x in args.profile]

    try:
        data = model(
            model_kind=args.model_kind,
            B0_nT=args.B0_nT,
            inc_deg=args.inc_deg,
            dec_deg=args.dec_deg,
            susceptibility=args.susceptibility,
            m_A_m2=tuple(args.m_A_m2) if args.m_A_m2 else None,
            center_m=tuple(args.center) if args.center else None,
            depth_m=args.depth,
            radius_m=args.radius,
            dyke_strike_deg=args.dyke_strike,
            dip_deg=args.dip,
            thickness_m=args.thickness,
            profile_x_m=profile,
            noise_nT=args.noise_nT,
            seed=args.seed,
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
