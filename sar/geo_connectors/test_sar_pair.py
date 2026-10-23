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


class Despeckle(unittest.TestCase):
    def test_off_by_default(self) -> None:
        before = np.full((8, 8), 1.0)
        after = np.full((8, 8), 10.0)
        a = sp.amplitude_ratio_db(before, after)
        b = sp.amplitude_ratio_db(before, after, despeckle_method=None)
        self.assertTrue(np.allclose(a, b))
        self.assertTrue(np.allclose(sp.despeckle(after), after))

    def test_lee_reduces_speckle_variance(self) -> None:
        clean, speckled = sp.synthetic_speckled_image(looks=1.0, seed=11)
        filtered = sp.lee_filter(speckled, window=7, looks=1.0)
        # Compare within a homogeneous region, away from the central edge.
        raw = speckled[:, 4:24]
        out = filtered[:, 4:24]
        self.assertLess(float(np.var(out)), float(np.var(raw)) * 0.5)
        # Mean is roughly preserved (no bias blow-up).
        self.assertAlmostEqual(float(np.mean(out)), float(np.mean(raw)), delta=0.2)
        # Closer to truth than the noisy input, in MSE.
        truth = clean[:, 4:24]
        self.assertLess(
            float(np.mean((out - truth) ** 2)), float(np.mean((raw - truth) ** 2))
        )

    def test_refined_lee_keeps_edge_sharper_than_lee(self) -> None:
        clean, speckled = sp.synthetic_speckled_image(looks=4.0, seed=12)
        lee = sp.lee_filter(speckled, window=9, looks=4.0)
        ref = sp.refined_lee_filter(speckled, window=9, looks=4.0)
        # Step is from 1.0 to 4.0 at column 32; measure contrast across the edge.
        def step(arr: np.ndarray) -> float:
            return float(np.mean(arr[:, 32:35])) - float(np.mean(arr[:, 29:32]))

        self.assertGreater(step(ref), step(lee))
        self.assertLess(float(np.var(ref[:, 4:24])), float(np.var(speckled[:, 4:24])))

    def test_filters_reject_bad_args(self) -> None:
        _, speckled = sp.synthetic_speckled_image(shape=(16, 16))
        with self.assertRaises(ValueError):
            sp.lee_filter(speckled, window=4)
        with self.assertRaises(ValueError):
            sp.lee_filter(speckled, window=7, looks=0)
        with self.assertRaises(ValueError):
            sp.refined_lee_filter(speckled, window=2)
        with self.assertRaises(ValueError):
            sp.despeckle(speckled, "sar-cnn")

    def test_despeckled_ratio_still_finds_change(self) -> None:
        rng = np.random.default_rng(5)
        before = rng.gamma(4.0, 1.0 / 4.0, size=(48, 48)) * 0.1
        after = before.copy()
        after[20:28, 20:28] *= 10.0
        r = sp.amplitude_ratio_db(
            before, after, despeckle_method="refined_lee", despeckle_window=7, looks=4.0
        )
        self.assertGreater(float(np.mean(r[22:26, 22:26])), 5.0)
        self.assertLess(abs(float(np.mean(r[0:10, 0:10]))), 2.0)


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
            self.assertIsNone(side["despeckle"]["method"])
            self.assertTrue((root / "ratio.tif").is_file())
            self.assertTrue((root / "ratio.json").is_file())
            import rasterio

            with rasterio.open(root / "ratio.tif") as ds:
                arr = ds.read(1)
            self.assertGreater(float(np.nanmean(arr[12:16, 12:16])), 8.0)


if __name__ == "__main__":
    unittest.main()
