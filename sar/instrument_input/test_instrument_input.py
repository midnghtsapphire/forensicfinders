import os, tempfile, unittest
import instrument_input as ii

class T(unittest.TestCase):
    def test_csv_roundtrip_and_header(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("x,y,z,i\n0,0,1,5\n1,0,2\n")
        try:
            self.assertEqual(ii.read_points(f.name), [(0, 0, 1, 5), (1, 0, 2, 0.0)])
        finally: os.unlink(f.name)
    def test_csv_rejects_short_rows(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f: f.write("1,2\n")
        try:
            with self.assertRaises(ValueError): ii.read_points_csv(f.name)
        finally: os.unlink(f.name)
    def test_synthetic_lidar_is_deterministic_and_shows_pit(self):
        a, b = ii.synthetic_lidar(seed=3), ii.synthetic_lidar(seed=3)
        self.assertEqual(a, b)
        g = ii.grid_min_z(ii.synthetic_lidar(n=4000, seed=1), cell_m=1.0)
        self.assertLess(g[(10, 10)], g[(10, 2)] - 0.2)
    def test_synthetic_gpr_hyperbola_apex(self):
        tr = ii.synthetic_gpr(seed=0)
        apex = [max(range(len(t)), key=t.__getitem__) for t in tr]
        self.assertEqual(min(apex), apex[20])
    def test_gpr_csv_ragged_rejected(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f: f.write("1,2,3\n1,2\n")
        try:
            with self.assertRaises(ValueError): ii.read_gpr_csv(f.name)
        finally: os.unlink(f.name)
    def test_las_without_laspy_is_explicit(self):
        try:
            import laspy  # noqa
            self.skipTest("laspy installed")
        except ImportError:
            with self.assertRaises(RuntimeError): ii.read_las("x.las")

if __name__ == "__main__": unittest.main()
