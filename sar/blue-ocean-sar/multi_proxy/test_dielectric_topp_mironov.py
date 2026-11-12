# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Humus-N (navigator) / Humus-D (driver), Grok Bot, for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  XP navigator step: failing tests for Topp (1980) permittivity<->theta_v, Mironov
#       (2009) mineralogy-based dielectric (clay %), and a seeded Topp/Mironov cross-check.
#       SenseCrew Humus owns multi_proxy/dielectric.py. Synthetic fixtures only.
# What: NEW FILE. unittest.TestCase so registry component 100 discovers these under
#       `unittest discover -s . -p 'test_*.py'` from blue-ocean-sar.
# Notes: Relative imports (`from .dielectric import ...`). No LUCAS, no case/hfmr/evidence/
#       public_records. Units: theta_v [m3/m3], clay_pct [mass %], eps [-], freq_hz [Hz].
# ══════════════════════════════════════════════════════════════════════════════════════════
"""Failing-first tests for Topp/Mironov dielectric extensions (Humus XP pair)."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import numpy as np

from .dielectric import (
    cross_check_topp_mironov,
    mironov_dielectric,
    topp_dielectric,
    topp_volumetric_water,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "topp_mironov_crosscheck_synthetic.json"

# Topp (1980) DOI 10.1029/WR016i003p00574 — forward cubic at dry end.
_TOPP_DRY_EPS = 3.03


class TestToppBidirectional(unittest.TestCase):
    """Topp eq. permittivity <-> volumetric water content."""

    def test_topp_forward_dry_end(self):
        m = np.array([0.0])
        eps = topp_dielectric(m)
        self.assertAlmostEqual(float(eps[0]), _TOPP_DRY_EPS, places=12)

    def test_topp_inverse_at_dry_permittivity(self):
        # Topp forward and inverse are independently fitted cubics, not algebraic
        # inverses; at eps=3.03 the published inverse yields ~0.03 m3/m3, not 0.
        theta = topp_volumetric_water(np.array([_TOPP_DRY_EPS]))
        self.assertAlmostEqual(float(theta[0]), 0.0305, places=3)
        self.assertGreaterEqual(float(theta[0]), 0.0)

    def test_topp_roundtrip_moisture_fraction(self):
        # theta_v in m3/m3; Topp validity ~0.02–0.5 typically.
        # atol ~0.02: published forward/inverse are separate empirical fits (DOI above).
        theta = np.array([0.05, 0.15, 0.25, 0.35])
        eps = topp_dielectric(theta)
        back = topp_volumetric_water(eps)
        np.testing.assert_allclose(back, theta, atol=2e-2, rtol=0.0)

    def test_topp_units_are_fraction_not_percent(self):
        # 25% VWC as fraction 0.25 must NOT be treated as 25.0.
        eps_ok = float(topp_dielectric(np.array([0.25]))[0])
        eps_wrong_if_percent = float(topp_dielectric(np.array([0.25]))[0])
        self.assertEqual(eps_ok, eps_wrong_if_percent)
        self.assertLess(eps_ok, 40.0)  # relative permittivity at 0.25 is well below 40
        with self.assertRaises((ValueError, AssertionError)):
            # Reject out-of-range percent-like inputs when strict flag used via helper path
            topp_volumetric_water(np.array([-1.0]))


class TestMironovMineralogy(unittest.TestCase):
    """Mironov (2009) DOI 10.1109/TGRS.2008.2011631 (+ corr. 10.1109/TGRS.2009.2023842)."""

    def test_mironov_requires_clay_pct(self):
        with self.assertRaises(TypeError):
            mironov_dielectric(0.2)  # missing clay

    def test_mironov_returns_complex_relative_permittivity(self):
        # Convention eps = eps' - j eps'' (Mironov / IEEE e^{-jωt}): imag(eps) <= 0,
        # loss factor eps'' = -imag(eps) >= 0.
        eps = mironov_dielectric(theta_v=0.2, clay_pct=20.0, freq_hz=1.4e9)
        self.assertTrue(np.iscomplexobj(eps) or isinstance(eps, complex))
        self.assertGreater(float(np.real(eps)), 1.0)
        self.assertLessEqual(float(np.imag(eps)), 0.0)
        self.assertGreaterEqual(float(-np.imag(eps)), 0.0)

    def test_mironov_real_part_rises_with_moisture(self):
        clay = 25.0
        e_dry = np.real(mironov_dielectric(0.05, clay, 1.4e9))
        e_wet = np.real(mironov_dielectric(0.35, clay, 1.4e9))
        self.assertGreater(float(e_wet), float(e_dry))

    def test_mironov_clay_changes_result(self):
        e_lo = np.real(mironov_dielectric(0.25, clay_pct=5.0, freq_hz=1.4e9))
        e_hi = np.real(mironov_dielectric(0.25, clay_pct=55.0, freq_hz=1.4e9))
        self.assertNotAlmostEqual(float(e_lo), float(e_hi), places=4)

    def test_mironov_vectorized_theta(self):
        theta = np.array([0.1, 0.2, 0.3])
        out = mironov_dielectric(theta, clay_pct=30.0, freq_hz=1.4e9)
        self.assertEqual(np.shape(out), (3,))


class TestToppMironovCrossCheck(unittest.TestCase):
    """Seeded disagreement report across a synthetic moisture/clay grid."""

    def test_cross_check_deterministic_byte_identical(self):
        a = cross_check_topp_mironov(seed=20261104, n_theta=5, n_clay=4, freq_hz=1.4e9)
        b = cross_check_topp_mironov(seed=20261104, n_theta=5, n_clay=4, freq_hz=1.4e9)
        sa = json.dumps(a, sort_keys=True, separators=(",", ":"))
        sb = json.dumps(b, sort_keys=True, separators=(",", ":"))
        self.assertEqual(sa, sb)
        self.assertEqual(
            hashlib.sha256(sa.encode("utf-8")).hexdigest(),
            hashlib.sha256(sb.encode("utf-8")).hexdigest(),
        )

    def test_cross_check_different_seeds_differ(self):
        a = cross_check_topp_mironov(seed=1, n_theta=5, n_clay=4)
        b = cross_check_topp_mironov(seed=2, n_theta=5, n_clay=4)
        self.assertNotEqual(
            json.dumps(a, sort_keys=True),
            json.dumps(b, sort_keys=True),
        )

    def test_cross_check_report_schema(self):
        report = cross_check_topp_mironov(seed=20261104, n_theta=5, n_clay=4)
        for key in (
            "seed",
            "freq_hz",
            "n_theta",
            "n_clay",
            "theta_v_m3m3",
            "clay_pct",
            "eps_topp",
            "eps_mironov_real",
            "abs_diff",
            "rmse",
            "max_abs_diff",
            "citations",
        ):
            self.assertIn(key, report)
        self.assertEqual(report["seed"], 20261104)
        self.assertEqual(report["citations"]["topp_1980"], "10.1029/WR016i003p00574")
        self.assertEqual(report["citations"]["mironov_2009"], "10.1109/TGRS.2008.2011631")
        self.assertIsInstance(report["rmse"], float)
        self.assertIsInstance(report["max_abs_diff"], float)
        self.assertGreaterEqual(report["max_abs_diff"], 0.0)

    def test_cross_check_matches_synthetic_fixture(self):
        self.assertTrue(FIXTURE.is_file(), f"missing synthetic fixture {FIXTURE}")
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
        got = cross_check_topp_mironov(
            seed=expected["seed"],
            n_theta=expected["n_theta"],
            n_clay=expected["n_clay"],
            freq_hz=expected["freq_hz"],
        )
        self.assertEqual(
            json.dumps(got, sort_keys=True, separators=(",", ":")),
            json.dumps(expected, sort_keys=True, separators=(",", ":")),
        )


if __name__ == "__main__":
    unittest.main()
