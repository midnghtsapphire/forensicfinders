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
        self.assertTrue(any("dynamic" in h[2] or "importlib" in str(h) for h in hits), hits)

    def test_bypass_importlib_fixed_denied(self):
        self.w("sar/sensegame/a.py", "import importlib\nimportlib.import_module('hfmr.archive')\n")
        hits = self.scan(["sar/sensegame"])
        self.assertTrue(any("hfmr" in str(h) or "importlib" in str(h) for h in hits), hits)

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
        self.assertTrue(any("dynamic" in h[2] or "importlib" in str(h) for h in hits), hits)

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

class AllowlistBypassTest(unittest.TestCase):
    """13 bypasses Verity-N found on f2ea3ed; must fail until the gate is allowlist-based."""
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.root = pathlib.Path(self.t.name)
    def tearDown(self):
        self.t.cleanup()
    def w(self, name, body):
        p = self.root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(body); return p
    def scan(self, entry="sar/sensegame"):
        return g.scan([self.root / entry], self.root, set())[0]
    def assert_hit(self, src, label):
        self.w("sar/sensegame/a.py", src if src.endswith("\n") else src + "\n")
        hits = self.scan()
        self.assertTrue(hits, f"{label}: expected hits, got none for {src!r}")

    def test_b_builtins_import(self):
        self.assert_hit("b = __builtins__; b['__import__']('hfmr')", "b=__builtins__")

    def test_builtins_dunder_import(self):
        self.assert_hit("import builtins\nbuiltins.__import__('hfmr')", "builtins.__import__")

    def test_importlib_util_spec(self):
        self.assert_hit(
            "import importlib.util\n"
            "s = importlib.util.spec_from_file_location('x', 'hfmr.py')\n"
            "m = importlib.util.module_from_spec(s); s.loader.exec_module(m)\n",
            "importlib.util spec/exec_module")

    def test_importlib_machinery_loader(self):
        self.assert_hit(
            "from importlib.machinery import SourceFileLoader\n"
            "SourceFileLoader('x', 'hfmr.py').load_module()\n",
            "importlib.machinery SourceFileLoader")

    def test_pkgutil_find_spec(self):
        self.assert_hit(
            "import pkgutil\ns = pkgutil.find_spec('hfmr'); s.loader.exec_module(__import__('types').ModuleType('x'))\n",
            "pkgutil find_spec")

    def test_loader_class(self):
        self.assert_hit("L = __loader__.__class__; L('x', 'hfmr.py').load_module()\n", "__loader__.__class__")

    def test_e_exec_alias(self):
        self.assert_hit("e = exec; e('import hfmr')\n", "e=exec")

    def test_g_getattr_alias(self):
        self.assert_hit("import importlib\ng = getattr; g(importlib, 'import_module')('hfmr')\n", "g=getattr")

    def test_vars_builtins_and_dict(self):
        self.assert_hit("vars(__builtins__)['__import__']('hfmr')\n", "vars(__builtins__)")
        self.assert_hit("import importlib\nimportlib.__dict__['import_module']('hfmr')\n", "importlib.__dict__")

    def test_m_sys_modules_alias(self):
        self.assert_hit("import sys\nm = sys.modules; m['hfmr']\n", "m=sys.modules")

    def test_open_nonliteral_path(self):
        self.assert_hit("p = 'hf' + 'mr.py'; open(p)\n", "open non-literal")
        self.assert_hit("from pathlib import Path\nPath('x' + '.bin').read_text()\n", "Path non-literal")

    def test_subprocess_or_os_system(self):
        self.assert_hit("import subprocess\nsubprocess.run(['python','-c','import hfmr'])\n", "subprocess")
        self.assert_hit("import os\nos.system('python -c \"import hfmr\"')\n", "os.system")

    def test_zipimport(self):
        self.assert_hit("import zipimport\nzipimport.zipimporter('x.zip').load_module('hfmr')\n", "zipimport")

class AllowlistTightenTest(unittest.TestCase):
    """28 Verity-N probes that got through ffce767."""
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.root = pathlib.Path(self.t.name)
    def tearDown(self):
        self.t.cleanup()
    def w(self, name, body):
        p = self.root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(body); return p
    def scan(self, src):
        self.w("sar/sensegame/a.py", src if src.endswith("\n") else src + "\n")
        return g.scan([self.root / "sar/sensegame"], self.root, set())[0]
    def assert_hit(self, src, label):
        hits = self.scan(src)
        self.assertTrue(hits, f"{label}: expected hits for {src!r}, got none")

    # --- os.path binds the name `os` ---
    def test_os_path_binds_os_system(self):
        self.assert_hit("import os.path\nos.system('x')\n", "os.path → os.system")

    def test_os_path_binds_os_environ(self):
        self.assert_hit("import os.path\nos.environ['PATH']\n", "os.path → os.environ")

    def test_os_path_binds_os_popen(self):
        self.assert_hit("import os.path\nos.popen('x')\n", "os.path → os.popen")

    def test_os_path_binds_os_execv(self):
        self.assert_hit("import os.path\nos.execv('/bin/sh', ['sh'])\n", "os.path → os.execv")

    def test_from_os_path_import_os(self):
        self.assert_hit("from os.path import os\nos.system('x')\n", "from os.path import os")

    def test_os_path_attr_ok_and_join(self):
        hits = self.scan("import os.path\np = os.path.join('a', 'b')\n")
        self.assertEqual(hits, [], hits)

    def test_os_path_getattr_system(self):
        self.assert_hit("import os.path\ngateway = getattr(os, 'system')\n", "getattr(os, system)")

    def test_os_path_partial_system(self):
        self.assert_hit("import os.path\nfrom functools import partial\npartial(os.system, 'x')\n",
                        "partial(os.system)")

    def test_os_path_decorator_wraps(self):
        self.assert_hit(
            "import os.path\nfrom functools import wraps\n"
            "def deco(f):\n"
            "    @wraps(f)\n"
            "    def inner(*a, **k):\n"
            "        os.system('x'); return f(*a, **k)\n"
            "    return inner\n",
            "decorator os.system")

    # --- numpy file I/O / ctypeslib / lib.* ---
    def test_np_fromfile(self):
        self.assert_hit("import numpy as np\nnp.fromfile('x')\n", "np.fromfile")

    def test_np_load(self):
        self.assert_hit("import numpy as np\nnp.load('x.npy')\n", "np.load")

    def test_np_loadtxt(self):
        self.assert_hit("import numpy as np\nnp.loadtxt('x')\n", "np.loadtxt")

    def test_np_genfromtxt(self):
        self.assert_hit("import numpy as np\nnp.genfromtxt('x')\n", "np.genfromtxt")

    def test_np_memmap(self):
        self.assert_hit("import numpy as np\nnp.memmap('x')\n", "np.memmap")

    def test_np_save(self):
        self.assert_hit("import numpy as np\nnp.save('x', a)\n", "np.save")

    def test_np_savez(self):
        self.assert_hit("import numpy as np\nnp.savez('x', a=a)\n", "np.savez")

    def test_np_savez_compressed(self):
        self.assert_hit("import numpy as np\nnp.savez_compressed('x', a=a)\n", "np.savez_compressed")

    def test_np_tofile(self):
        self.assert_hit("import numpy as np\na.tofile('x')\n", "ndarray.tofile")

    def test_np_DataSource(self):
        self.assert_hit("import numpy as np\nnp.DataSource()\n", "np.DataSource")

    def test_np_ctypeslib(self):
        self.assert_hit("import numpy as np\nnp.ctypeslib.as_ctypes(a)\n", "np.ctypeslib")

    def test_np_lib_format(self):
        self.assert_hit("import numpy as np\nnp.lib.format.open_memmap('x')\n", "np.lib.format")

    def test_np_lib_utils(self):
        self.assert_hit("import numpy as np\nnp.lib.utils.getlimits\n", "np.lib.utils")

    def test_np_lib_npyio(self):
        self.assert_hit("import numpy as np\nnp.lib.npyio.load('x')\n", "np.lib.npyio")

    def test_np_safe_attrs_ok(self):
        hits = self.scan("import numpy as np\na = np.zeros((2,)); b = np.stack([a]); c = np.sqrt(np.mean(a))\n")
        self.assertEqual(hits, [], hits)

    # --- dunder / help / breakpoint / input ---
    def test_dunder_mro(self):
        self.assert_hit("t = int.__mro__\n", "__mro__")

    def test_dunder_subclasses(self):
        self.assert_hit("t = int.__subclasses__()\n", "__subclasses__")

    def test_dunder_getattribute(self):
        self.assert_hit("x = object.__getattribute__\n", "__getattribute__")

    def test_help_builtin(self):
        self.assert_hit("help(json)\n", "help")

    def test_breakpoint_builtin(self):
        self.assert_hit("breakpoint()\n", "breakpoint")

    def test_input_builtin(self):
        self.assert_hit("input('x')\n", "input")

    def test_name_main_ok(self):
        hits = self.scan("if __name__ == '__main__':\n    x = 1\n")
        self.assertEqual(hits, [], hits)

    # --- scipy R34 ---
    def test_scipy_nnls_from_ok(self):
        hits = self.scan("from scipy.optimize import nnls\nnnls(A, b)\n")
        self.assertEqual(hits, [], hits)

    def test_scipy_nnls_attr_ok(self):
        hits = self.scan("import scipy.optimize\nscipy.optimize.nnls(A, b)\n")
        self.assertEqual(hits, [], hits)

    def test_scipy_other_attr_hit(self):
        self.assert_hit("from scipy.optimize import minimize\n", "scipy minimize")
        self.assert_hit("import scipy\nscipy.io.loadmat('x')\n", "scipy.io")
