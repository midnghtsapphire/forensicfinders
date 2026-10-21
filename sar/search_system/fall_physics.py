#!/usr/bin/env python3
# PROPRIETARY - ALL RIGHTS RESERVED. (c) 2026 Audrey Evans / Walter-Evans Forensic Intelligence Systems.
# No license is granted. Pre-patent-filing; keep the repository private. See LICENSE and docs/PATENT_PREP.md.
# STATUS: PROTOTYPE. All numbers this module prints in demos are SYNTHETIC; see search_system/README.md "Audit".
"""
fall_physics.py - formalized fall/slide trajectory reconstruction.

Purpose: convert two years of notebook reconstructions into a reproducible,
uncertainty-quantified module. Two modes:
  1. FORWARD: last-seen point + launch assumptions -> landing probability
     raster -> plugs into the fusion as a physics prior layer.
  2. BACK-CAST (validation): given a KNOWN recovery point (resolved case),
     report the recovery percentile inside the predicted distribution - the
     honest "confirmation" statistic for families and agencies.

Physics: 2D ballistic flight with quadratic drag, ray-marched against the
DEM (flat-earth approximations fail on steep terrain), then post-impact
slide along steepest descent with Coulomb friction until rest or shaft
entry. Direction and speed uncertainty are marginalized, not ignored.

TUNABLES (literature ballparks - cite your own case measurements where you
have them): Cd~0.8, A~0.7 m^2 for a tumbling human; mu_slide 0.4-0.7 body on
leaf litter/rock. PROTOTYPE: these ballparks carry NO citation in the source; the code default
mu_slide=0.30 is below that stated range. Supply sourced or measured values. The module's value is reproducibility + sensitivity, not
false precision.
"""
import numpy as np, pandas as pd

G = 9.81

def _ground_z(dem, res, x, y):
    """Bilinear DEM height at continuous (x, y) in meters from array origin."""
    r, c = y / res, x / res
    r0, c0 = int(np.floor(r)), int(np.floor(c))
    fr, fc = r - r0, c - c0
    if r0 < 0 or c0 < 0 or r0 + 1 >= dem.shape[0] or c0 + 1 >= dem.shape[1]:
        return np.nan
    return (dem[r0, c0] * (1-fr) * (1-fc) + dem[r0+1, c0] * fr * (1-fc) +
            dem[r0, c0+1] * (1-fr) * fc + dem[r0+1, c0+1] * fr * fc)

def _slope_rad(dem, res, r, c):
    gy, gx = np.gradient(dem, res)
    return np.arctan(np.hypot(gy[r, c], gx[r, c]))

def _slide_to_rest(dem, res, x, y, vx, vy, mu=0.30, max_steps=2000):
    """Follow steepest descent with kinetic friction from impact point."""
    from scipy.ndimage import map_coordinates
    gy, gx = np.gradient(dem, res)
    v = np.hypot(vx, vy)
    for _ in range(max_steps):
        r, c = int(round(y / res)), int(round(x / res))
        if not (0 < r < dem.shape[0]-1 and 0 < c < dem.shape[1]-1): break
        gxn, gyn = gx[r, c], gy[r, c]
        mag = np.hypot(gxn, gyn)
        if mag < 1e-9: break
        dxn, dyn = -gxn / mag, -gyn / mag           # downhill unit vector
        slope = np.arctan(mag)
        v = np.sqrt(max(v**2 + 2*G*res*np.sin(slope) - 2*mu*G*res*np.cos(slope), 0.0))
        if v <= 0.05: break
        x, y = x + dxn * res, y + dyn * res
    return x, y

def trajectory_landing_distribution(dem, res, launch_xy, v0_mph,
                                    direction_deg=None, dir_sigma_deg=30.0,
                                    v0_sigma_mph=2.0, mu_slide=0.30,
                                    cd=0.8, area=0.7, mass=75.0, rho=1.2,
                                    shaft_mask=None, n_dir=36, dt=0.02,
                                    smooth_sigma_m=6.0, n_mc=400, seed=7):
    """Monte-Carlo over (direction, speed) -> landing mass raster.
    direction_deg=None marginalizes over a wrapped-Gaussian direction prior."""
    from scipy.ndimage import gaussian_filter
    rng = np.random.default_rng(seed)
    landing = np.zeros_like(dem, dtype=float)        # accumulator raster (was 'mass':
                                                     # name collision with body mass!)
    for _ in range(n_mc):
        if direction_deg is None:
            th = rng.uniform(0, 2 * np.pi)
        else:
            th = np.radians(direction_deg) + rng.normal(0, np.radians(dir_sigma_deg))
        v0 = max(0.0, (v0_mph + rng.normal(0, v0_sigma_mph)) * 0.44704)  # mph -> m/s
        x, y = float(launch_xy[0]), float(launch_xy[1])
        z = _ground_z(dem, res, x, y)
        if not np.isfinite(z): continue
        vx, vy = v0 * np.cos(th), v0 * np.sin(th)   # horizontal flight components
        vz = 0.0
        k = 0.5 * rho * cd * area / mass            # quadratic-drag coeff (body mass)
        hit = None
        for _s in range(4000):                       # ballistic ray-march, full 2D
            speed = np.hypot(np.hypot(vx, vy), vz)
            vx -= k * vx * speed * dt
            vy -= k * vy * speed * dt
            vz -= (G + k * vz * speed) * dt          # falling: drag slows descent
            x += vx * dt; y += vy * dt; z += vz * dt
            gz = _ground_z(dem, res, x, y)
            if not np.isfinite(gz): break
            if z <= gz:
                hit = (x, y, gz, np.hypot(vx, vy)); break
        if hit is None: continue
        hx, hy, hz, vh_impact = hit
        r, c = int(round(hy / res)), int(round(hx / res))
        if 0 <= r < dem.shape[0] and 0 <= c < dem.shape[1]:
            if shaft_mask is not None and shaft_mask[r, c]:   # fell into opening
                landing[r, c] += 1.0; continue
            fx, fy = _slide_to_rest(dem, res, hx, hy, vh_impact, 0.0, mu=mu_slide)
            rr, cc = int(round(fy / res)), int(round(fx / res))
            if 0 <= rr < landing.shape[0] and 0 <= cc < landing.shape[1]:
                landing[rr, cc] += 1.0
    landing = gaussian_filter(landing, sigma=max(0.5, smooth_sigma_m / res))
    p = landing / (landing.sum() + 1e-12)
    return p

def ellipse_stats(p, res):
    """95% ellipse of the landing distribution (2-sigma moment ellipse)."""
    ys, xs = np.where(p > 0)
    if len(xs) == 0: return None
    w = p[ys, xs]; w /= w.sum()
    cx, cy = (xs * w).sum() * res, (ys * w).sum() * res
    cov = np.cov(np.vstack([xs * res, ys * res]), aweights=w)
    eig, vec = np.linalg.eigh(cov)
    axes = 2 * np.sqrt(np.maximum(eig, 0))          # ~2-sigma
    orient = np.degrees(np.arctan2(vec[1, 1], vec[0, 1]))
    return {"centroid_m": (round(float(cx), 1), round(float(cy), 1)),
            "ellipse_axes_m": (round(float(axes[1]), 1), round(float(axes[0]), 1)),
            "orientation_deg": round(float(orient), 1)}

def recovery_percentile(p, recovery_xy, res):
    """Where the known recovery point sits in the predicted distribution
    (percentile of its cell's probability). ~50 = typical; >90 = strongly
    consistent; <10 = the reconstruction needs re-examination."""
    r, c = int(round(recovery_xy[1] / res)), int(round(recovery_xy[0] / res))
    if not (0 <= r < p.shape[0] and 0 <= c < p.shape[1]): return None
    vals = np.sort(p[p > 0].ravel())
    return round(float((vals <= p[r, c]).mean() * 100), 1)

def sensitivity(dem, res, launch_xy, base_kw):
    """Tornado: which assumption moves the answer most?"""
    rows = []
    base_c = ellipse_stats(trajectory_landing_distribution(dem, res, launch_xy, **base_kw), res)["centroid_m"]
    for param, deltas in [("v0_mph", [-4, 4]), ("mu_slide", [-0.2, 0.2]),
                          ("dir_sigma_deg", [-30, 30]), ("smooth_sigma_m", [-4, 4])]:
        for d in deltas:
            kw = dict(base_kw); kw[param] = kw.get(param, {"v0_mph": 8, "mu_slide": 0.30,
                                  "dir_sigma_deg": 30, "smooth_sigma_m": 6.0}[param]) + d
            if kw[param] < 0: continue
            c = ellipse_stats(trajectory_landing_distribution(dem, res, launch_xy, **kw), res)["centroid_m"]
            rows.append({"param": param, "delta": d,
                         "centroid_shift_m": round(float(np.hypot(c[0]-base_c[0], c[1]-base_c[1])), 1)})
    return pd.DataFrame(rows)

if __name__ == "__main__":
    # Demo: SYNTHETIC steep ridge (generic terrain; no real location)
    yy, xx = np.mgrid[0:300, 0:300]
    dem = 0.55 * yy - 0.04 * xx + 6 * np.sin(xx / 40.0)          # ~29 deg synthetic ridge
    launch = (150.0, 40.0)
    kw = {"v0_mph": 8.0, "mu_slide": 0.30, "smooth_sigma_m": 6.0}
    p = trajectory_landing_distribution(dem, 1.0, launch, **kw)
    stats = ellipse_stats(p, 1.0)
    print("landing distribution:", stats)
    recovery = (152.0, 88.0)                                     # planted ~down-slope
    print("recovery percentile at known point:", recovery_percentile(p, recovery, 1.0), "(planted ~down-slope)")
    print("\nsensitivity (centroid shift):")
    print(sensitivity(dem, 1.0, launch, kw).to_string(index=False))
