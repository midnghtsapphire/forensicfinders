"""Tests for waveform (985) on a synthetic canopy + ground waveform."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from geo_connectors import waveform as wv  # noqa: E402


class Decompose(unittest.TestCase):
    def test_two_returns_ground_last(self) -> None:
        t = np.arange(300, dtype=float)
        rng = np.random.default_rng(0)
        y = 50 + wv.gaussian_sum(t, 40, 100, 8, 120, 220, 4) + rng.normal(0, 1.0, t.size)
        out = wv.decompose(y, t)
        self.assertEqual(len(out["peaks"]), 2)
        g = out["ground"]
        self.assertAlmostEqual(g.center, 220, delta=0.5)
        self.assertAlmostEqual(g.sigma, 4, delta=0.5)
        self.assertAlmostEqual(out["peaks"][0].center, 100, delta=1.0)
        self.assertAlmostEqual(out["baseline"], 50, delta=2.0)

    def test_noise_only(self) -> None:
        y = np.random.default_rng(1).normal(10, 1, 200)
        self.assertIsNone(wv.decompose(y, noise_sigmas=6)["ground"])

    def test_bad_input(self) -> None:
        with self.assertRaises(ValueError):
            wv.decompose([1, 2])


if __name__ == "__main__":
    unittest.main()
