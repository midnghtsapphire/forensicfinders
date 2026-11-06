"""Golden tests for gpr_void_detector (registry 530). Write BEFORE implementation."""

from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# Peer gpr-wave-model on path for velocity/fresnel cross-check (extend, don't replace).
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "gpr-wave-model")))

import gpr_void_detector as d  # noqa: E402
import gpr_wave_model as gpr  # noqa: E402


class HyperbolaRecovery(unittest.TestCase):
    def test_hyperbola_apex_recovers_known_x0_z0(self) -> None:
        # synthetic air void at x0=2.0 m, z0=1.0 m, εr=9
        # v = 0.299792458/3 ≈ 0.099931 m/ns; recover ±0.05 m
        fixture = os.path.join(HERE, "fixtures", "synthetic_air_void_bscan.json")
        with open(fixture) as f:
            scene = json.load(f)
        out = d.detect(
            bscan=scene["bscan"],
            dx_m=scene["dx_m"],
            dt_ns=scene["dt_ns"],
            soil_er=scene["soil_er"],
            seed=42,
        )
        self.assertGreaterEqual(len(out["results"]["detections"]), 1)
        det = out["results"]["detections"][0]
        self.assertAlmostEqual(det["x0_m"], 2.0, delta=0.05)
        self.assertAlmostEqual(det["z0_m"], 1.0, delta=0.05)

    def test_velocity_matches_gpr_wave_model(self) -> None:
        v_fit = d.velocity_from_soil_er(9.0)
        self.assertAlmostEqual(v_fit, gpr.velocity(9.0), delta=1e-4)


class PolarityAndNull(unittest.TestCase):
    def test_air_polarity_label(self) -> None:
        fixture = os.path.join(HERE, "fixtures", "synthetic_air_void_bscan.json")
        with open(fixture) as f:
            scene = json.load(f)
        out = d.detect(
            bscan=scene["bscan"],
            dx_m=scene["dx_m"],
            dt_ns=scene["dt_ns"],
            soil_er=scene["soil_er"],
            seed=0,
        )
        self.assertEqual(out["results"]["detections"][0]["polarity"], "air_like")

    def test_water_polarity_label(self) -> None:
        fixture = os.path.join(HERE, "fixtures", "synthetic_water_void_bscan.json")
        with open(fixture) as f:
            scene = json.load(f)
        out = d.detect(
            bscan=scene["bscan"],
            dx_m=scene["dx_m"],
            dt_ns=scene["dt_ns"],
            soil_er=scene["soil_er"],
            seed=0,
        )
        self.assertEqual(out["results"]["detections"][0]["polarity"], "water_like")

    def test_null_bscan_no_detections(self) -> None:
        fixture = os.path.join(HERE, "fixtures", "synthetic_null_bscan.json")
        with open(fixture) as f:
            scene = json.load(f)
        out = d.detect(
            bscan=scene["bscan"],
            dx_m=scene["dx_m"],
            dt_ns=scene["dt_ns"],
            soil_er=scene["soil_er"],
            seed=scene.get("seed", 0),
        )
        self.assertEqual(out["results"]["detections"], [])


class GuardsAndDeterminism(unittest.TestCase):
    def test_seed_byte_identical(self) -> None:
        fixture = os.path.join(HERE, "fixtures", "synthetic_air_void_bscan.json")
        with open(fixture) as f:
            scene = json.load(f)
        kwargs = dict(
            bscan=scene["bscan"],
            dx_m=scene["dx_m"],
            dt_ns=scene["dt_ns"],
            soil_er=scene["soil_er"],
            seed=42,
        )
        a = d.dumps_canonical(d.detect(**kwargs))
        b = d.dumps_canonical(d.detect(**kwargs))
        self.assertEqual(a, b)

    def test_rejects_ultralytics_import(self) -> None:
        src_path = os.path.join(HERE, "gpr_void_detector.py")
        with open(src_path) as f:
            src = f.read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name.split(".")[0], "ultralytics")
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertNotEqual(node.module.split(".")[0], "ultralytics")
        # no importlib/dynamic loader of the banned name either
        self.assertNotRegex(src, r"importlib.*(ultralytics)")

    def test_cli_writes_valid_json(self) -> None:
        fixture = os.path.join(HERE, "fixtures", "synthetic_air_void_bscan.json")
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "d.json")
            with contextlib.redirect_stdout(io.StringIO()):
                d.main(
                    [
                        "--bscan",
                        fixture,
                        "--soil-er",
                        "9",
                        "--dx",
                        "0.05",
                        "--dt",
                        "0.1",
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
        self.assertIn("detections", data["results"])


if __name__ == "__main__":
    unittest.main()
