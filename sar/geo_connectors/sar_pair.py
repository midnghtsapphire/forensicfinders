"""Pairwise SAR GeoTIFF change cues (amplitude ratio + optional coherent change).

Registry ID: 980. Crawl stub for VHR SAR change add-on (see docs/research/vhr-radar-lidar-fusion.md).
Works on arrays or single-band GeoTIFF paths. All demo data is synthetic.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np

PathLike = Union[str, Path]


def amplitude_ratio_db(
    before: np.ndarray,
    after: np.ndarray,
    eps: float = 1e-6,
) -> np.ndarray:
    """10·log10(after/before) in dB. Inputs are linear amplitude or power (same units)."""
    b = np.asarray(before, dtype="float64")
    a = np.asarray(after, dtype="float64")
    if b.shape != a.shape:
        raise ValueError(f"shape mismatch {b.shape} vs {a.shape}")
    return 10.0 * np.log10((a + eps) / (b + eps))


def coherent_change_index(
    z0: np.ndarray,
    z1: np.ndarray,
    window: int = 5,
    eps: float = 1e-12,
) -> np.ndarray:
    """Local complex coherence magnitude in (0, 1]; lower ⇒ more change.

    z0, z1 are complex arrays (SLC-like). Uses a square boxcar of odd size.
    """
    if window < 1 or window % 2 == 0:
        raise ValueError("window must be odd and >= 1")
    a = np.asarray(z0, dtype="complex128")
    b = np.asarray(z1, dtype="complex128")
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch {a.shape} vs {b.shape}")
    pad = window // 2
    ap = np.pad(a, pad, mode="edge")
    bp = np.pad(b, pad, mode="edge")
    out = np.empty(a.shape, dtype="float64")
    for i in range(a.shape[0]):
        for j in range(a.shape[1]):
            u = ap[i : i + window, j : j + window].ravel()
            v = bp[i : i + window, j : j + window].ravel()
            num = np.abs(np.vdot(u, v))
            den = math.sqrt(float(np.vdot(u, u).real) * float(np.vdot(v, v).real) + eps)
            out[i, j] = num / den
    return out


def _read_band(path: PathLike) -> tuple[np.ndarray, dict[str, Any]]:
    import rasterio

    with rasterio.open(path) as ds:
        arr = ds.read(1)
        meta = {
            "transform": ds.transform,
            "crs": ds.crs,
            "width": ds.width,
            "height": ds.height,
            "nodata": ds.nodata,
        }
        return arr, meta


def pair_amplitude_ratio_geotiff(
    before_path: PathLike,
    after_path: PathLike,
    out_path: PathLike,
    eps: float = 1e-6,
) -> dict[str, Any]:
    """Write float32 GeoTIFF of amplitude_ratio_db; requires matching shape/transform."""
    import rasterio
    from rasterio.transform import Affine

    b, mb = _read_band(before_path)
    a, ma = _read_band(after_path)
    if (mb["width"], mb["height"]) != (ma["width"], ma["height"]):
        raise ValueError("GeoTIFF dimensions differ; resample externally first")
    if mb["transform"] != ma["transform"]:
        raise ValueError("GeoTIFF transforms differ; co-register first")
    ratio = amplitude_ratio_db(b, a, eps=eps).astype("float32")
    profile = {
        "driver": "GTiff",
        "height": ratio.shape[0],
        "width": ratio.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": mb["crs"],
        "transform": mb["transform"],
        "nodata": float("nan"),
    }
    out_path = Path(out_path)
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(ratio, 1)
        dst.update_tags(
            registry_id="980",
            cue="amplitude_ratio_db",
            before=str(before_path),
            after=str(after_path),
        )
    side = {
        "registry_id": "980",
        "cue": "amplitude_ratio_db",
        "before": str(before_path),
        "after": str(after_path),
        "href": str(out_path),
        "units": "dB",
    }
    out_path.with_suffix(".json").write_text(json.dumps(side, indent=2) + "\n")
    return side


def write_synthetic_pair(
    directory: PathLike,
    shape: tuple[int, int] = (32, 32),
    seed: int = 0,
) -> tuple[Path, Path]:
    """Write two float32 GeoTIFFs: after has a bright 4×4 patch (linear power)."""
    import rasterio
    from rasterio.transform import from_origin

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    h, w = shape
    before = (0.05 + 0.01 * rng.random((h, w))).astype("float32")
    after = before.copy()
    after[12:16, 12:16] *= 10.0
    transform = from_origin(-100.0, 40.0, 0.0001, 0.0001)
    profile = {
        "driver": "GTiff",
        "height": h,
        "width": w,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": transform,
    }
    p0 = directory / "before.tif"
    p1 = directory / "after.tif"
    for path, arr in ((p0, before), (p1, after)):
        with rasterio.open(path, "w", **profile) as dst:
            dst.write(arr, 1)
    return p0, p1


def synthetic_complex_pair(
    shape: tuple[int, int] = (24, 24),
    seed: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Complex pair: high coherence everywhere except a changed block."""
    rng = np.random.default_rng(seed)
    h, w = shape
    phase = rng.uniform(0, 2 * np.pi, size=(h, w))
    amp = 1.0 + 0.1 * rng.random((h, w))
    z0 = amp * np.exp(1j * phase)
    z1 = amp * np.exp(1j * (phase + 0.05 * rng.standard_normal((h, w))))
    # Destroy coherence in a block
    z1[8:14, 8:14] = (1.0 + 0.1 * rng.random((6, 6))) * np.exp(
        1j * rng.uniform(0, 2 * np.pi, size=(6, 6))
    )
    return z0.astype("complex128"), z1.astype("complex128")
