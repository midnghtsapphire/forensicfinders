"""Golden tests for magnetometry_model (registry 520). Write BEFORE implementation."""

from __future__ import annotations

import contextlib
import io
import json
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import magnetometry_model as m  # noqa: E402

MU0_OVER_4PI = 1.0e-7


class DipolePhysics(unittest.TestCase):
    def test_dipole_axial_field(self) -> None:
        # vertical m=(0,0,1), on axis at z=10 m:
        # Bz = (μ0/4π) * 2m / z^3 = 2e-10 T = 0.2 nT
        # Spec v0 wrote "2e-9 T = 2.0 nT"; corrected to SI (Blakely 1995 / Jackson).
        B = m.dipole_B_nT(m_A_m2=(0.0, 0.0, 1.0), r_m=(0.0, 0.0, 10.0))
        self.assertAlmostEqual(B[2], 0.2, delta=1e-6)

    def test_total_field_reduces_to_Bz_when_vertical_B0(self) -> None:
        Banom = (1.0, 2.0, 3.0)  # nT
        dT = m.total_field_anomaly_nT(Banom_nT=Banom, inc_deg=90.0, dec_deg=0.0)
        self.assertAlmostEqual(dT, Banom[2], delta=1e-6 * abs(Banom[2]))


class SphereAndDyke(unittest.TestCase):
    def test_sphere_moment_scales_R3(self) -> None:
        m1 = m.sphere_moment_A_m2(radius_m=1.0, kappa=0.1, B0_nT=50000.0, inc_deg=65.0, dec_deg=10.0)
        m2 = m.sphere_moment_A_m2(radius_m=2.0, kappa=0.1, B0_nT=50000.0, inc_deg=65.0, dec_deg=10.0)
        mag1 = math.sqrt(sum(c * c for c in m1))
        mag2 = math.sqrt(sum(c * c for c in m2))
        self.assertAlmostEqual(mag2 / mag1, 8.0, delta=1e-9)

    def test_thin_dyke_antisymmetric_or_symmetric_by_dip(self) -> None:
        # vertical dyke + vertical magnetization → symmetric ΔT about epicentre
        xs = [float(x) for x in range(-20, 21)]
        data = m.model(
            model_kind="thin_dyke",
            depth_m=10.0,
            dip_deg=90.0,
            thickness_m=2.0,
            susceptibility=0.05,
            B0_nT=50000.0,
            inc_deg=90.0,
            dec_deg=0.0,
            dyke_strike_deg=90.0,
            profile_x_m=xs,
            seed=0,
            noise_nT=0.0,
        )
        dT = data["results"]["delta_T_nT"]
        mid = len(xs) // 2
        for i in range(1, mid + 1):
            self.assertAlmostEqual(dT[mid - i], dT[mid + i], delta=1e-6, msg=f"i={i}")


class DeterminismAndCli(unittest.TestCase):
    def test_seed_byte_identical(self) -> None:
        kwargs = dict(
            model_kind="dipole",
            m_A_m2=(0.0, 0.0, 10.0),
            center_m=(0.0, 0.0, 5.0),
            B0_nT=50000.0,
            inc_deg=65.0,
            dec_deg=10.0,
            profile_x_m=[-5.0, 0.0, 5.0],
            seed=42,
            noise_nT=1.0,
        )
        a = m.dumps_canonical(m.model(**kwargs))
        b = m.dumps_canonical(m.model(**kwargs))
        self.assertEqual(a, b)

    def test_cli_writes_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "r.json")
            with contextlib.redirect_stdout(io.StringIO()):
                m.main(
                    [
                        "--kind",
                        "sphere",
                        "--depth",
                        "5",
                        "--radius",
                        "1",
                        "--kappa",
                        "0.1",
                        "--B0",
                        "50000",
                        "--inc",
                        "65",
                        "--dec",
                        "10",
                        "--profile",
                        "-2:2:1",
                        "--seed",
                        "42",
                        "--out",
                        out,
                        "--no-table",
                    ]
                )
            with open(out) as f:
                data = json.load(f)
        self.assertEqual(data["parameters"]["seed"], 42)
        self.assertIn("delta_T_nT", data["results"])


if __name__ == "__main__":
    unittest.main()
