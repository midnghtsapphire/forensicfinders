# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  forensic_pipeline/tests/test_snow_wells_pipes.py was written, committed, and never
#       executed once. Not because it failed -- because no component in registry.json
#       covered the directory it lives in, so `registry.py --test-all` never looked there.
#       Nothing in the repository could notice that. registry.json is the contract for what
#       the suite covers, and a test file outside every component's scope is a silent hole
#       in that contract: the file looks like coverage in the diff and provides none.
#       GREEN_MAIN_STANDARD.md requires a regression test with every fix, and the defect
#       being fixed is "a test file that nothing runs", so the regression test has to be a
#       check that no such file exists -- not a second test of snow_wells_pipes.
# What: NEW FILE, purely additive. Nothing else was changed by it. It reads registry.json,
#       works out which paths each component's test command would actually reach, walks
#       sar/ for test_*.py, and fails naming any file no component would run.
# Notes: Two deliberate anti-decoration properties, per RVS-VERIFY-001 ("A marker is a
#       claim. If nothing checks the claim, the marker is decoration"), section 5.3:
#       (1) An unrecognised test-command shape is a FAILURE, not a skip. If someone adds a
#           component invoked in a way this file cannot interpret, the guard says so rather
#           than quietly treating that component as covering nothing -- which would make
#           every file under it look orphaned, or worse, make this test pass while
#           understanding less of the registry than it claims to.
#       (2) Finding no test files at all is a FAILURE. A walk that silently matches nothing
#           would otherwise report success while checking nothing.
#       There is NO allowlist of permitted orphans, because as of this change there are
#       none: 71 test files, 71 covered. If an orphan is ever genuinely intended, add it
#       here with its reason the way registry.json's "deselected_tests" does -- do not
#       loosen the assertion.
#       NOT checked here, on purpose: whether a file inside a `unittest discover` component
#       actually contains a TestCase subclass. unittest collects only TestCase subclasses,
#       so a pytest-style file in a unittest component is covered by path and still
#       collects zero tests -- the companion defect, found in multi_proxy/test_engines.py.
#       That check is deliberately left out of this file because it would fail on main
#       until PR #5 lands, and shipping a knowingly-red test would violate the same
#       standard this file exists to serve. It is the obvious next guard once #5 is merged.
# ══════════════════════════════════════════════════════════════════════════════════════════
"""registry.json must account for every test file in the repository."""
import json
import os
import unittest

SAR_ROOT = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(SAR_ROOT, "registry.json")

# Flags that consume the token after them. A path-looking token that is really the value of
# one of these must not be mistaken for a test path, or the guard would believe a component
# covers a directory that does not exist and let real orphans through.
VALUE_FLAGS = frozenset({"-s", "-p", "-t", "-k", "-m", "-n", "-c", "--rootdir", "--top-level-directory",
                         "--start-directory", "--pattern", "-P"})

# Directories the walk ignores. Kept narrow on purpose: anything excluded here is a place an
# orphaned test could hide.
SKIP_DIRS = frozenset({".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"})


def _positional_paths(cmd, after):
    """Tokens in `cmd` after the token `after` that are paths, not flags or flag values."""
    out = []
    i = cmd.index(after) + 1
    while i < len(cmd):
        tok = cmd[i]
        if tok in VALUE_FLAGS:
            i += 2
            continue
        if tok.startswith("-"):
            i += 1
            continue
        out.append(tok)
        i += 1
    return out


class RegistryCoversEveryTestFile(unittest.TestCase):
    """No test_*.py may sit outside every registry component's reach."""

    @classmethod
    def setUpClass(cls):
        with open(REGISTRY, encoding="utf-8") as fh:
            cls.registry = json.load(fh)

    def _scopes(self):
        """(dirs, files) of absolute paths the registry's test commands would reach.

        Fails on a command shape it does not understand rather than ignoring it.
        """
        dirs, files = set(), set()
        for cid, comp in sorted(self.registry["components"].items()):
            cmd = comp.get("test")
            if not cmd:
                continue  # child components (e.g. 110, 901) are covered by their parent
            base = os.path.normpath(os.path.join(SAR_ROOT, comp.get("test_cwd", ".")))
            if "pytest" in cmd:
                targets = _positional_paths(cmd, "pytest")
                self.assertTrue(
                    targets,
                    f"component {cid} runs pytest with no path argument, so this guard "
                    f"cannot tell what it covers: {cmd}")
                for t in targets:
                    dirs.add(os.path.normpath(os.path.join(base, t)))
            elif "unittest" in cmd and "discover" in cmd:
                start = cmd[cmd.index("-s") + 1] if "-s" in cmd else "."
                dirs.add(os.path.normpath(os.path.join(base, start)))
            elif "unittest" in cmd:
                mods = _positional_paths(cmd, "unittest")
                self.assertTrue(
                    mods,
                    f"component {cid} runs unittest with no module argument: {cmd}")
                for m in mods:
                    rel = m.replace(".", os.sep) + ".py"
                    files.add(os.path.normpath(os.path.join(base, rel)))
            else:
                self.fail(
                    f"component {cid} has a test command this guard cannot interpret: "
                    f"{cmd}. Teach _scopes() the new shape -- do NOT delete this assertion. "
                    f"Until it is taught, every test file under that component looks "
                    f"orphaned and this guard is lying about what the suite covers.")
        return dirs, files

    def _test_files(self):
        found = []
        for root, subdirs, filenames in os.walk(SAR_ROOT):
            subdirs[:] = [d for d in subdirs if d not in SKIP_DIRS]
            for name in filenames:
                if name.startswith("test_") and name.endswith(".py"):
                    found.append(os.path.normpath(os.path.join(root, name)))
        return sorted(found)

    def test_every_test_file_is_reachable_by_some_component(self):
        dirs, files = self._scopes()
        found = self._test_files()
        # A walk that matches nothing would pass every assertion below while checking
        # nothing at all. 71 files existed when this was written; require a real floor.
        self.assertGreater(
            len(found), 50,
            f"only {len(found)} test files found under {SAR_ROOT} -- the walk is wrong, or "
            f"SKIP_DIRS is now excluding real code. This guard proves nothing until that "
            f"is explained.")
        orphans = []
        for path in found:
            if path in files:
                continue
            if any(path.startswith(d + os.sep) for d in dirs):
                continue
            orphans.append(os.path.relpath(path, SAR_ROOT).replace(os.sep, "/"))
        self.assertEqual(
            orphans, [],
            "these test files are not covered by any component in registry.json, so "
            "`registry.py --test-all` never runs them and they are not coverage no matter "
            "what they assert:\n    " + "\n    ".join(orphans) +
            "\nAdd a component for each (next free ID is the highest in registry.json "
            "rounded up -- IDs are never reused), or state the reason it is intentionally "
            "unregistered in this file's notes.")

    def test_forensic_pipeline_is_registered(self):
        """The direct regression. Before 2026-11-04 no component covered this directory."""
        dirs, _ = self._scopes()
        target = os.path.normpath(os.path.join(SAR_ROOT, "forensic_pipeline", "tests"))
        self.assertTrue(
            any(target == d or target.startswith(d + os.sep) for d in dirs),
            "no registry component covers forensic_pipeline/tests, so "
            "test_snow_wells_pipes.py does not run. This is the exact state the 2026-11-04 "
            "fix corrected; component 990 is what covers it.")

    def test_registered_test_paths_exist_on_disk(self):
        """A component pointing at a path that is gone covers nothing and must not pass."""
        dirs, files = self._scopes()
        missing = sorted(
            os.path.relpath(p, SAR_ROOT).replace(os.sep, "/")
            for p in list(dirs) + list(files)
            if not os.path.exists(p))
        self.assertEqual(
            missing, [],
            "registry.json points these test paths at things that do not exist on disk, so "
            "the components naming them run nothing: " + ", ".join(missing))


if __name__ == "__main__":
    unittest.main()
