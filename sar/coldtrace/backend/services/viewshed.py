"""Viewshed computation via WhiteboxTools.

Production: uses whitebox Python package to call the viewshed tool against a
real DEM. There is no demo mode.
"""

from __future__ import annotations

import asyncio
import math
import tempfile
from pathlib import Path
from typing import Any

from ..config import settings


async def compute_viewshed(
    dem_path: Path | str,
    observer_lon: float,
    observer_lat: float,
    observer_height: float = 1.65,
    max_distance: float = 0.0,
) -> dict[str, Any]:
    """
    Run a viewshed analysis from the observer point.

    Returns a GeoJSON FeatureCollection of visible polygons.
    No demo fallback: a missing DEM or whitebox raises instead of inventing a result.
    """

    return await asyncio.to_thread(
        _run_whitebox_viewshed,
        dem_path=Path(dem_path),
        observer_lon=observer_lon,
        observer_lat=observer_lat,
        observer_height=observer_height,
        max_distance=max_distance,
    )


def _run_whitebox_viewshed(
    dem_path: Path,
    observer_lon: float,
    observer_lat: float,
    observer_height: float,
    max_distance: float,
) -> dict[str, Any]:
    """Run WhiteboxTools viewshed synchronously (called in thread pool)."""
    try:
        import whitebox
        import rasterio
        from rasterio.transform import from_bounds
        from shapely.geometry import mapping
    except ImportError as exc:
        raise RuntimeError(
            "whitebox, rasterio, and shapely must be installed for production viewshed. "
            "Set DEMO_MODE=true to use synthetic data."
        ) from exc

    wbt = whitebox.WhiteboxTools()
    wbt.verbose = False

    with tempfile.TemporaryDirectory() as tmp:
        output_path = Path(tmp) / "viewshed.tif"
        wbt.viewshed(
            dem=str(dem_path),
            output=str(output_path),
            observer_x=observer_lon,
            observer_y=observer_lat,
            observer_height=observer_height,
        )
        return _raster_to_geojson(output_path)


def _raster_to_geojson(raster_path: Path) -> dict[str, Any]:
    """Convert a binary viewshed raster to a GeoJSON FeatureCollection."""
    try:
        import rasterio
        from rasterio.features import shapes as rasterio_shapes
        from shapely.geometry import shape, mapping
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("rasterio, shapely, numpy required.") from exc

    features = []
    with rasterio.open(raster_path) as src:
        data = src.read(1)
        transform = src.transform
        for geom, val in rasterio_shapes(data.astype("uint8"), transform=transform):
            if val == 1:  # visible cells
                features.append({
                    "type": "Feature",
                    "geometry": geom,
                    "properties": {"visible": True},
                })

    return {"type": "FeatureCollection", "features": features}


