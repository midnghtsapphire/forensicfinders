"""Builds sensecrew/golden.json from sar/registry.json. Only lists file names; never opens forbidden files."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
SAR = ROOT / "sar"
reg = json.loads((SAR / "registry.json").read_text())["components"]
EXCL_COMPONENTS = {"110", "140", "200"}
FORBIDDEN_PARTS = ("case/", "hfmr/", "evidence/", "dossier", "public_records", "records_adapter",
                   "opendata/test_fetch.py", "sweep_width", "search_theory", "optimal_search", "realdata/test_evidence_scoring.py")
# Test classes that read case data (../../case-files/...), absent and out of scope.
OUT_OF_SCOPE_TESTS = {"realdata/test_drift_envelope.py": ["SeedCli"]}
suites = []
for k, v in reg.items():
    if "test" not in v or k in EXCL_COMPONENTS:
        continue
    s = {"id": k, "name": v["name"], "cwd": "sar/" + v["test_cwd"].rstrip("/").replace("sar/.", "sar"), "cmd": v["test"]}
    s["cwd"] = s["cwd"].rstrip("/.") if s["cwd"] != "sar/." else "sar"
    if k == "100":
        base = SAR / "blue-ocean-sar"
        mods = sorted(str(p.relative_to(base)) for p in base.rglob("test_*.py"))
        keep = [m for m in mods if not any(f in m for f in FORBIDDEN_PARTS)]
        import ast
        ids = []
        for m in keep:
            mod = m[:-3].replace("/", ".")
            if m in OUT_OF_SCOPE_TESTS:
                tree = ast.parse((base / m).read_text())
                ids += [f"{mod}.{c.name}" for c in tree.body if isinstance(c, ast.ClassDef)
                        and c.name not in OUT_OF_SCOPE_TESTS[m] and c.name.endswith(("Test", "Tests")) or
                        isinstance(c, ast.ClassDef) and c.name not in OUT_OF_SCOPE_TESTS[m] and
                        any(isinstance(b, ast.Attribute) and b.attr == "TestCase" for b in c.bases)]
            else:
                ids.append(mod)
        s["cmd"] = ["python3", "-m", "unittest"] + sorted(set(ids))
        s["excluded_test_classes"] = OUT_OF_SCOPE_TESTS
        s["excluded_tests"] = [m for m in mods if m not in keep]
        s["note"] = "Suite 100 subset; Audrey's suite 100 itself is unchanged."
    suites.append(s)
golden = {
    "name": "sensecrew-golden",
    "license": "UNLICENSED (private repo; licence pending Audrey)",
    "source": "sar/registry.json",
    "excluded_components": {"110": "evidence", "140": "public_records_engine", "200": "hfmr"},
    "forbidden_paths": ["case/", "hfmr/", "evidence/", "dossier.py", "public_records_engine.py", "public-records code"],
    "out_of_scope": [{"path": "sar/blue-ocean-sar/realdata/columbus_records.py",
                      "why": "missing; needed only by evidence.test_importers.Columbus (2 errors in suite 100)"}],
    "determinism": {
        "sensor-fusion-grid/sensor_fusion_grid.py --seed 7": "byte-identical",
        "sar-change-detection/sar_change_detection.py --seed 7": "byte-identical",
        "vision.synth_demo --seed 7 --skip-frcnn": "byte-identical",
        "blue-ocean-sar/realdata/lost_person_sim.py simulate --seed 7": "pending Bedrock's synthetic DEM",
    },
    "case_data_tests_excluded": {"realdata/test_drift_envelope.py::SeedCli": "reads ../../case-files/general/sar_case_records.json (absent; case data out of scope)"},
    "coverage_note": "Registry suite 100 discover does not descend into realdata/ (no __init__.py), so Audrey's suite 100 never ran realdata tests; golden lists them explicitly.",
    "broken_upstream": [{"path": "sar/blue-ocean-sar/realdata/test_evidence_scoring.py", "why": "SyntaxError at line 125 (method name test_CASE-X_...); excluded from golden, not edited"}],
    "suites": suites,
}
(ROOT / "sensecrew" / "golden.json").write_text(json.dumps(golden, indent=2) + "\n")
