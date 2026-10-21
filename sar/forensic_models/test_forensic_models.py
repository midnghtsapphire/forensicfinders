"""Tests use published worked values or closed-form checks, plus synthetic data only."""
import io, json, math, os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
from forensic_models import constants, taphonomy, gpr_dielectric as gd, gistar, soil_nitrogen, void_detector as vd, reliability, qpcr_qc


class Constants(unittest.TestCase):
    def test_every_constant_has_source(self):
        for k, v in constants.load().items():
            self.assertTrue(v["source"].strip(), k)
            if v["status"] != "user_required":
                self.assertIsNotNone(v["value"], k)
    def test_user_required_refused_without_override(self):
        with self.assertRaises(constants.MissingConstant): constants.value(constants.load(), "eps_soap")
        with self.assertRaises(ValueError): constants.load(overrides={"eps_soap": {"value": 3.0}})
        c = constants.load(overrides={"eps_soap": {"value": 3.0, "source": "lab measurement #1"}})
        self.assertEqual(constants.value(c, "eps_soap"), 3.0)


class Taphonomy(unittest.TestCase):
    def test_topp_published_anchor_and_inverse(self):
        self.assertAlmostEqual(taphonomy.topp_eps(0.0), 3.03)          # Topp (1980) inverse at theta=0
        self.assertAlmostEqual(taphonomy.topp_theta(80.0), 0.0292*80 - 0.053 - 0.00055*6400 + 0.0000043*512000, places=9)
        for th in (0.05, 0.2, 0.35):                                   # the two published polynomials agree to ~0.01
            self.assertAlmostEqual(taphonomy.topp_theta(taphonomy.topp_eps(th)), th, delta=0.015)
    def test_megyesi(self):
        add, lo, hi = taphonomy.megyesi_add(20)                        # 10^(0.002*400+1.81) = 10^2.61
        self.assertAlmostEqual(add, 10 ** 2.61, places=6); self.assertAlmostEqual(hi - add, 388.16)
        with self.assertRaises(ValueError): taphonomy.megyesi_add(40)
        self.assertEqual(taphonomy.accumulated_degree_days([10, -2, 5.5]), 15.5)
    def test_vass(self):
        p = taphonomy.vass_pmi(100, 10, 50)                            # 1285 / (0.0103*10*50)
        self.assertAlmostEqual(p, 1285 / 5.15, places=6)
        self.assertAlmostEqual(taphonomy.vass_pmi(100, 10, 50, buried=True), 4.6 * p, places=6)
    def test_saponification_needs_sourced_rate(self):
        with self.assertRaises(constants.MissingConstant): taphonomy.saponified_fraction(5)
        c = constants.load(overrides={"k_saponification": {"value": 0.1, "source": "synthetic test"}})
        self.assertAlmostEqual(taphonomy.saponified_fraction(5, c), 1 - math.exp(-0.5))


class Dielectric(unittest.TestCase):
    def test_mixing_formula_exact(self):
        e = gd.eps_eff(0.3, 0.4, eps_fat=5.5, eps_soap=3.0, eps_soil=20.0)
        self.assertAlmostEqual(e, 0.7 * (5.5 * 0.6 + 3.0 * 0.4) + 0.3 * 20.0)
        self.assertAlmostEqual(gd.gpr_velocity(e), 0.3 / math.sqrt(e))
        self.assertAlmostEqual(gd.gpr_velocity(1.0), 0.3); self.assertAlmostEqual(gd.gpr_velocity(81.0), 0.3 / 9)
    def test_soil_from_topp_and_soap_required(self):
        with self.assertRaises(constants.MissingConstant): gd.eps_eff(0.2, 0.5)
        e = gd.eps_eff(0.2, 0.0, eps_soap=1.0)
        self.assertAlmostEqual(e, 0.8 * 5.5 + 0.2 * taphonomy.topp_eps(0.2))
        self.assertAlmostEqual(gd.reflection_coefficient(4, 16), -1 / 3); self.assertAlmostEqual(gd.depth_from_twt(20, 9), 1.0)


class GiStar(unittest.TestCase):
    def test_matches_pysal_esda(self):
        try:
            import esda, libpysal
        except ImportError:
            self.skipTest("esda/libpysal not installed")
        z = vd.synthetic_dem(n=12, seed=4)
        w = libpysal.weights.lat2W(12, 12, rook=False)
        g = esda.G_Local(z.flatten(), w, star=True, transform="B", permutations=0)
        np.testing.assert_allclose(gistar.gi_star(z).flatten(), g.Zs, rtol=1e-9, atol=1e-9)
    def test_hand_example(self):
        x = np.array([[1.0, 2.0, 3.0]])                                 # n=3, every window covers ... check middle cell
        g = gistar.gi_star(x)
        self.assertAlmostEqual(g[0, 1], 0.0)                            # window = all cells -> numerator 0
        self.assertTrue(np.all(gistar.gi_star(np.ones((3, 3))) == 0))
        g = gistar.gi_star(np.array([[0.0, 0, 0, 0, 10]]))             # hand: (10-2*2)/(4*sqrt((5*2-4)/4))
        self.assertAlmostEqual(g[0, 4], 6 / (4 * math.sqrt(1.5)), places=12)


class SoilN(unittest.TestCase):
    def test_requires_sourced_rates_and_conserves_n(self):
        with self.assertRaises(constants.MissingConstant): soil_nitrogen.simulate(10, 20, 0.6, 100)
        c = constants.load(overrides={"k_ammonification": {"value": 0.2, "source": "synthetic"}, "k_nitrification": {"value": 0.05, "source": "synthetic"}})
        rows = soil_nitrogen.simulate(30, 20, 0.6, 100, consts=c)
        t, n, a, o = rows[-1]
        self.assertAlmostEqual(n + a + o, 100, places=6); self.assertAlmostEqual(t, 30, places=6)
        warm = soil_nitrogen.simulate(5, 30, 0.6, 100, consts=c)[-1][1]; cool = soil_nitrogen.simulate(5, 20, 0.6, 100, consts=c)[-1][1]
        self.assertLess(warm, cool)                                     # Q10 = 2 speeds ammonification


class VoidDetector(unittest.TestCase):
    def test_demo_finds_known_depression(self):
        cells = vd.detect(vd.detrend_plane(vd.synthetic_dem()), sign="low")
        top = cells[0]; self.assertLessEqual(abs(top["row"] - 20) + abs(top["col"] - 20), 2)
    def test_validate_and_run_on_dem_file(self):
        try: import rasterio; from rasterio.transform import from_origin
        except ImportError: self.skipTest("rasterio not installed")
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "dem.tif"); z = vd.synthetic_dem().astype("float32")
            with rasterio.open(p, "w", driver="GTiff", width=40, height=40, count=1, dtype="float32", crs="EPSG:32614", transform=from_origin(500000, 4500000, 1, 1)) as ds:
                ds.write(z, 1)
            cfg = os.path.join(d, "c.json"); json.dump({"name": "synthetic", "tiles": [{"id": "T1", "dem_path": p, "sign": "low"}]}, open(cfg, "w"))
            self.assertEqual(vd.main(["validate", cfg]), 0)
            self.assertEqual(vd.main(["run", cfg, "--out-dir", d]), 0)
            res = json.load(open(os.path.join(d, "synthetic_anomalies.json")))
            c0 = res["tiles"][0]["cells"][0]; self.assertAlmostEqual(c0["x"], 500020.5, delta=2.5); self.assertEqual(c0["crs"], "EPSG:32614")
        self.assertTrue(vd.validate({"name": "x", "tiles": [{}]}))
    def test_3dep_path_with_recorded_dtm(self):
        try: import rasterio  # noqa
        except ImportError: self.skipTest("rasterio not installed")
        import shutil
        fx = Path(__file__).resolve().parent.parent / "geo_connectors/fixtures/3dep_dtm16.tif"
        def fetch(bbox, size, out_path): shutil.copy(fx, out_path); return {"path": out_path}
        with tempfile.TemporaryDirectory() as d:
            r = vd.run_tile({"id": "NEUTRAL", "bbox": [-100.50, 41.00, -100.495, 41.005], "size": [16, 16]}, d, 1.96, fetch=fetch)
        self.assertEqual(r["basis"], "plane_detrended_residual"); self.assertTrue(all("x" in c for c in r["cells"]))
    def test_roc_from_labels(self):
        fpr, tpr, auc = vd.roc([0.9, 0.8, 0.7, 0.6], [1, 1, 0, 0]); self.assertEqual(auc, 1.0)
        _, _, auc = vd.roc([0.9, 0.8, 0.7, 0.6], [1, 0, 1, 0]); self.assertAlmostEqual(auc, 0.75)
        with self.assertRaises(ValueError): vd.roc([1, 2], [1, 1])
        self.assertNotIn("tpr = [0.0, 0.42", Path(vd.__file__).read_text())


class Reliability(unittest.TestCase):
    def test_table(self):
        self.assertEqual(reliability.grade("instrument_record", "original_file_with_hash", "documented", 2)["grade"], "A1")
        self.assertEqual(reliability.grade("instrument_record", "original_file_with_hash", "partial", 0, consistent=True)["grade"], "C3")
        self.assertEqual(reliability.grade("online_post", "anonymous", "unknown", 0)["grade"], "F6")
        self.assertEqual(reliability.grade("witness", "interviewed_on_record", "documented", 1, contradicted=True)["grade"], "C5")
        self.assertEqual(reliability.grade("news_media", "named_outlet", "documented", 1)["grade"], "C2")
    def test_unknown_inputs_raise(self):
        with self.assertRaises(KeyError): reliability.grade("tip", "x", "documented", 0)
        with self.assertRaises(KeyError): reliability.grade("witness", "secondhand", "lost", 0)


QS = """* Block Type = 96fast
* Chemistry = TAQMAN
[Results]
Well,Sample Name,Target Name,Task,CT,Quantity
A1,STD1,ASSAY,STANDARD,{s1},10000
A2,STD2,ASSAY,STANDARD,{s2},1000
A3,STD3,ASSAY,STANDARD,{s3},100
A4,STD4,ASSAY,STANDARD,{s4},10
B1,NTC1,ASSAY,NTC,Undetermined,
B2,NTC1,IPC,NTC,28.00,
B3,EB1,ASSAY,UNKNOWN,{eb},
C1,SYN-S1,IPC,UNKNOWN,28.40,
C2,SYN-S2,IPC,UNKNOWN,30.10,
"""


def synth(slope=-3.32, b=38.0, jitter=(0.0, 0.05, -0.04, 0.02), eb="Undetermined"):
    cq = [b + slope * math.log10(q) + j for q, j in zip((1e4, 1e3, 1e2, 1e1), jitter)]
    return QS.format(s1=f"{cq[0]:.3f}", s2=f"{cq[1]:.3f}", s3=f"{cq[2]:.3f}", s4=f"{cq[3]:.3f}", eb=eb)


class QPCR(unittest.TestCase):
    def test_efficiency_formula_and_pass(self):
        r = qpcr_qc.qc(qpcr_qc.read_export(synth(), "quantstudio"), "ASSAY", ipc_target="IPC")
        sc = r["standard_curve"]
        self.assertAlmostEqual(sc["efficiency"], 10 ** (-1 / sc["slope"]) - 1)
        self.assertAlmostEqual(sc["slope"], -3.32, delta=0.05); self.assertLess(sc["r2"], 1.0); self.assertGreater(sc["r2"], 0.99)
        self.assertTrue(r["pass"]); self.assertTrue(r["ntc"]["clean"]); self.assertTrue(r["extraction_blanks"]["clean"])
        ipc = {s["sample"]: s for s in r["ipc"]["samples"]}
        self.assertFalse(ipc["SYN-S1"]["inhibited"]); self.assertTrue(ipc["SYN-S2"]["inhibited"])
    def test_perfect_slope_known_value(self):
        sc = qpcr_qc.standard_curve(qpcr_qc.read_export(synth(slope=-3.3219, jitter=(0, 0, 0, 0)), "quantstudio"), "ASSAY")
        self.assertAlmostEqual(sc["efficiency"], 1.0, places=3)        # slope -3.3219 -> 100 %
    def test_failures(self):
        r = qpcr_qc.qc(qpcr_qc.read_export(synth(slope=-4.0), "quantstudio"), "ASSAY")
        self.assertFalse(r["standard_curve"]["pass"]); self.assertFalse(r["pass"])   # E = 77.8 %
        r = qpcr_qc.qc(qpcr_qc.read_export(synth(eb="33.5"), "quantstudio"), "ASSAY")
        self.assertFalse(r["extraction_blanks"]["clean"]); self.assertEqual(r["extraction_blanks"]["hits"], ["EB1"])
    def test_biorad_layout(self):
        cfx = "Well,Fluor,Target,Content,Sample,Cq,Starting Quantity (SQ)\n" + "\n".join(
            f"A{i},FAM,ASSAY,Std-0{i},STD{i},{38 - 3.32 * k:.2f},{10 ** k}" for i, k in enumerate((4, 3, 2, 1), 1)) + "\nB1,FAM,ASSAY,NTC,NTC1,,\n"
        r = qpcr_qc.qc(qpcr_qc.read_export(cfx, "biorad_cfx"), "ASSAY")
        self.assertTrue(r["standard_curve"]["pass"]); self.assertTrue(r["ntc"]["clean"])


if __name__ == "__main__":
    unittest.main()
