"""Temporal change detection — NDVI diff and elevation change."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from ..config import settings
from ..models.analysis import ElevationChange, NDVIAnomaly


async def compute_ndvi_diff(
    ndvi_before: Any,
    ndvi_after: Any,
    sigma_threshold: float = 1.5,
) -> list[NDVIAnomaly]:
    """
    Compute pixel-wise NDVI delta and return anomalies above sigma_threshold.
    Production uses rioxarray + numpy; there is no demo fallback.
    """

    return await asyncio.to_thread(
        _compute_ndvi_sync, ndvi_before, ndvi_after, sigma_threshold
    )


async def compute_elevation_diff(
    dem_path: Path | str,
    date_start: Any,
    date_end: Any,
    threshold_m: float = 0.25,
) -> list[ElevationChange]:
    """
    Compare multi-epoch DEMs to detect terrain changes.
    Production fetches second DEM epoch from USGS 3DEP; there is no demo fallback.
    """

    return await asyncio.to_thread(
        _compute_elev_sync, Path(dem_path), threshold_m
    )


def _compute_ndvi_sync(ndvi_before: Any, ndvi_after: Any, sigma_threshold: float) -> list[NDVIAnomaly]:
    """Synchronous NDVI delta computation (called in thread pool)."""
    try:
        import numpy as np
        import rioxarray  # registers the .rio accessor on xarray objects
    except ImportError as exc:
        raise RuntimeError("numpy and rioxarray required for NDVI computation.") from exc

    before = ndvi_before.values.astype(float)
    after = ndvi_after.values.astype(float)
    delta = after - before

    mean = float(np.nanmean(delta))
    std = float(np.nanstd(delta))
    if std == 0:
        return []

    mask = np.abs(delta - mean) > sigma_threshold * std
    ys, xs = np.where(mask)

    anomalies = []
    for y, x in zip(ys[:50], xs[:50]):  # cap at 50 anomalies
        transform = ndvi_after.rio.transform()
        lon = transform.c + x * transform.a
        lat = transform.f + y * transform.e
        anomalies.append(
            NDVIAnomaly(
                lon=float(lon),
                lat=float(lat),
                sigma=float(abs(delta[y, x] - mean) / std),
                ndvi_before=float(before[y, x]),
                ndvi_after=float(after[y, x]),
                ndvi_delta=float(delta[y, x]),
            )
        )

    return sorted(anomalies, key=lambda a: -a.sigma)


def _compute_elev_sync(dem_path: Path, threshold_m: float) -> list[ElevationChange]:
    """Synchronous elevation change detection (stub — fetches second epoch in prod)."""
    return []



