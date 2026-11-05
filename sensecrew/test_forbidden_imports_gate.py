import pathlib, sys, tempfile, unittest
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

if __name__ == "__main__":
    unittest.main()
