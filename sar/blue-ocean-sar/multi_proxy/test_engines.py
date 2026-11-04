# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-03
# Why:  registry.json component 100 runs `python3 -m unittest discover -s . -p test_*.py`
#       with the cwd set to blue-ocean-sar. Discovery walks into multi_proxy/, finds
#       __init__.py, and therefore imports this file as the SUBMODULE
#       `multi_proxy.test_engines`, not as a top-level script. Inside a package, a flat
#       `from dielectric import ...` is an absolute import of a top-level module named
#       `dielectric`, which does not exist -- the siblings live at `multi_proxy.dielectric`.
#       So every run of the fleet suite ended in:
#           ERROR: multi_proxy.test_engines (unittest.loader._FailedTest...)
#           ModuleNotFoundError: No module named 'dielectric'
#       and `python3 sar/registry.py --test-all` reported FAILED: 100. Per
#       revvel-standards/standards/GREEN_MAIN_STANDARD.md a red main is a fleet emergency
#       that outranks feature work, so this is its own one-fix PR.
# What: The four intra-package imports on lines 2-5 are now explicit relative imports
#       (`from .dielectric import ...`). The originals are preserved verbatim in the
#       REVVEL-DISABLED block below, per RVS-AGENT-001 (COMMENT-DONT-DELETE) -- nothing
#       was removed. No test body, assertion or numeric tolerance was touched.
# What Worked: `from .x import y` rather than `from multi_proxy.x import y`. Relative form
#       keeps working if the package is ever vendored or renamed, and it is what the rest
#       of this repository uses for intra-package imports.
# Notes: The flat form DOES work if you run the file directly from inside multi_proxy/
#       (`cd multi_proxy && python3 -m pytest test_engines.py`), because then the package
#       directory itself is sys.path[0]. That is almost certainly how it was verified when
#       it was written, and it is why the breakage was invisible locally but fatal under
#       the registry's discovery. test_package_imports.py in this directory now asserts the
#       discovery-shaped behaviour so the class of mistake cannot come back silently.
#       See also: the identical pattern must NOT be introduced in data_fetcher.py, loader.py,
#       consensus.py, twi.py, sam.py, nnls_unmix.py or dielectric.py -- as of this change
#       none of them import a sibling at all (checked, every one imports only numpy/scipy).
# ══════════════════════════════════════════════════════════════════════════════════════════
import numpy as np

# REVVEL-DISABLED | AGENT: claude-code | MODEL: claude-opus-5 | WR: UNASSIGNED | DATE: 2026-11-03 | STATUS: REPLACED
# REASON: flat intra-package imports. Under `unittest discover` this file is imported as
#         `multi_proxy.test_engines`, so these four lines resolve as ABSOLUTE imports of
#         top-level modules that do not exist, and the whole component-100 suite errored
#         with ModuleNotFoundError. Replaced by the explicit relative imports below; the
#         names bound and the symbols used are identical, so no test behaviour changes.
# PREVIOUS IMPORTS, kept verbatim:
# from dielectric import topp_dielectric
# from twi import calculate_twi
# from consensus import multiplicative_consensus
# from nnls_unmix import constrained_nnls_unmix
# OWNER: @midnghtsapphire
# REVVEL-DISABLED-END
from .dielectric import topp_dielectric
from .twi import calculate_twi
from .consensus import multiplicative_consensus
from .nnls_unmix import constrained_nnls_unmix

def test_topp():
    m = np.array([0.0, 0.2, 0.4])
    d = topp_dielectric(m)
    assert d[0] == 3.03
    assert d[1] > d[0]

def test_twi_shape():
    dem = np.random.rand(10, 10) * 10
    twi = calculate_twi(dem)
    assert twi.shape == dem.shape

def test_nnls_and_consensus():
    em = {
        "a": np.array([1.0, 0.0]),
        "b": np.array([0.0, 1.0]),
    }
    spec = np.zeros((2, 2, 2))
    spec[0, 0] = em["a"]
    fracs, rms = constrained_nnls_unmix(spec, em)
    assert fracs["a"][0, 0] > 0.9
    assert rms[0, 0] < 1e-6
    cons = multiplicative_consensus(fracs["a"], 1.0 - rms)
    assert cons.shape == (2, 2)


# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-03
# Why:  The three functions above are written pytest-style -- bare `test_*` functions with
#       plain `assert`. registry.json component 100 runs `unittest discover`, and unittest
#       collects ONLY unittest.TestCase subclasses. It never collects bare functions.
#       Measured on this file: 0 tests collected. So fixing the import error on its own
#       would have swapped a loud ERROR for silent zero coverage -- main would read green
#       while topp_dielectric, calculate_twi, constrained_nnls_unmix and
#       multiplicative_consensus went on having no executed test at all. GREEN_MAIN_STANDARD.md
#       forbids weakening a gate, and quietly dropping three assertions out of the suite is
#       weakening it, so the adapter below is part of the same fix rather than a follow-up.
# What: ADDITIVE ONLY. The three functions above are untouched and still work unchanged
#       under pytest (`cd sar/blue-ocean-sar && python3 -m pytest multi_proxy/`). This
#       TestCase simply calls them, so the same assertions now also execute under the
#       registry's unittest runner. Component 100 goes from 0 to 3 real multi_proxy tests.
# Notes: Deliberately a thin adapter rather than a rewrite of the three functions into
#       methods. Rewriting them would mean deleting the pytest-style originals, which
#       RVS-AGENT-001 forbids, and would break anyone running pytest on this package.
#       If a fourth test function is added above, add one line here too -- or the new test
#       silently will not run under component 100. There is no mechanism that catches that
#       for you; this comment is the only reminder.
# ══════════════════════════════════════════════════════════════════════════════════════════
import unittest


class MultiProxyEngines(unittest.TestCase):
    """unittest adapter so the pytest-style functions above run under component 100."""

    def test_topp(self):
        test_topp()

    def test_twi_shape(self):
        test_twi_shape()

    def test_nnls_and_consensus(self):
        test_nnls_and_consensus()


if __name__ == "__main__":
    unittest.main()
