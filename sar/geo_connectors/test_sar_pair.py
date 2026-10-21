"""Tests for sar_pair (980)."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from geo_connectors import sar_pair as sp  # noqa: E402

HAS_RASTERIO = importlib.util.find_spec("rasterio") is not None


class AmplitudeRatio(unittest.TestCase):
    def test_known_ratio(self) -> None:
        r = sp.amplitude_ratio_db(np.array([[1.0]]), np.array([[10.0]]))
        self.assertAlmostEqual(float(r[0, 0]), 10.0, places=5)

    def test_shape_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            sp.amplitude_ratio_db(np.zeros((2, 2)), np.zeros((3, 3)))


class CoherentChange(unittest.TestCase):
    def test_changed_block_lower_coherence(self) -> None:
        z0, z1 = sp.synthetic_complex_pair(seed=2)
        coh = sp.coherent_change_index(z0, z1, window=5)
        stable = float(np.mean(coh[0:6, 0:6]))
        changed = float(np.mean(coh[8:14, 8:14]))
        self.assertGreater(stable, 0.85)
        self.assertLess(changed, stable - 0.15)

    def test_window_must_be_odd(self) -> None:
        z0, z1 = sp.synthetic_complex_pair()
        with self.assertRaises(ValueError):
            sp.coherent_change_index(z0, z1, window=4)


@unittest.skipUnless(HAS_RASTERIO, "rasterio not installed")
class GeoTIFFPair(unittest.TestCase):
    def test_write_ratio(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            b, a = sp.write_synthetic_pair(root, seed=3)
            side = sp.pair_amplitude_ratio_geotiff(b, a, root / "ratio.tif")
            self.assertEqual(side["cue"], "amplitude_ratio_db")
            self.assertTrue((root / "ratio.tif").is_file())
            self.assertTrue((root / "ratio.json").is_file())
            import rasterio

            with rasterio.open(root / "ratio.tif") as ds:
                arr = ds.read(1)
            self.assertGreater(float(np.nanmean(arr[12:16, 12:16])), 8.0)


if __name__ == "__main__":
    unittest.main()
