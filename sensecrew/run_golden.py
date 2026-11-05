#!/usr/bin/env python3
"""Runs every suite in sensecrew/golden.json; exit 1 if any fails."""
import json, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
fail = []
for s in json.loads((ROOT / "sensecrew" / "golden.json").read_text())["suites"]:
    r = subprocess.run(s["cmd"], cwd=ROOT / s["cwd"], capture_output=True, text=True)
    last = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()][-1:]
    print(f"[{'PASS' if r.returncode == 0 else 'FAIL'}] {s['id']} {s['name']}: {' '.join(last)}")
    if r.returncode: fail.append(s["id"]); print(r.stdout[-3000:] + r.stderr[-3000:])
print("golden suites:", "FAILED " + ",".join(fail) if fail else "all passed")
sys.exit(1 if fail else 0)
