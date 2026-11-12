"""Golden tests for ert_model (registry 510). Write BEFORE implementation (Deepscan-N)."""

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

import ert_model as m  # noqa: E402


class GeometricFactors(unittest.TestCase):
    def test_wenner_geometric_factor(self) -> None:
        # a=2 m → K=2πa ≈ 12.566371 m ± 1e-9
        self.assertAlmostEqual(m.wenner_geometric_factor(2.0), 2.0 * math.pi * 2.0, delta=1e-9)
        self.assertAlmostEqual(m.wenner_geometric_factor(2.0), 12.5663706144, delta=1e-9)

    def test_dipole_dipole_geometric_factor(self) -> None:
        # a=1 m, n=2 → K=π·2·3·4·1 = 24π ≈ 75.398224 ± 1e-9
        self.assertAlmostEqual(m.dipole_dipole_geometric_factor(1.0, 2), 24.0 * math.pi, delta=1e-9)
        self.assertAlmostEqual(m.dipole_dipole_geometric_factor(1.0, 2), 75.3982236862, delta=1e-9)


class HomogeneousAndLayered(unittest.TestCase):
    def test_wenner_homogeneous_equals_host(self) -> None:
        # ρh=100 Ω·m, a∈{1,2,5,10} m → ρa = 100 ± 1e-9 Ω·m
        for a in (1.0, 2.0, 5.0, 10.0):
            data = m.model(
                array="wenner",
                a_m=a,
                rho_layers_ohm_m=[100.0],
                thickness_m=[],
                profile_x_m=[0.0],
                seed=0,
                noise_pct=0.0,
            )
            for rho_a in data["results"]["apparent_resistivity_ohm_m"]:
                self.assertAlmostEqual(rho_a, 100.0, delta=1e-9, msg=f"a={a}")

    def test_two_layer_large_a_approaches_basement(self) -> None:
        # ρ=[100,500], h=5 m; at a ≫ h, ρa within 5% of 500
        data = m.model(
            array="wenner",
            a_m=200.0,
            rho_layers_ohm_m=[100.0, 500.0],
            thickness_m=[5.0],
            profile_x_m=[0.0],
            seed=0,
            noise_pct=0.0,
        )
        rho_a = data["results"]["apparent_resistivity_ohm_m"][0]
        self.assertAlmostEqual(rho_a, 500.0, delta=0.05 * 500.0)


class SphereAnomaly(unittest.TestCase):
    def test_insulating_sphere_peak_positive_anomaly(self) -> None:
        # air sphere: max(ρa)/ρh > 1 along surface profile over centre
        profile = [float(x) for x in range(-20, 21)]
        data = m.model(
            array="wenner",
            a_m=2.0,
            host_rho_ohm_m=100.0,
            sphere_center_m=(0.0, 0.0, 3.0),
            sphere_radius_m=1.0,
            sphere_rho_ohm_m=1.0e6,
            profile_x_m=profile,
            seed=0,
            noise_pct=0.0,
        )
        rhos = data["results"]["apparent_resistivity_ohm_m"]
        self.assertGreater(max(rhos) / 100.0, 1.0)


class DeterminismAndCli(unittest.TestCase):
    def test_seed_byte_identical(self) -> None:
        kwargs = dict(
            array="wenner",
            a_m=2.0,
            rho_layers_ohm_m=[100.0],
            thickness_m=[],
            profile_x_m=[0.0, 2.0, 4.0],
            seed=42,
            noise_pct=5.0,
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
                        "--array",
                        "wenner",
                        "--a",
                        "2",
                        "--rho-layers",
                        "100",
                        "--profile",
                        "0",
                        "2",
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
        self.assertIn("apparent_resistivity_ohm_m", data["results"])
        self.assertEqual(data["parameters"]["array"], "wenner")


if __name__ == "__main__":
    unittest.main()
