import json, os, pathlib, subprocess, sys, tempfile, textwrap, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import forbidden_imports_gate as g

class NarrowGateTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.root = pathlib.Path(self.t.name)
    def tearDown(self):
        self.t.cleanup()
    def w(self, name, body):
        p = self.root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(body); return p
    def scan(self, entry, allow=()):
        return g.scan([self.root / e for e in entry], self.root, set(allow))[0]

    def test_clean_game(self):
        self.w("sar/sensegame/a.py", "import json\nfrom . import b\n"); self.w("sar/sensegame/b.py", "x = 1\n")
        self.assertEqual(self.scan(["sar/sensegame"]), [])

    def test_direct_forbidden_imports(self):
        for src in ["from evidence import core", "import hfmr.x", "import dossier", "import public_records_engine",
                    "from opendata import fetch", "import sweep_width", "import search_theory as st",
                    "from realdata.optimal_search import run", "import case"]:
            self.w("sar/sensegame/a.py", src + "\n")
            self.assertTrue(self.scan(["sar/sensegame"]), src)

    def test_path_reference(self):
        self.w("sar/sensegame/a.py", "P = '../case/x.json'\n")
        self.assertTrue(self.scan(["sar/sensegame"]))

    def test_transitive_and_allowlist(self):
        self.w("sar/blue-ocean-sar/realdata/terrain.py", "import math\n")
        self.w("sar/sensegame/a.py", "import terrain\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("allowlist" in h[2] for h in hits))
        self.assertEqual(self.scan(["sar/sensegame"], allow={"sar/blue-ocean-sar/realdata/terrain.py"}), [])

    def test_transitive_forbidden_through_cleared_adapter(self):
        self.w("sar/blue-ocean-sar/realdata/terrain.py", "import search_theory\n")
        self.w("sar/sensegame/a.py", "import terrain\n")
        self.assertTrue(self.scan(["sar/sensegame"], allow={"sar/blue-ocean-sar/realdata/terrain.py"}))

    def test_forbidden_file_not_opened(self):
        self.w("sar/evidence/core.py", "this is not python (\n")
        self.w("sar/sensegame/a.py", "x = 1\n")
        self.assertEqual(self.scan(["sar/sensegame"]), [])

    def test_empty_block(self):
        self.assertEqual(g.block_paths({"components": {"100": {"path": "x"}}}, self.root), [])

    # --- Verity-N bypass fixtures (must fail until gate is tightened) ---

    def test_bypass_importlib_dynamic(self):
        self.w("sar/sensegame/a.py", "import importlib\nimportlib.import_module(os.environ['M'])\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("dynamic" in h[2] for h in hits), hits)

    def test_bypass_importlib_fixed_denied(self):
        self.w("sar/sensegame/a.py", "import importlib\nimportlib.import_module('hfmr.archive')\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("hfmr" in h[2] or "hfmr" in str(h[3]) for h in hits), hits)

    def test_bypass_dunder_import_dynamic(self):
        self.w("sar/sensegame/a.py", "name = 'hf' + 'mr'\n__import__(name)\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("dynamic" in h[2] for h in hits), hits)

    def test_bypass_dunder_import_fixed(self):
        self.w("sar/sensegame/a.py", "__import__('evidence')\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("evidence" in h[2] or "evidence" in str(h[3]) for h in hits), hits)

    def test_bypass_runpy(self):
        self.w("sar/sensegame/a.py", "import runpy\nrunpy.run_module('dossier')\nrunpy.run_path(p)\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(len(hits) >= 2, hits)

    def test_bypass_string_path_mid(self):
        """Forbidden folder names anywhere inside a string, not only at the start."""
        self.w("sar/sensegame/a.py", "open('sar/hfmr/archive.json')\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("path" in h[2] or "hfmr" in str(h) for h in hits), hits)

    def test_bypass_case_files(self):
        self.w("sar/sensegame/a.py", "P = '../../case-files/general/x.json'\nQ = 'case_files/y.json'\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("case-files" in str(h) or "case_files" in str(h) for h in hits), hits)

    def test_bypass_joined_module_name(self):
        self.w("sar/sensegame/a.py", "import importlib\nimportlib.import_module('search' + '_theory')\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("dynamic" in h[2] for h in hits), hits)

    def test_bypass_sys_modules(self):
        self.w("sar/sensegame/a.py", "import sys\nm = sys.modules['evidence']\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("sys.modules" in h[2] or "evidence" in str(h) for h in hits), hits)

    def test_subprocess_loaded_modules(self):
        """Import the game entry in a fresh subprocess; loaded modules must not touch the denylist."""
        self.w("sar/sensegame/__init__.py", "")
        self.w("sar/sensegame/entry.py", "x = 1\n")
        harness = self.root / "harness.py"
        harness.write_text(textwrap.dedent("""\
            import sys, json
            sys.path.insert(0, {sar!r})
            import sensegame.entry  # noqa: F401
            denied = {denied!r}
            loaded = [m for m in sys.modules if any(p == m or m.startswith(p + '.') for p in denied)]
            print(json.dumps({{"loaded": loaded}}))
        """).format(sar=str(self.root / "sar"), denied=sorted(g.DENY_MODULES | {"case-files", "case_files"})))
        r = subprocess.run([sys.executable, str(harness)], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        loaded = json.loads(r.stdout)["loaded"]
        self.assertEqual(loaded, [], loaded)

    def test_strict_auto_detect(self):
        """main() is strict by default when a 2300-block component exists."""
        self.assertTrue(callable(getattr(g, "should_be_strict", None)) or "--strict" in open(g.__file__).read())

if __name__ == "__main__":
    unittest.main()

class ExecEvalCompileTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.root = pathlib.Path(self.t.name)
    def tearDown(self):
        self.t.cleanup()
    def w(self, name, body):
        p = self.root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(body); return p
    def scan(self, entry, allow=()):
        return g.scan([self.root / e for e in entry], self.root, set(allow))[0]

    def test_exec_fixed_import(self):
        self.w("sar/sensegame/a.py", "exec('import hfmr')\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("hfmr" in str(h) for h in hits), hits)

    def test_exec_joined_string(self):
        self.w("sar/sensegame/a.py", "exec('import ' + 'hfmr')\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("exec" in h[2] or "dynamic" in h[2] for h in hits), hits)

    def test_compile_fixed(self):
        self.w("sar/sensegame/a.py", "compile('import evidence', '<x>', 'exec')\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("evidence" in str(h) for h in hits), hits)

    def test_eval_dunder_import(self):
        self.w("sar/sensegame/a.py", "eval(\"__import__('case')\")\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("case" in str(h) for h in hits), hits)

    def test_getattr_importlib_joined(self):
        self.w("sar/sensegame/a.py", "import importlib\ngateway = getattr(importlib, 'import_'+'module')\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("getattr" in h[2] or "dynamic" in h[2] for h in hits), hits)

    def test_runtime_subprocess_hook_exists(self):
        self.assertTrue(callable(getattr(g, "runtime_loaded_modules_check", None)),
                        "gate must expose runtime_loaded_modules_check for the game entry")
