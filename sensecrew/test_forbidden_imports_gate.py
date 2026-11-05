import pathlib, sys, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import forbidden_imports_gate as g

class GateTest(unittest.TestCase):
    def _scan(self, files):
        with tempfile.TemporaryDirectory() as t:
            root = pathlib.Path(t)
            for name, body in files.items():
                p = root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(body)
            return g.scan([root], root=root)

    def test_clean(self):
        self.assertEqual(self._scan({"game/a.py": "import json\n"}), [])

    def test_hits(self):
        for src in ["from evidence import core", "import hfmr.x", "from realdata import dossier",
                    "import public_records_engine", "from opendata.fetch import x", "import sweep_width",
                    "from realdata.search_theory import p", "import optimal_search", "open('case/x')"]:
            self.assertTrue(self._scan({"game/a.py": src + "\n"}), src)

    def test_forbidden_files_not_opened(self):
        self.assertEqual(self._scan({"evidence/core.py": "import hfmr\n", "realdata/dossier.py": "import evidence\n"}), [])

if __name__ == "__main__":
    unittest.main()
