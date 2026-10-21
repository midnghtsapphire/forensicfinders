#!/usr/bin/env python3
"""Numeric lookup for the SAR toolchain. Usage: registry.py [id] [--test] | registry.py --test-all"""
import json, subprocess, sys, unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
REG = json.loads((HERE / "registry.json").read_text())
C = REG["components"]

def run(cid):
    c = C[cid]
    if "test" not in c:
        return run(c["parent"])
    cwd = HERE / c["test_cwd"]
    if cid == "100":  # unittest discovery minus documented deselections
        suite = unittest.defaultTestLoader.discover(str(cwd), pattern="test_*.py", top_level_dir=str(cwd))
        sys.path.insert(0, str(cwd))
        def keep(s):
            out = unittest.TestSuite()
            for t in s:
                if isinstance(t, unittest.TestSuite): out.addTests(keep(t))
                elif not any(t.id().startswith(d) for d in REG["deselected_tests"]): out.addTest(t)
            return out
        import os; old = os.getcwd(); os.chdir(cwd)
        try: r = unittest.TextTestRunner(verbosity=1).run(keep(suite))
        finally: os.chdir(old)
        return 0 if r.wasSuccessful() else 1
    return subprocess.call(c["test"], cwd=cwd)

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        for k, v in C.items(): print(f"{k:>4}  {v['name']:<26} {v['what']}")
    elif a[0] == "--test-all":
        bad = [k for k in C if "test" in C[k] and run(k) != 0]
        print("FAILED:" if bad else "ALL OK", *bad); sys.exit(1 if bad else 0)
    else:
        print(json.dumps(C[a[0]], indent=2))
        if "--test" in a: sys.exit(run(a[0]))
