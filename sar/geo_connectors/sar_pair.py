"""Pairwise SAR GeoTIFF change cues (amplitude ratio + optional coherent change).

Optional speckle filtering (classical Lee / refined Lee, numpy only) can be applied
before change detection. It is OFF by default.

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


def _boxcar_mean(img: np.ndarray, window: int) -> np.ndarray:
    """Mean over a square boxcar of odd size, edge-padded (numpy only)."""
    pad = window // 2
    p = np.pad(img, pad, mode="edge")
    csum = p.cumsum(axis=0).cumsum(axis=1)
    csum = np.pad(csum, ((1, 0), (1, 0)), mode="constant")
    h, w = img.shape
    total = (
        csum[window:window + h, window:window + w]
        - csum[0:h, window:window + w]
        - csum[window:window + h, 0:w]
        + csum[0:h, 0:w]
    )
    return total / float(window * window)


def lee_filter(
    img: np.ndarray,
    window: int = 7,
    looks: float = 1.0,
    eps: float = 1e-12,
) -> np.ndarray:
    """Classical Lee speckle filter for intensity images (Lee, 1980).

    Multiplicative speckle model: the local linear MMSE estimate is
    ``mean + k * (x - mean)`` with ``k = max(0, var - mean^2 * cu^2) / var``
    and ``cu^2 = 1 / looks`` the speckle coefficient of variation squared.
    Pure numpy; no training, no GPU.
    """
    if window < 3 or window % 2 == 0:
        raise ValueError("window must be odd and >= 3")
    if looks <= 0:
        raise ValueError("looks must be > 0")
    x = np.asarray(img, dtype="float64")
    if x.ndim != 2:
        raise ValueError("img must be 2-D")
    mean = _boxcar_mean(x, window)
    mean_sq = _boxcar_mean(x * x, window)
    var = np.maximum(mean_sq - mean * mean, 0.0)
    cu2 = 1.0 / float(looks)
    k = np.clip((var - mean * mean * cu2) / (var + eps), 0.0, 1.0)
    return mean + k * (x - mean)


def refined_lee_filter(
    img: np.ndarray,
    window: int = 7,
    looks: float = 1.0,
    edge_threshold: float = 1.0,
    eps: float = 1e-12,
) -> np.ndarray:
    """Edge-aware ("refined") Lee filter, numpy only.

    Runs the Lee estimator twice: a large window in locally homogeneous areas and a
    small (3x3) window where the local coefficient of variation exceeds
    ``edge_threshold * sqrt(1/looks)``, i.e. where structure (an edge or point
    target) is likely. This keeps edges sharper than plain Lee while still
    smoothing flat speckle. No training, no GPU.
    """
    if window < 3 or window % 2 == 0:
        raise ValueError("window must be odd and >= 3")
    x = np.asarray(img, dtype="float64")
    broad = lee_filter(x, window=window, looks=looks, eps=eps)
    fine = lee_filter(x, window=3, looks=looks, eps=eps)
    mean = _boxcar_mean(x, window)
    mean_sq = _boxcar_mean(x * x, window)
    var = np.maximum(mean_sq - mean * mean, 0.0)
    ci = np.sqrt(var) / (mean + eps)
    cu = math.sqrt(1.0 / float(looks))
    structured = ci > (edge_threshold * cu)
    return np.where(structured, fine, broad)


DESPECKLE_FILTERS = {"lee": lee_filter, "refined_lee": refined_lee_filter}


def despeckle(
    img: np.ndarray,
    method: Optional[str] = None,
    window: int = 7,
    looks: float = 1.0,
) -> np.ndarray:
    """Optional speckle filter. ``method=None`` (default) returns the input unchanged.

    Supported methods: ``"lee"``, ``"refined_lee"``. Deep-learning despecklers are
    documented as optional add-ons in docs/research/vhr-radar-lidar-fusion.md (2030)
    but are not implemented or vendored here.
    """
    if method is None:
        return np.asarray(img, dtype="float64")
    try:
        fn = DESPECKLE_FILTERS[method]
    except KeyError:
        raise ValueError(
            f"unknown despeckle method {method!r}; "
            f"expected one of {sorted(DESPECKLE_FILTERS)} or None"
        ) from None
    return fn(img, window=window, looks=looks)


def amplitude_ratio_db(
    before: np.ndarray,
    after: np.ndarray,
    eps: float = 1e-6,
    despeckle_method: Optional[str] = None,
    despeckle_window: int = 7,
    looks: float = 1.0,
) -> np.ndarray:
    """10·log10(after/before) in dB. Inputs are linear amplitude or power (same units).

    Optional pre-filtering: ``despeckle_method`` is ``None`` by default (no filtering,
    behaviour unchanged). Set it to ``"lee"`` or ``"refined_lee"`` to speckle-filter
    both scenes with identical settings before the ratio.
    """
    b = np.asarray(before, dtype="float64")
    a = np.asarray(after, dtype="float64")
    if b.shape != a.shape:
        raise ValueError(f"shape mismatch {b.shape} vs {a.shape}")
    if despeckle_method is not None:
        b = despeckle(b, despeckle_method, window=despeckle_window, looks=looks)
        a = despeckle(a, despeckle_method, window=despeckle_window, looks=looks)
        b = np.maximum(b, 0.0)
        a = np.maximum(a, 0.0)
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
    despeckle_method: Optional[str] = None,
    despeckle_window: int = 7,
    looks: float = 1.0,
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
    ratio = amplitude_ratio_db(
        b,
        a,
        eps=eps,
        despeckle_method=despeckle_method,
        despeckle_window=despeckle_window,
        looks=looks,
    ).astype("float32")
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
            despeckle=str(despeckle_method),
        )
    side = {
        "registry_id": "980",
        "cue": "amplitude_ratio_db",
        "before": str(before_path),
        "after": str(after_path),
        "href": str(out_path),
        "units": "dB",
        "despeckle": {
            "method": despeckle_method,
            "window": despeckle_window if despeckle_method else None,
            "looks": looks if despeckle_method else None,
        },
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


def synthetic_speckled_image(
    shape: tuple[int, int] = (64, 64),
    looks: float = 1.0,
    seed: int = 7,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (clean, speckled) intensity images for tests.

    Clean image is a two-level step (edge down the middle). Speckle is multiplicative
    Gamma noise with unit mean and the given number of looks, the standard
    single-channel intensity speckle model.
    """
    rng = np.random.default_rng(seed)
    h, w = shape
    clean = np.full((h, w), 1.0)
    clean[:, w // 2:] = 4.0
    noise = rng.gamma(shape=looks, scale=1.0 / looks, size=(h, w))
    return clean, clean * noise
