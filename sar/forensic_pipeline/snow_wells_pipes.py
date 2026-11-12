"""
Pure-function residuals for snow wells, culvert-ice, pipes, image accent,
synthetic search-scenario priors. Array-in/array-out.

Renames (Verity-N APPROVE on rule-7 / Deepscan follow-up):
  isrid_prior_map -> synthetic_prior_map
  finder_confirmation -> confirmation_event
Old names remain as deprecated aliases emitting DeprecationWarning.
"""
import warnings
import numpy as np
from scipy.ndimage import uniform_filter

def tree_well_residual(canopy_height, snow_depth, tree_mask=None):
    if tree_mask is None:
        tree_mask = canopy_height > np.percentile(canopy_height, 70)
    local_mean = uniform_filter(snow_depth.astype(float), size=11)
    void = np.maximum(0, local_mean - snow_depth) * tree_mask.astype(float)
    return {"residual": void, "mask": tree_mask.astype(bool)}

def rootball_trench_residual(dem, tree_mask, trench_mask=None):
    if trench_mask is None:
        trench_mask = np.zeros_like(dem, dtype=bool)
    highpass = dem - uniform_filter(dem, size=21)
    score = np.abs(highpass) * (tree_mask | trench_mask)
    return {"residual": score}

def culvert_ice_trajectory(vel_culvert, vel_river, ice_cover, fighting=0):
    ratio = vel_culvert / (vel_river + 1e-6)
    held = 1.0 / (1.0 + np.exp(-(0.5 - ratio + fighting * 0.3)))
    exit_speed = vel_river * (1 - ice_cover * 0.4)
    return {"exit_speed": float(exit_speed), "held_probability": float(held)}

def pipe_airflow_residual(diameter, velocity, air_temp, water_temp, inversion=0):
    buoyancy = max(0, water_temp - air_temp) / 10.0
    dilution = velocity * diameter * (1 + inversion * 2)
    strength = buoyancy / (dilution + 1e-6)
    return {"odor_strength": float(strength), "dog_detectable": bool(strength > 0.05)}

def local_image_accent(image, mask, mode="blowout"):
    out = image.copy()
    if mode == "blowout":
        region = out[mask]
        if region.size:
            p2, p98 = np.percentile(region, (2, 98))
            out[mask] = np.clip((region - p2) / (p98 - p2 + 1e-6) * 255, 0, 255)
    elif mode == "invert":
        out[mask] = 255 - out[mask]
    return out

def synthetic_prior_map(shape, last_seen_xy, category_radius=500):
    y, x = np.ogrid[:shape[0], :shape[1]]
    dist = np.sqrt((y - last_seen_xy[0])**2 + (x - last_seen_xy[1])**2)
    prior = np.exp(-dist / category_radius)
    return prior

def confirmation_event(candidate_mask, heartbeat_detected=False):
    return candidate_mask & heartbeat_detected

def isrid_prior_map(shape, last_seen_xy, category_radius=500):
    warnings.warn(
        "isrid_prior_map is deprecated; use synthetic_prior_map",
        DeprecationWarning,
        stacklevel=2,
    )
    return synthetic_prior_map(shape, last_seen_xy, category_radius=category_radius)

def finder_confirmation(candidate_mask, heartbeat_detected=False):
    warnings.warn(
        "finder_confirmation is deprecated; use confirmation_event",
        DeprecationWarning,
        stacklevel=2,
    )
    return confirmation_event(candidate_mask, heartbeat_detected=heartbeat_detected)
