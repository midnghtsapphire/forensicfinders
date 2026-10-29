"""Tests for the decode seam itself (sar/decode_hooks.py).

Every test here asserts observable behaviour -- a value that changed, a name in a
receipt, an exception raised. None of them assert that a string appears in a source
file, because per standards/VERIFY_THE_POSTCONDITION.md a check that a comment exists
is satisfied by the comment and proves nothing about the code.
"""
import unittest
import decode_hooks


class Seam(unittest.TestCase):
    def setUp(self):
        decode_hooks.clear()

    def tearDown(self):
        decode_hooks.clear()

    def test_identity_when_nothing_registered(self):
        payload = [1, 2, 3]
        self.assertIs(decode_hooks.apply(payload), payload)

    def test_empty_registry_does_not_touch_meta(self):
        meta = {}
        decode_hooks.apply("x", meta)
        self.assertEqual(meta, {})  # no receipt key invented when nothing ran

    def test_hook_changes_the_payload(self):
        decode_hooks.register("double", lambda p, m: [v * 2 for v in p])
        self.assertEqual(decode_hooks.apply([1, 2, 3]), [2, 4, 6])

    def test_hooks_run_in_registration_order(self):
        decode_hooks.register("add1", lambda p, m: p + 1)
        decode_hooks.register("times10", lambda p, m: p * 10)
        self.assertEqual(decode_hooks.apply(1), 20)       # (1+1)*10, not 1+10
        self.assertEqual(decode_hooks.registered(), ["add1", "times10"])

    def test_receipt_names_the_hooks_that_ran(self):
        decode_hooks.register("a", lambda p, m: p)
        decode_hooks.register("b", lambda p, m: p)
        meta = {}
        decode_hooks.apply("payload", meta)
        self.assertEqual(meta["decode_hooks_applied"], ["a", "b"])

    def test_re_registering_a_name_replaces_rather_than_doubling(self):
        calls = []
        decode_hooks.register("same", lambda p, m: calls.append(1) or p)
        decode_hooks.register("same", lambda p, m: calls.append(2) or p)
        decode_hooks.apply("x")
        self.assertEqual(calls, [2])                       # the first is gone, not stacked
        self.assertEqual(decode_hooks.registered(), ["same"])

    def test_unregister(self):
        decode_hooks.register("gone", lambda p, m: "changed")
        self.assertTrue(decode_hooks.unregister("gone"))
        self.assertFalse(decode_hooks.unregister("gone"))  # second call reports nothing removed
        self.assertEqual(decode_hooks.apply("kept"), "kept")

    def test_non_callable_is_refused_at_registration(self):
        with self.assertRaises(TypeError):
            decode_hooks.register("nope", "not a function")

    def test_failing_hook_aborts_and_names_itself(self):
        """A failed correction must not be skipped -- see apply()'s docstring for why."""
        decode_hooks.register("ok", lambda p, m: p)
        decode_hooks.register("broken", lambda p, m: 1 / 0)
        with self.assertRaises(decode_hooks.DecodeHookError) as cm:
            decode_hooks.apply([1])
        self.assertIn("broken", str(cm.exception))
        self.assertIsInstance(cm.exception.__cause__, ZeroDivisionError)

    def test_hook_may_change_shape(self):
        """Two IQ channels legitimately collapse to one power channel; don't over-constrain."""
        decode_hooks.register("collapse", lambda p, m: [p[0] + p[1]])
        self.assertEqual(decode_hooks.apply([1.0, 2.0]), [3.0])   # two channels in, one out


class Scoping(unittest.TestCase):
    """A hook written for one payload type must not be handed the others.

    This is the defect these tests exist for: before scoping, a hook expecting a numpy
    array from read_cog_window was also run over the list-of-tuples from read_points.
    """
    def setUp(self):
        decode_hooks.clear()

    def tearDown(self):
        decode_hooks.clear()

    def test_scoped_hook_runs_only_for_its_decoder(self):
        decode_hooks.register("rasters_only", lambda p, m: "TOUCHED", decoders=["read_cog_window"])
        self.assertEqual(decode_hooks.apply("x", {"decoder": "read_cog_window"}), "TOUCHED")
        self.assertEqual(decode_hooks.apply("x", {"decoder": "read_points"}), "x")
        self.assertEqual(decode_hooks.apply("x", {"decoder": "read_gpr_csv"}), "x")

    def test_unscoped_hook_still_runs_everywhere(self):
        decode_hooks.register("all", lambda p, m: "TOUCHED")
        for d in decode_hooks.KNOWN_DECODERS:
            self.assertEqual(decode_hooks.apply("x", {"decoder": d}), "TOUCHED")

    def test_receipt_only_names_hooks_that_actually_ran(self):
        decode_hooks.register("points_only", lambda p, m: p, decoders=["read_points"])
        decode_hooks.register("everywhere", lambda p, m: p)
        meta = {"decoder": "read_cog_window"}
        decode_hooks.apply("x", meta)
        self.assertEqual(meta["decode_hooks_applied"], ["everywhere"])

    def test_skipped_hook_leaves_no_receipt_at_all(self):
        decode_hooks.register("points_only", lambda p, m: p, decoders=["read_points"])
        meta = {"decoder": "read_cog_window"}
        decode_hooks.apply("x", meta)
        self.assertNotIn("decode_hooks_applied", meta)

    def test_typo_in_decoder_name_is_refused_at_registration(self):
        """A hook scoped to a misspelled decoder would never fire and never complain."""
        with self.assertRaises(ValueError) as cm:
            decode_hooks.register("oops", lambda p, m: p, decoders=["read_cog_windows"])
        self.assertIn("read_cog_windows", str(cm.exception))

    def test_registered_can_be_filtered_by_decoder(self):
        decode_hooks.register("a", lambda p, m: p, decoders=["read_points"])
        decode_hooks.register("b", lambda p, m: p, decoders=["read_cog_window"])
        decode_hooks.register("c", lambda p, m: p)
        self.assertEqual(decode_hooks.registered(), ["a", "b", "c"])
        self.assertEqual(decode_hooks.registered("read_points"), ["a", "c"])
        self.assertEqual(decode_hooks.registered("read_cog_window"), ["b", "c"])

    def test_apply_without_meta_skips_scoped_hooks(self):
        """No decoder name means no way to know scope; scoped hooks must not guess."""
        decode_hooks.register("scoped", lambda p, m: "TOUCHED", decoders=["read_points"])
        self.assertEqual(decode_hooks.apply("x"), "x")


if __name__ == "__main__":
    unittest.main()
