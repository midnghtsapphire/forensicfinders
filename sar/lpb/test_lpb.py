import os, unittest
import lpb
HERE = os.path.dirname(os.path.abspath(__file__))
SYN = {"source": {"citation": "synthetic test table", "verified": True},
       "profiles": [{"key": "human/child", "when": {"age": {"max": 3}}, "speed_kmh": 1, "p25_km": 1, "p50_km": 2, "p75_km": 3, "p95_km": 4},
                    {"key": "human/child", "speed_kmh": 2, "p25_km": 2, "p50_km": 4, "p75_km": 6, "p95_km": 8}]}

class T(unittest.TestCase):
    def test_match_order_and_bounds(self):
        t = lpb.load_table(SYN)
        self.assertEqual(lpb.profile(t, "human", "child", {"age": 2})["p50_km"], 2)
        self.assertEqual(lpb.profile(t, "human", "child", {"age": 9})["p50_km"], 4)
    def test_no_default_means_no_data(self):
        t = lpb.load_table(SYN)
        self.assertIsNone(lpb.profile(t, "animal", "cat"))
        self.assertEqual(lpb.rings(None), [])
    def test_rings(self):
        r = lpb.rings(lpb.profile(lpb.load_table(SYN), "human", "child", {"age": 9}))
        self.assertEqual([x["percentile"] for x in r], [25, 50, 75, 95])
    def test_unverified_refused_by_default(self):
        p = os.path.join(HERE, "lpb_table.unverified.example.json")
        with self.assertRaises(lpb.UnverifiedTable): lpb.load_table(p)
        t = lpb.load_table(p, allow_unverified=True)
        self.assertEqual(lpb.profile(t, "human", "hiker", {"experience_level": "expert"})["p95_km"], 20.0)
    def test_missing_citation_and_bad_percentiles(self):
        with self.assertRaises(lpb.UnverifiedTable): lpb.load_table({"source": {}, "profiles": []})
        bad = {"source": {"citation": "x", "verified": True}, "profiles": [{"key": "a/b", "speed_kmh": 1, "p25_km": 3, "p50_km": 2, "p75_km": 4, "p95_km": 5}]}
        with self.assertRaises(ValueError): lpb.load_table(bad)
    def test_haversine_synthetic(self):
        self.assertAlmostEqual(lpb.haversine_km(0, 0, 0, 1), 111.19, places=1)

if __name__ == "__main__": unittest.main()
