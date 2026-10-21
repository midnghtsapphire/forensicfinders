# PROPRIETARY - ALL RIGHTS RESERVED. (c) 2026 Audrey Evans / Walter-Evans Forensic Intelligence Systems.
"""Synthetic-data tests for search_system (1400-1450). No real case data."""
import json, os, sys, tempfile, unittest
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import remains_anomaly_pipeline as rap, run_county as rc, field_confirmation as fc, coldcase_master as cm, fall_physics as fp


class Pipeline(unittest.TestCase):  # 1410
    def test_lod_is_196_sigma_for_gaussian(self):
        x = np.random.default_rng(0).normal(0, 0.05, 200000)
        self.assertAlmostEqual(rap.level_of_detection(x), 1.96 * 0.05, delta=0.002)

    def test_signature_peaks_at_planted_grave(self):
        rng = np.random.default_rng(1); years = [2018, 2020, 2023, 2026]
        dems = [np.zeros((60, 60)) + rng.normal(0, 0.005, (60, 60)) for _ in years]
        rap.plant_grave(dems, years, 2019, 30, 30)
        s = rap.grave_signature_score(dems, years, 1.0)
        r, c = np.unravel_index(np.argmax(s), s.shape)
        self.assertLessEqual(max(abs(r - 30), abs(c - 30)), 3)

    def test_make_tile_has_no_label_leakage(self):
        _, rasters, lab = rap.make_tile(5, shape=(80, 80), graves=[(40, 40, 2020)])
        self.assertEqual(lab.sum(), 25)
        self.assertEqual(rasters["reports"].max(), 0.0)
        self.assertEqual(rasters["nitrate"].max(), 0.0)

    def test_qpcr_scaling(self):
        out = rap.qpcr_quantify(37.9 - 3.32 * 3, (-3.32, 37.9), 24.6, 24.6, soil_g=0.25, elution_ul=100, template_ul=2)
        self.assertAlmostEqual(out["copies_per_g_soil"], 1000 * 50 / 0.25, delta=1e-6)
        self.assertFalse(out["inhibited"])
        with self.assertRaises(ValueError):
            rap.qpcr_quantify(30, (-3.32, 37.9), 24, 24, soil_g=0, elution_ul=100, template_ul=2)


class County(unittest.TestCase):  # 1420
    def test_tile_aoi_ragged(self):
        t = rc.tile_aoi([0, 0, 250, 100], 100, 1.0)
        self.assertEqual(len(t), 3); self.assertEqual(t[-1]["shape"], (100, 50))

    def test_validate_config(self):
        self.assertIn("missing key: bbox", rc.validate_config({}))
        cfg = {"bbox": [0, 0, 10, 10], "tile_m": 5, "res": 1, "years": [2020, 2018],
               "epochs": [{"year": 2020}], "sites_csv": "/nonexistent.csv", "out_dir": "x"}
        p = rc.validate_config(cfg)
        self.assertTrue(any("ascending" in x for x in p)); self.assertTrue(any("ept_url or bbox" in x for x in p))

    def test_compute_tile_rasters_with_arrays(self):
        dems = [np.zeros((40, 40)) for _ in range(3)]
        r = rc.compute_tile_rasters(dems, [2018, 2020, 2023], 1.0, {"ndvi_raster": np.ones((40, 40))})
        self.assertEqual(r["ndvi"].mean(), 1.0)


class Assay(unittest.TestCase):  # 1430
    def test_lod_loq(self):
        concs = [10, 100, 1000]
        cts = [[30, np.nan, np.nan, np.nan], [27, 27.1, 26.9, np.nan], [24, 24.1, 23.9, 24.0]]
        lod, loq = fc.estimate_lod_loq(concs, cts)
        self.assertTrue(100 < lod < 1000); self.assertEqual(loq, 1000.0)
        lod2, _ = fc.estimate_lod_loq([10, 100], [[30, 30, 30], [27, 27, 27]])
        self.assertEqual(lod2, 10.0)

    def test_interpret_order(self):
        self.assertTrue(fc.interpret_sample(30, 27, 24, 500, 100, 200)["call"].startswith("INCONCLUSIVE - inhibition"))
        self.assertTrue(fc.interpret_sample(30, 24, 24, 500, 100, 200, triplicate_ct=[29, 30, 31.2])["call"].startswith("INCONCLUSIVE - replicates"))
        self.assertTrue(fc.interpret_sample(30, 24, 24, 50, 100, 200)["call"].startswith("NEGATIVE"))
        self.assertTrue(fc.interpret_sample(30, 24, 24, 150, 100, 200)["call"].startswith("DETECTED below LOQ"))
        self.assertIn("ASSAY UNVALIDATED", fc.interpret_sample(30, 24, 24, 150, None, None)["call"])

    def test_culvert_vs_compact(self):
        dem = np.zeros((120, 120)); dem[60:63, 10:100] -= 0.5
        yy, xx = np.mgrid[0:120, 0:120]; dem -= 0.5 * np.exp(-((yy - 20) ** 2 + (xx - 20) ** 2) / 8.0)
        _, df = fc.detect_culverts(dem, 1.0)
        self.assertIn("linear (culvert/vault?)", set(df.kind)); self.assertIn("compact (grave-scale?)", set(df.kind))


class EvidenceLog(unittest.TestCase):  # 1440
    def test_chain_and_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "a.txt"); open(f, "w").write("x")
            log = cm.EvidenceLog(os.path.join(d, "evidence.jsonl"))
            log.record("one", f); log.record("two", f, {"k": 1})
            ok, rep = cm.verify_chain(log.path); self.assertTrue(ok); self.assertEqual(rep["entries"], 2)
            lines = open(log.path).read().splitlines(); e = json.loads(lines[1]); e["action"] = "tampered"
            open(log.path, "w").write(lines[0] + "\n" + json.dumps(e) + "\n")
            ok, rep = cm.verify_chain(log.path); self.assertFalse(ok); self.assertEqual(rep["first_bad"], 1)
            p, heads = cm.export_anchor_manifest(d); self.assertFalse(heads["."]["chain_ok"])

    def test_seal(self):
        with tempfile.TemporaryDirectory() as d:
            cdir = cm.new_case(d, "SYN-1", {"resolved": True, "truth_e": 1, "truth_n": 2, "truth_year": 2020})
            self.assertEqual(open(os.path.join(cdir, "truth.sha256")).read().strip(), cm.seal(os.path.join(cdir, "truth.json")))


class Fall(unittest.TestCase):  # 1450
    def test_landing_downhill_and_normalised(self):
        yy, xx = np.mgrid[0:120, 0:120]; dem = -0.5 * yy.astype(float)   # slopes down toward +y
        p = fp.trajectory_landing_distribution(dem, 1.0, (60.0, 20.0), 5.0, direction_deg=90, n_mc=60, seed=1)
        self.assertAlmostEqual(p.sum(), 1.0, places=6)
        self.assertGreater(fp.ellipse_stats(p, 1.0)["centroid_m"][1], 20.0)
        self.assertIsNone(fp.recovery_percentile(p, (500, 500), 1.0))


if __name__ == "__main__":
    unittest.main()
