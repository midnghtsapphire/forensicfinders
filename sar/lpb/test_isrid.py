"""Checks sar/data/isrid_distances.json against values printed in Koester (2008) p.164 (Dementia.pdf)."""
import unittest
import lpb


class ISRID(unittest.TestCase):
    def setUp(self):
        self.t = lpb.load_isrid()

    def p(self, **a):
        return lpb.profile(self.t, "human", "dementia", a)

    def test_printed_values(self):
        self.assertEqual(self.p(ecoregion="temperate", terrain="mountain")["p95_km"], 8.3)
        self.assertEqual(self.p(ecoregion="temperate", terrain="flat")["p50_km"], 1.0)
        self.assertEqual(self.p(ecoregion="dry", terrain="mountain")["p25_km"], 1.0)
        self.assertEqual(self.p(ecoregion="urban")["p75_km"], 3.2)

    def test_rings_and_no_invention(self):
        r = lpb.rings(self.p(ecoregion="dry", terrain="flat"))
        self.assertEqual([x["radius_km"] for x in r], [0.5, 1.6, 3.6, 11.8])
        self.assertIsNone(lpb.profile(self.t, "human", "hiker", {"ecoregion": "temperate", "terrain": "flat"}))

    def test_rows_cite_page(self):
        import json
        d = json.load(open(lpb.ISRID_PATH))
        self.assertIn("Koester", d["source"]["citation"])
        for r in d["distances"]:
            self.assertEqual(r["page"], 164)
            self.assertTrue(r["url"].startswith("https://dbs-sar.com/LPB/"))
        o = d["other_stats"]["dementia"]
        self.assertEqual(o["track_offset_m"]["p95"], 307)
        self.assertEqual(o["alive_by_elapsed"][0]["alive_pct"], 95)


if __name__ == "__main__":
    unittest.main()
