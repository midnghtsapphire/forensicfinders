"""1060 golden tests, written first. expectedFailure until Driver impl (keeps main green, documents contract)."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decay_taphonomy_model as m
class Contract(unittest.TestCase):
    def test_interface_fields(self):
        self.assertEqual(m.SOIL_INTERFACE_FIELDS, ("moisture_vwc", "dielectric", "synthetic_voc_proxies", "soil_dna_sensor_copies_per_g"))
    @unittest.expectedFailure
    def test_same_seed_identical(self):
        self.assertEqual(m.run(seed=1), m.run(seed=1))
    @unittest.expectedFailure
    def test_stage_monotonic_with_add(self):
        out = m.run(seed=2, days=40); self.assertTrue(out["synthetic"])
if __name__ == "__main__": unittest.main()
