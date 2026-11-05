"""Golden tests for 2350 insect-trace-add-sim (written FIRST, Chitin-N).
Licence: UNLICENSED (private repo; licence pending Audrey). Synthetic, educational, non-graphic."""
import json, os, subprocess, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
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
        thr = {s["name"]: s["add_threshold"] for s in out["species"]["stages"]}
        for d in out["days"]:
            self.assertGreaterEqual(d["add_cumulative_degree_days"], thr[d["stage"]])
        self.assertEqual(out["units"], {"temperature": "degC", "add": "degree-days"})

    def test_soil_modifier_default_identity(self):
        self.assertEqual(sim.to_json(sim.run(seed=5, days=20)),
                         sim.to_json(sim.run(seed=5, days=20, soil_moisture_vwc=0.3)))

    def test_fixture_is_synthetic_and_licensed(self):
        out = sim.run(seed=1, days=5)
        self.assertTrue(out["synthetic"])
        self.assertIn("synthetic", os.path.basename(sim.SPECIES_FIXTURE))
        self.assertEqual(out["licence"], "UNLICENSED (private repo; licence pending Audrey)")

    def test_cli_seed(self):
        r = subprocess.run([sys.executable, "-m", "insect_trace_add_sim", "--seed", "7", "--days", "30"],
                           cwd=HERE, capture_output=True, text=True, check=True)
        self.assertEqual(r.stdout.strip(), sim.to_json(sim.run(seed=7, days=30)))

if __name__ == "__main__":
    unittest.main()
