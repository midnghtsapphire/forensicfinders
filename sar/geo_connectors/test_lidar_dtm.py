"""Tests for 925 lidar_dtm on a synthetic cloud with a known surface. Synthetic only, not field-validated."""
import os, tempfile, unittest
import numpy as np

try:
    import scipy  # noqa: F401
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False
try:
    import rasterio  # noqa: F401
    HAVE_RIO = True
except ImportError:
    HAVE_RIO = False

if HAVE_SCIPY:
    from geo_connectors import lidar_dtm as L


@unittest.skipUnless(HAVE_SCIPY, "scipy missing")
class Pipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xyz, t, cls.lab = L.synthetic_cloud(seed=1)
        cls.truth = staticmethod(t)

    def test_outliers_catch_noise(self):
        keep = L.remove_outliers(self.xyz)
        noise = self.lab == 7
        self.assertGreater((~keep[noise]).mean(), 0.9)     # most noise removed
        self.assertGreater(keep[self.lab == 0].mean(), 0.97)  # little ground lost

    def test_pmf_separates_ground(self):
        keep = L.remove_outliers(self.xyz)
        g = L.classify_ground_pmf(self.xyz[keep])
        lab = self.lab[keep]
        self.assertGreater(g[lab == 0].mean(), 0.9)
        self.assertLess(g[lab == 1].mean(), 0.1)
        self.assertLess(g[lab == 2].mean(), 0.05)

    def test_dtm_rmse_idw_and_tin(self):
        for method in ("idw", "tin"):
            r = L.build_dtm(self.xyz, method=method, engine="pmf")
            rmse, mx = L.rmse_vs_truth(r["dtm"], r["transform"], self.truth)
            self.assertLess(rmse, 0.15, method)
            self.assertLess(mx, 1.0, method)

    def test_filter_matters(self):
        # gridding everything (no ground filter) is much worse than the filtered DTM
        dtm, tr, _ = L.grid_dtm(self.xyz[L.remove_outliers(self.xyz)], method="idw")
        naive, _ = L.rmse_vs_truth(dtm, tr, self.truth)
        self.assertGreater(naive, 1.0)

    def test_hole_filling(self):
        g = self.xyz[self.lab == 0]
        g = g[~((g[:, 0] > 20) & (g[:, 0] < 30) & (g[:, 1] > 20) & (g[:, 1] < 30))]  # 10 m gap
        dtm, tr, holes = L.grid_dtm(g, method="idw", bounds=(0, 0, 60, 60))
        self.assertTrue(holes.any())
        self.assertTrue(np.isfinite(dtm).all())

    def test_empty_raises(self):
        with self.assertRaises(L.EmptyRaster):
            L.grid_dtm(np.zeros((2, 3)))

    def test_pdal_skips_cleanly(self):
        if L.have_pdal():
            self.skipTest("pdal installed; fallback-skip path not exercised")
        with self.assertRaises(L.MissingDependency):
            L.classify_ground_pdal(self.xyz[:10])
        _, used = L.classify_ground(self.xyz[:500], engine="auto")
        self.assertEqual(used, "numpy-pmf")

    @unittest.skipUnless(HAVE_RIO, "rasterio missing")
    def test_geotiff_written_and_validated(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "dtm.tif")
            r = L.build_dtm(self.xyz, out_path=p)
            self.assertEqual(r["raster"]["valid_frac"], 1.0)
            with self.assertRaises(L.EmptyRaster):
                L.validate_raster(os.path.join(d, "missing.tif"))
            bad = os.path.join(d, "bad.tif")
            L.write_geotiff(np.full((5, 5), np.nan), (0, 1, 5), bad)
            with self.assertRaises(L.EmptyRaster):
                L.validate_raster(bad)


if __name__ == "__main__":
    unittest.main()
