"""Fetch free DEM and spectral stacks for the private multi-proxy pipeline.
One step: get real data into the engines.
"""
import os
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

def fetch_dem_3dep(bbox: Tuple[float, float, float, float], out_dir: str = "data/dem") -> Optional[str]:
    """Download a 3DEP DEM for the bounding box (west, south, east, north).
    Uses seamless-3dep if available, otherwise prints the National Map URL.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    try:
        import seamless_3dep as s3dep
        files = s3dep.get_dem(bbox, out_dir, resolution="10m")
        return files[0] if files else None
    except ImportError:
        print("Install: pip install seamless-3dep")
        print("Or download manually: https://apps.nationalmap.gov/downloader/")
        print(f"BBox: {bbox}")
        return None

def fetch_sentinel2(bbox: Tuple[float, float, float, float], date_range: Tuple[str, str], out_dir: str = "data/s2") -> Optional[str]:
    """Placeholder for Sentinel-2 L2A download via cdse-client or CDSETool.
    Returns path to a downloaded product or None.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    print("For real Sentinel-2:")
    print("  pip install cdse-client")
    print("  Register free account at https://dataspace.copernicus.eu/")
    print(f"  BBox {bbox}, dates {date_range}")
    # Stub returns None until credentials are set
    return None

def simple_coherence_diff(pre: np.ndarray, post: np.ndarray) -> np.ndarray:
    """Simple coherence difference map for disturbance detection.
    pre/post are coherence rasters [0,1]. Low values after an event flag potential change.
    """
    diff = pre - post
    return np.clip(diff, 0, 1)
