"""Golden tests for 2350 insect-trace-add-sim (written FIRST, Chitin-N).
Licence: UNLICENSED (private repo; licence pending Audrey). Synthetic, educational, non-graphic."""
import json, os, subprocess, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
SAR = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, SAR)  # parent of forensic_models for live 1010 import
from insect_trace_add_sim import sim

class GoldenTests(unittest.TestCase):
    def test_same_seed_byte_identical_json(self):
        self.assertEqual(sim.to_json(sim.run(seed=7, days=30)), sim.to_json(sim.run(seed=7, days=30)))

    def test_different_seed_differs(self):
        self.assertNotEqual(sim.to_json(sim.run(seed=7, days=30)), sim.to_json(sim.run(seed=8, days=30)))

    def test_daily_add_averaging_method(self):
        self.assertEqual(sim.daily_add(20.0, 10.0, base_c=10.0), 5.0)
        self.assertEqual(sim.daily_add(8.0, 2.0, base_c=10.0), 0.0)

    def test_stage_transitions_only_after_threshold(self):
        out = sim.run(seed=3, days=60)
        stages = sorted(out["species"]["stages"], key=lambda s: s["add_threshold"])
        for d in out["days"]:
            add = d["add_cumulative_degree_days"]
            idx = [s["name"] for s in stages].index(d["stage"])
            self.assertGreaterEqual(add, stages[idx]["add_threshold"])
            if idx + 1 < len(stages):
                self.assertLess(add, stages[idx + 1]["add_threshold"])
        self.assertEqual(out["days"][-1]["stage"], "adult")
        self.assertEqual(out["units"]["add"], "degree-days")

    def test_soil_modifier_default_identity(self):
        self.assertEqual(sim.run(seed=5, days=20)["days"],
                         sim.run(seed=5, days=20, soil_moisture_vwc=0.3)["days"])

    def test_fixture_is_synthetic_and_licensed(self):
        out = sim.run(seed=1, days=5)
        self.assertTrue(out["synthetic"])
        self.assertIn("synthetic", os.path.basename(sim.SPECIES_FIXTURE))
        self.assertEqual(out["licence"], "UNLICENSED (private repo; licence pending Audrey)")

    def test_cli_seed(self):
        r = subprocess.run([sys.executable, "-m", "insect_trace_add_sim", "--seed", "7", "--days", "30"],
                           cwd=HERE, capture_output=True, text=True, check=True)
        self.assertEqual(r.stdout.strip(), sim.to_json(sim.run(seed=7, days=30)))

class RefloatReuseTests(unittest.TestCase):
    def test_default_engine_reuses_refloat_and_labels_preprint(self):
        out = sim.run(seed=7, days=10)
        self.assertEqual(out["add_engine"]["name"], "refloat_timing")
        self.assertEqual(out["add_engine"]["label"], "preprint, not peer-reviewed")
        self.assertIn("synthetic", out["add_engine"]["species_thresholds"])

    def test_refloat_engine_matches_clean_room(self):
        a = sim.run(seed=4, days=30); b = sim.run(seed=4, days=30, add_engine="clean-room")
        self.assertEqual([d["add_cumulative_degree_days"] for d in a["days"]],
                         [d["add_cumulative_degree_days"] for d in b["days"]])
        self.assertNotIn("label", b["add_engine"])

    def test_cli_surfaces_label(self):
        r = subprocess.run([sys.executable, "-m", "insect_trace_add_sim", "--seed", "1", "--days", "3"],
                           cwd=HERE, capture_output=True, text=True, check=True)
        self.assertIn("preprint, not peer-reviewed", r.stdout)
        self.assertIn("preprint, not peer-reviewed", r.stderr)


class SoilMoistureTests(unittest.TestCase):
    def test_clamp_and_record(self):
        hi = sim.run(seed=1, days=3, soil_moisture_vwc=0.9)
        self.assertEqual(hi["soil_moisture_vwc_input"], 0.9)
        self.assertEqual(hi["soil_moisture_vwc_clamped"], 0.5)
        lo = sim.run(seed=1, days=3, soil_moisture_vwc=-1)
        self.assertEqual(lo["soil_moisture_vwc_clamped"], 0.0)
        none = sim.run(seed=1, days=3)
        self.assertIsNone(none["soil_moisture_vwc_input"])
        self.assertIsNone(none["soil_moisture_vwc_clamped"])

    def test_rejects_nan_and_non_numeric(self):
        for bad in (float("nan"), "wet", float("inf"), True):
            with self.assertRaises(ValueError):
                sim.validate_soil_moisture(bad)

    def test_cli_rejects_nan(self):
        r = subprocess.run([sys.executable, "-m", "insect_trace_add_sim", "--seed", "1", "--soil-moisture-vwc", "nan"],
                           cwd=HERE, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("soil_moisture_vwc", r.stderr)


class TaphonomyBridgeTests(unittest.TestCase):
    def test_bridge_live_backend_and_add(self):
        from insect_trace_add_sim import decay_taphonomy_bridge as b
        self.assertEqual(b.REGISTRY_PARENT, "1010")
        # Default on this branch: live 1010 (constants CLEAR 0.92). Stub only if import fails.
        self.assertEqual(b.backend_name(), "forensic_models.taphonomy")
        self.assertEqual(b.accumulated_degree_days([5.0, 15.0, 25.0], base_c=10.0), 20.0)
        hook = b.decay_hook(sim.run(seed=2, days=5))
        self.assertEqual(hook["taphonomy_backend"], "forensic_models.taphonomy")
        self.assertEqual(hook["registry_parent"], "1010")
        self.assertTrue(hook["synthetic"])

    def test_bridge_live_megyesi_add_deterministic(self):
        from insect_trace_add_sim import decay_taphonomy_bridge as b
        self.assertEqual(b.backend_name(), "forensic_models.taphonomy")
        a = b.megyesi_add(20)
        b2 = b.megyesi_add(20)
        self.assertEqual(a, b2)
        add, low, high = a
        self.assertGreater(add, 0.0)
        self.assertLessEqual(low, add)
        self.assertGreaterEqual(high, add)

if __name__ == "__main__":
    unittest.main()
