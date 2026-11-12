#!/usr/bin/env python3
"""
Analytic / semi-analytic DC resistivity forward model (registry 510).

Wenner and dipole–dipole arrays over a 1-D layered half-space or a buried
resistive/conductive sphere (air void). Stdlib + numpy only.

Physics (Telford, Geldart & Sheriff, Applied Geophysics, 2nd ed., 1990, ch. 8):
  K_W  = 2 π a
  K_DD = π n (n+1)(n+2) a
  ρ_a  = K ΔV / I

Two-layer Wenner image series (Telford et al. 1990; common textbook form):
  k = (ρ2 - ρ1) / (ρ2 + ρ1)
  ρ_a/ρ1 = 1 + 4 Σ_{n=1}^N k^n [ 1/√(1+(2n h/a)²) − 1/√(4+(2n h/a)²) ]

Buried sphere (leading dipole term; insulating limit β → −1/2):
  β = (σ_s − σ_h) / (σ_s + 2 σ_h)   with σ = 1/ρ
  Secondary surface potential from the induced dipole in the primary field
  of each current electrode (half-space primary V = ρ I / (2 π r)).

Seeding: noise_pct=0 is RNG-free; else numpy.random.default_rng(seed).
Canonical JSON: sort_keys=True, fixed decimal rounding → byte-identical.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, Optional, Sequence

import numpy as np

TWO_LAYER_IMAGE_TERMS = 80
RHO_ROUND = 6
K_ROUND = 9
V_ROUND = 12


def wenner_geometric_factor(a_m: float) -> float:
    if a_m <= 0:
        raise ValueError(f"a_m must be > 0, got {a_m}")
    return 2.0 * math.pi * a_m


def dipole_dipole_geometric_factor(a_m: float, n: int) -> float:
    if a_m <= 0:
        raise ValueError(f"a_m must be > 0, got {a_m}")
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    return math.pi * n * (n + 1) * (n + 2) * a_m


def geometric_factor(array: str, a_m: float, n: int = 1) -> float:
    if array == "wenner":
        return wenner_geometric_factor(a_m)
    if array == "dipole-dipole":
        return dipole_dipole_geometric_factor(a_m, n)
    raise ValueError(f"unknown array {array!r}")


def _two_layer_wenner_rho_a(rho1: float, rho2: float, h: float, a: float) -> float:
    """Wenner apparent resistivity for a two-layer earth (image series)."""
    if a <= 0 or h < 0:
        raise ValueError("a must be > 0 and h >= 0")
    if rho1 <= 0 or rho2 <= 0:
        raise ValueError("resistivities must be > 0")
    k = (rho2 - rho1) / (rho2 + rho1)
    s = 0.0
    for n in range(1, TWO_LAYER_IMAGE_TERMS + 1):
        kn = k**n
        term1 = 1.0 / math.sqrt(1.0 + (2.0 * n * h / a) ** 2)
        term2 = 1.0 / math.sqrt(4.0 + (2.0 * n * h / a) ** 2)
        s += kn * (term1 - term2)
    return rho1 * (1.0 + 4.0 * s)


def _layered_rho_a_wenner(rho_layers: Sequence[float], thickness: Sequence[float], a: float) -> float:
    if len(rho_layers) == 1:
        return float(rho_layers[0])
    if len(rho_layers) == 2 and len(thickness) == 1:
        return _two_layer_wenner_rho_a(rho_layers[0], rho_layers[1], thickness[0], a)
    raise ValueError("only homogeneous or two-layer earth supported in v0")


def _layered_rho_a(
    array: str,
    a_m: float,
    n: int,
    rho_layers: Sequence[float],
    thickness: Sequence[float],
) -> float:
    # Homogeneous: ρa = ρ for any array.
    if len(rho_layers) == 1:
        return float(rho_layers[0])
    if array == "wenner":
        return _layered_rho_a_wenner(rho_layers, thickness, a_m)
    # Dipole–dipole two-layer: evaluate via four electrode potentials on a
    # horizontally layered earth approximated by Wenner-equivalent spacing
    # scaling is not exact; use image series on each pair distance via the
    # Stefanescu kernel reduced to two-layer point-potential form.
    if len(rho_layers) == 2 and len(thickness) == 1:
        return _two_layer_dipole_dipole_rho_a(rho_layers[0], rho_layers[1], thickness[0], a_m, n)
    raise ValueError("only homogeneous or two-layer earth supported in v0")


def _two_layer_point_potential_factor(rho1: float, rho2: float, h: float, r: float) -> float:
    """V / (I) factor such that V = factor * I for a surface point source.

    Homogeneous: factor = rho1 / (2 π r).
    Two-layer image series (Telford): 
      V = (ρ1 I)/(2π) [ 1/r + 2 Σ k^n / √(r² + (2 n h)²) ]
    """
    if r <= 0:
        raise ValueError("horizontal offset r must be > 0")
    k = (rho2 - rho1) / (rho2 + rho1)
    s = 1.0 / r
    for n in range(1, TWO_LAYER_IMAGE_TERMS + 1):
        s += 2.0 * (k**n) / math.sqrt(r * r + (2.0 * n * h) ** 2)
    return rho1 / (2.0 * math.pi) * s


def _two_layer_dipole_dipole_rho_a(rho1: float, rho2: float, h: float, a: float, n: int) -> float:
    # Electrodes: A at 0, B at a, M at a*(1+n), N at a*(2+n)  (standard DD)
    # Actually common: A--a--B ---- n*a ---- M--a--N
    pos = {
        "A": 0.0,
        "B": a,
        "M": a + n * a,
        "N": a + n * a + a,
    }
    I = 1.0

    def V_at(x: float, src: float, sign: float) -> float:
        r = abs(x - src)
        return sign * _two_layer_point_potential_factor(rho1, rho2, h, r) * I

    v_m = V_at(pos["M"], pos["A"], +1.0) + V_at(pos["M"], pos["B"], -1.0)
    v_n = V_at(pos["N"], pos["A"], +1.0) + V_at(pos["N"], pos["B"], -1.0)
    dV = v_m - v_n
    K = dipole_dipole_geometric_factor(a, n)
    return K * dV / I


def _sphere_beta(rho_s: float, rho_h: float) -> float:
    """Conductivity contrast factor β = (σs − σh)/(σs + 2 σh)."""
    sig_s = 1.0 / rho_s
    sig_h = 1.0 / rho_h
    return (sig_s - sig_h) / (sig_s + 2.0 * sig_h)


def _potential_halfspace(rho: float, I: float, r: float) -> float:
    if r <= 0:
        # Coincident electrode — not physical for distinct A/M/N/B
        return 0.0
    return rho * I / (2.0 * math.pi * r)


def _sphere_secondary_potential(
    I: float,
    rho_h: float,
    beta: float,
    R: float,
    center: tuple[float, float, float],
    src_xy: tuple[float, float],
    obs_xy: tuple[float, float],
) -> float:
    """Leading dipole secondary potential at surface obs from current at src.

    Primary field at the sphere centre from a surface point source on a
    homogeneous half-space is approximated with the half-space green function
    gradient; the induced dipole moment is p = β R³ E_primary, and the
    surface secondary uses the image-augmented dipole field (factor 2 on the
    vertical-moment contribution via the free-surface image for potential).
    """
    cx, cy, cz = center
    if cz <= R:
        raise ValueError("sphere must not breach the surface (z > R)")
    # Vector from source to centre
    sx, sy = src_xy
    rx, ry, rz = cx - sx, cy - sy, cz
    r = math.sqrt(rx * rx + ry * ry + rz * rz)
    if r < R * 1.001:
        return 0.0
    # E = -grad V, V = ρ I / (2π R_full); |E| primary at centre
    # grad(1/r) = -r_hat/r² → E = (ρ I / 2π) * r_vec / r³
    e_scale = (rho_h * I / (2.0 * math.pi)) / (r**3)
    Ex, Ey, Ez = e_scale * rx, e_scale * ry, e_scale * rz
    # dipole moment m = β R³ E  (potential dipole convention matching β)
    mx = beta * (R**3) * Ex
    my = beta * (R**3) * Ey
    mz = beta * (R**3) * Ez
    # Potential of dipole at surface observation (and its image for z=0 plane)
    ox, oy = obs_xy
    dx, dy, dz = ox - cx, oy - cy, 0.0 - cz
    ro = math.sqrt(dx * dx + dy * dy + dz * dz)
    if ro < 1e-12:
        return 0.0
    # V_dip = (m · r_hat) / r² = (m · r) / r³
    v = (mx * dx + my * dy + mz * dz) / (ro**3)
    # Image dipole (mz flips) at z=+cz contributing at surface
    dz_i = 0.0 - (-cz)
    ri = math.sqrt(dx * dx + dy * dy + dz_i * dz_i)
    v_img = (mx * dx + my * dy + (-mz) * dz_i) / (ri**3)
    return v + v_img


def _electrode_offsets_wenner(a: float, mid_x: float) -> dict[str, tuple[float, float]]:
    # A--a--M--a--N--a--B, midpoint between M and N
    return {
        "A": (mid_x - 1.5 * a, 0.0),
        "M": (mid_x - 0.5 * a, 0.0),
        "N": (mid_x + 0.5 * a, 0.0),
        "B": (mid_x + 1.5 * a, 0.0),
    }


def _electrode_offsets_dd(a: float, n: int, mid_x: float) -> dict[str, tuple[float, float]]:
    # A--a--B ---- n a ---- M--a--N; midpoint between B and M span centre
    # Centre of array at mid_x: total length a + n*a + a = a(n+2)
    half = 0.5 * a * (n + 2)
    A = mid_x - half
    return {
        "A": (A, 0.0),
        "B": (A + a, 0.0),
        "M": (A + a + n * a, 0.0),
        "N": (A + a + n * a + a, 0.0),
    }


def _sphere_rho_a(
    array: str,
    a_m: float,
    n: int,
    host_rho: float,
    sphere_center: tuple[float, float, float],
    sphere_radius: float,
    sphere_rho: float,
    mid_x: float,
) -> tuple[float, float, float]:
    """Return (ρa, K, ΔV) for unit current."""
    K = geometric_factor(array, a_m, n)
    els = (
        _electrode_offsets_wenner(a_m, mid_x)
        if array == "wenner"
        else _electrode_offsets_dd(a_m, n, mid_x)
    )
    beta = _sphere_beta(sphere_rho, host_rho)
    I = 1.0

    def V(obs: tuple[float, float]) -> float:
        vp = 0.0
        for src_name, sign in (("A", +1.0), ("B", -1.0)):
            src = els[src_name]
            r = math.hypot(obs[0] - src[0], obs[1] - src[1])
            vp += sign * _potential_halfspace(host_rho, I, r)
            vp += _sphere_secondary_potential(
                sign * I, host_rho, beta, sphere_radius, sphere_center, src, obs
            )
        return vp

    dV = V(els["M"]) - V(els["N"])
    return K * dV / I, K, dV


def dumps_canonical(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, allow_nan=False, sort_keys=True) + "\n"


def model(
    *,
    array: str = "wenner",
    a_m: float = 2.0,
    n: int = 1,
    rho_layers_ohm_m: Optional[Sequence[float]] = None,
    thickness_m: Optional[Sequence[float]] = None,
    host_rho_ohm_m: Optional[float] = None,
    sphere_center_m: Optional[tuple[float, float, float]] = None,
    sphere_radius_m: Optional[float] = None,
    sphere_rho_ohm_m: Optional[float] = None,
    profile_x_m: Optional[Sequence[float]] = None,
    seed: int = 42,
    noise_pct: float = 0.0,
) -> dict[str, Any]:
    if array not in ("wenner", "dipole-dipole"):
        raise ValueError(f"array must be wenner|dipole-dipole, got {array!r}")
    profile = list(profile_x_m) if profile_x_m is not None else [0.0]
    thickness = list(thickness_m) if thickness_m is not None else []
    use_sphere = sphere_center_m is not None
    rhos: list[float] = []
    Ks: list[float] = []
    dVs: list[float] = []

    if use_sphere:
        if host_rho_ohm_m is None or sphere_radius_m is None or sphere_rho_ohm_m is None:
            raise ValueError("sphere mode requires host_rho, sphere_radius, sphere_rho")
        for x in profile:
            rho_a, K, dV = _sphere_rho_a(
                array,
                a_m,
                n,
                float(host_rho_ohm_m),
                (float(sphere_center_m[0]), float(sphere_center_m[1]), float(sphere_center_m[2])),
                float(sphere_radius_m),
                float(sphere_rho_ohm_m),
                float(x),
            )
            rhos.append(rho_a)
            Ks.append(K)
            dVs.append(dV)
        layers_param: Any = None
        thickness_param: Any = None
        host_param = float(host_rho_ohm_m)
    else:
        layers = list(rho_layers_ohm_m) if rho_layers_ohm_m is not None else [100.0]
        K = geometric_factor(array, a_m, n)
        for _x in profile:
            rho_a = _layered_rho_a(array, a_m, n, layers, thickness)
            # Homogeneous/layered 1-D: ΔV = ρa / K for I=1
            dV = rho_a / K if K != 0 else 0.0
            rhos.append(rho_a)
            Ks.append(K)
            dVs.append(dV)
        layers_param = layers
        thickness_param = thickness
        host_param = None

    if noise_pct and noise_pct != 0.0:
        rng = np.random.default_rng(seed)
        noise = rng.standard_normal(len(rhos))
        rhos = [r * (1.0 + 0.01 * noise_pct * float(eps)) for r, eps in zip(rhos, noise)]

    rhos_r = [round(r, RHO_ROUND) for r in rhos]
    Ks_r = [round(k, K_ROUND) for k in Ks]
    dVs_r = [round(v, V_ROUND) for v in dVs]

    return {
        "model": "ERT DC resistivity forward (Wenner / dipole-dipole)",
        "assumptions": [
            "steady current ∇·(σ∇V)=0",
            "half-space free surface",
            "two-layer image series truncated at N=%d" % TWO_LAYER_IMAGE_TERMS,
            "buried sphere: leading induced-dipole term with free-surface image",
            "air void ≈ large sentinel resistivity",
        ],
        "constants": {
            "two_layer_image_terms": TWO_LAYER_IMAGE_TERMS,
        },
        "parameters": {
            "seed": int(seed),
            "array": array,
            "a_m": a_m,
            "n": n if array == "dipole-dipole" else None,
            "rho_layers_ohm_m": layers_param,
            "thickness_m": thickness_param,
            "host_rho_ohm_m": host_param,
            "sphere_center_m": list(sphere_center_m) if use_sphere else None,
            "sphere_radius_m": float(sphere_radius_m) if use_sphere else None,
            "sphere_rho_ohm_m": float(sphere_rho_ohm_m) if use_sphere else None,
            "profile_x_m": profile,
            "noise_pct": float(noise_pct),
        },
        "results": {
            "apparent_resistivity_ohm_m": rhos_r,
            "geometric_factor_m": Ks_r,
            "potential_diff_V": dVs_r,
        },
    }


def print_summary(data: dict[str, Any]) -> None:
    p = data["parameters"]
    print(f"\nERT model | array={p['array']} a={p['a_m']} m | seed={p['seed']} | noise={p['noise_pct']}%\n")
    print(f"{'x_m':>10} {'rho_a':>14} {'K':>14} {'dV':>14}")
    print("-" * 56)
    xs = p["profile_x_m"]
    r = data["results"]
    for i, x in enumerate(xs):
        print(f"{x:10.3f} {r['apparent_resistivity_ohm_m'][i]:14.6f} {r['geometric_factor_m'][i]:14.6f} {r['potential_diff_V'][i]:14.6e}")
    print()


def main(argv: Optional[Sequence[str]] = None) -> dict[str, Any]:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--array", choices=["wenner", "dipole-dipole"], default="wenner")
    ap.add_argument("--a", dest="a_m", type=float, default=2.0, help="electrode spacing a (m)")
    ap.add_argument("--n", type=int, default=1, help="dipole-dipole level n")
    ap.add_argument("--rho-layers", type=float, nargs="+", default=None)
    ap.add_argument("--thickness", type=float, nargs="*", default=None)
    ap.add_argument("--host-rho", type=float, default=None)
    ap.add_argument("--sphere-center", type=float, nargs=3, default=None)
    ap.add_argument("--sphere-radius", type=float, default=None)
    ap.add_argument("--sphere-rho", type=float, default=None)
    ap.add_argument("--profile", type=float, nargs="+", default=[0.0])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--noise-pct", type=float, default=0.0)
    ap.add_argument("--out", help="write JSON to this file")
    ap.add_argument("--no-table", action="store_true")
    args = ap.parse_args(argv)

    try:
        data = model(
            array=args.array,
            a_m=args.a_m,
            n=args.n,
            rho_layers_ohm_m=args.rho_layers,
            thickness_m=args.thickness if args.thickness is not None else [],
            host_rho_ohm_m=args.host_rho,
            sphere_center_m=tuple(args.sphere_center) if args.sphere_center else None,
            sphere_radius_m=args.sphere_radius,
            sphere_rho_ohm_m=args.sphere_rho,
            profile_x_m=args.profile,
            seed=args.seed,
            noise_pct=args.noise_pct,
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
