# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-03
# Why:  test_engines.py shipped with flat intra-package imports (`from dielectric import
#       ...`). That form works when you run the file from inside this directory, and fails
#       when registry.json component 100 imports it as `multi_proxy.test_engines` under
#       `unittest discover`. The whole 412-test fleet suite errored on it and nobody saw,
#       because the only place it was ever exercised was the directory where it happens to
#       work. revvel-standards/standards/GREEN_MAIN_STANDARD.md requires a regression test
#       with every fix, and RVS-VERIFY-001 is blunt about what that test has to be:
#       "A marker is a claim. If nothing checks the claim, the marker is decoration."
# What: NEW FILE, purely additive. Nothing else in this package was touched by it.
#       It asserts the BEHAVIOUR that broke -- that each module here imports successfully
#       under its real package name -- rather than grepping the source for a leading dot.
#       A source grep would pass the moment someone wrote `from multi_proxy.x import y`
#       (also correct) and would be fooled by the string appearing in a comment; an import
#       either resolves or it does not.
# Notes: A missing THIRD-PARTY dependency (numpy, scipy) is a skip, because that is an
#       environment fact and not a defect in this package. A missing SIBLING is always a
#       failure, because that is exactly the bug. The distinction is what stops this guard
#       from quietly turning into a no-op on a bare runner -- see the pip list in
#       sar/Dockerfile.tests and sar/docs/SELF_HOSTED_CI.md.
#       Mutation-tested: reverting line 2 of test_engines.py to its flat form makes
#       test_test_engines_imports_under_its_package_name fail with the sibling message, and
#       restoring it makes both tests pass again. Verified 2026-11-03 on Python 3.14.3.
# ══════════════════════════════════════════════════════════════════════════════════════════
import importlib
import pkgutil
import unittest

# Third-party distributions this package legitimately depends on. A ModuleNotFoundError
# naming one of these means "not installed here", which is a skip. Anything else that is a
# sibling of this file means "written as a top-level import by mistake", which is the bug.
THIRD_PARTY = frozenset({"numpy", "scipy", "seamless_3dep", "rasterio", "laspy"})


class PackageRelativeImports(unittest.TestCase):
    """Every module in multi_proxy must import under its package name, not just when cd'd here."""

    def _package(self):
        # __package__ is "multi_proxy" when this file is imported the way component 100
        # imports it. It is "" when the file was loaded as a flat top-level script, which
        # is the very situation that hid the original bug -- so that is a failure, not a
        # skip. Do not soften this into skipTest: a guard that excuses itself under the
        # conditions it exists to detect is decoration (RVS-VERIFY-001 section 5.3).
        pkg_name = __package__ or ""
        self.assertEqual(
            pkg_name,
            "multi_proxy",
            "this test module was imported flat (__package__ is empty), so it cannot check "
            "package-relative imports. Run it the way registry.json component 100 does: "
            "cd sar/blue-ocean-sar && python3 -m unittest discover -s . -p 'test_*.py'",
        )
        return importlib.import_module(pkg_name)

    def _import_or_skip_on_third_party(self, dotted, siblings):
        """Import `dotted`; skip only if a genuine third-party distribution is absent."""
        try:
            return importlib.import_module(dotted)
        except ModuleNotFoundError as exc:
            missing = (exc.name or "").split(".")[0]
            self.assertNotIn(
                missing,
                siblings,
                f"{dotted} imports its sibling {missing!r} as a TOP-LEVEL module. Inside a "
                f"package that is an absolute import of a module that does not exist, so "
                f"`unittest discover` errors on the whole component. Write "
                f"`from .{missing} import ...` instead.",
            )
            if missing in THIRD_PARTY:
                self.skipTest(f"third-party dependency {missing!r} is not installed")
            raise

    def _siblings(self, pkg):
        return frozenset(m.name for m in pkgutil.iter_modules(pkg.__path__))

    def test_test_engines_imports_under_its_package_name(self):
        # The direct regression. Before the 2026-11-03 fix this raised
        # ModuleNotFoundError: No module named 'dielectric'.
        pkg = self._package()
        siblings = self._siblings(pkg)
        self.assertIn(
            "test_engines",
            siblings,
            "test_engines.py has gone missing from multi_proxy/ -- this guard now proves "
            "nothing. Find out where it went before changing this assertion.",
        )
        mod = self._import_or_skip_on_third_party("multi_proxy.test_engines", siblings)
        # Assert the names the test functions actually call are bound, not merely that the
        # import statement ran. A partially-shadowed import would otherwise slip through.
        for symbol in ("topp_dielectric", "calculate_twi",
                       "multiplicative_consensus", "constrained_nnls_unmix"):
            self.assertTrue(
                hasattr(mod, symbol),
                f"multi_proxy.test_engines imported, but {symbol!r} is not bound in it",
            )

    def test_no_module_imports_a_sibling_as_top_level(self):
        # The generalisation: the same mistake anywhere else in the package fails here too,
        # including in modules added after this file was written.
        pkg = self._package()
        siblings = self._siblings(pkg)
        imported = 0
        for name in sorted(siblings):
            if name == "test_package_imports":
                continue  # already in sys.modules; importing self proves nothing
            with self.subTest(module=name):
                # A skip raises out of the helper, so `imported` is only bumped on a real
                # successful import. subTest records the skip and the loop carries on.
                self._import_or_skip_on_third_party(f"multi_proxy.{name}", siblings)
                imported += 1
        # If every module skipped, this test passed without checking anything. Say so.
        self.assertGreater(
            imported,
            0,
            "no module in multi_proxy could be imported, so nothing was checked. Install "
            "numpy and scipy (see sar/Dockerfile.tests) and run this again.",
        )


if __name__ == "__main__":
    unittest.main()
