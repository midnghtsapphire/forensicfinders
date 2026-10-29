"""Proves instrument_input's readers actually route through the decode seam.

These assert the returned VALUES, not that the source mentions decode_hooks: each test
registers a hook that changes the data to something the unseamed code could not return,
so removing the seam makes the assertion fail. That is the mutation test required by
standards/VERIFY_THE_POSTCONDITION.md 5.3 rule 4, built into the assertion itself.
"""
import os, tempfile, unittest
import instrument_input as ii
import decode_hooks


def _tmp(text, suffix):
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, newline="") as f:
        f.write(text)
        return f.name


class PointsSeam(unittest.TestCase):
    def setUp(self):
        decode_hooks.clear()
        self.path = _tmp("x,y,z,i\n0,0,1,5\n1,0,2,6\n", ".csv")

    def tearDown(self):
        decode_hooks.clear()
        os.unlink(self.path)

    def test_unhooked_result_is_unchanged(self):
        """The seam must be a no-op until someone opts in, or installing it broke the repo."""
        self.assertEqual(ii.read_points(self.path), [(0, 0, 1, 5), (1, 0, 2, 6)])

    def test_hook_reaches_read_points(self):
        decode_hooks.register("shift_z", lambda p, m: [(x, y, z + 100.0, i) for x, y, z, i in p])
        self.assertEqual(ii.read_points(self.path), [(0, 0, 101.0, 5), (1, 0, 102.0, 6)])

    def test_hook_runs_once_not_once_per_nested_reader(self):
        """read_points delegates to read_points_csv; seaming both would double every hook."""
        calls = []
        decode_hooks.register("count", lambda p, m: calls.append(m["decoder"]) or p)
        ii.read_points(self.path)
        self.assertEqual(calls, ["read_points"])

    def test_receipt_describes_the_decode(self):
        decode_hooks.register("noop", lambda p, m: p)
        meta = {}
        ii.read_points(self.path, meta)
        self.assertEqual(meta["decode_hooks_applied"], ["noop"])
        self.assertEqual(meta["decoder"], "read_points")
        self.assertEqual(meta["format"], "csv")
        self.assertEqual(meta["count"], 2)


class GprSeam(unittest.TestCase):
    def setUp(self):
        decode_hooks.clear()
        self.path = _tmp("1,2,3\n4,5,6\n", ".csv")

    def tearDown(self):
        decode_hooks.clear()
        os.unlink(self.path)

    def test_unhooked_result_is_unchanged(self):
        self.assertEqual(ii.read_gpr_csv(self.path), [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])

    def test_hook_reaches_read_gpr_csv(self):
        decode_hooks.register("gain", lambda p, m: [[v * 10 for v in t] for t in p])
        self.assertEqual(ii.read_gpr_csv(self.path), [[10.0, 20.0, 30.0], [40.0, 50.0, 60.0]])

    def test_ragged_file_still_rejected_before_any_hook_runs(self):
        """The file's own validity is not a hook's problem; it must fail on its own terms."""
        ragged = _tmp("1,2,3\n4,5\n", ".csv")
        decode_hooks.register("never", lambda p, m: self.fail("hook ran on an invalid file"))
        try:
            with self.assertRaises(ValueError):
                ii.read_gpr_csv(ragged)
        finally:
            os.unlink(ragged)


class ScopingEndToEnd(unittest.TestCase):
    """Scoping must hold through the real decoders, not just in decode_hooks' own tests."""
    def setUp(self):
        decode_hooks.clear()
        self.csv = _tmp("x,y,z,i\n0,0,1,5\n", ".csv")
        self.gpr = _tmp("1,2,3\n", ".csv")

    def tearDown(self):
        decode_hooks.clear()
        os.unlink(self.csv)
        os.unlink(self.gpr)

    def test_raster_hook_never_reaches_point_clouds(self):
        """The defect this guards: a numpy hook handed a list of tuples."""
        decode_hooks.register("raster", lambda p, m: self.fail("raster hook ran on points"),
                              decoders=["read_cog_window"])
        self.assertEqual(ii.read_points(self.csv), [(0, 0, 1, 5)])

    def test_point_hook_never_reaches_gpr(self):
        decode_hooks.register("points", lambda p, m: self.fail("point hook ran on GPR traces"),
                              decoders=["read_points"])
        self.assertEqual(ii.read_gpr_csv(self.gpr), [[1.0, 2.0, 3.0]])

    def test_scoped_hook_does_reach_its_own_decoder(self):
        decode_hooks.register("points", lambda p, m: [(9, 9, 9, 9)], decoders=["read_points"])
        self.assertEqual(ii.read_points(self.csv), [(9, 9, 9, 9)])


if __name__ == "__main__":
    unittest.main()
