#!/usr/bin/env python3
"""SenseCrew forbidden-imports gate. Static scan of the game path (golden suite dirs) for imports
of / references to forbidden modules. Forbidden and gated files themselves are never opened.
Exit 1 on any hit, 0 if clean."""
import json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
def _mod(name):
    # import statements, attribute use (name.x), or path strings (name.py / name/)
    return (rf"^\s*(from|import)\s+[\w.]*\b{name}\b|^\s*from\s+[\w.]+\s+import\s+[^#\n]*\b{name}\b"
            rf"|\b{name}\.(py\b|[A-Za-z_])|[\'\"/.]{name}/")
TARGETS = {
    "case/": r"[\'\"]case/|\.\./case\b|^\s*(from|import)\s+(sar\.)?case\b",
    "hfmr/": _mod("hfmr"),
    "evidence": _mod("evidence"),
    "dossier": _mod("dossier"),
    "public_records_engine": _mod("public_records_engine"),
    "opendata/fetch.py": r"opendata[/.]fetch\b|^\s*from\s+\.?\s*import\s+fetch\b|^\s*import\s+fetch\b|^\s*from\s+opendata\s+import\s+[^#\n]*\bfetch\b",
    "sweep_width": _mod("sweep_width"),
    "search_theory": _mod("search_theory"),
    "optimal_search": _mod("optimal_search"),
}
# Never opened: forbidden paths plus the gated modules and their own tests.
SKIP = re.compile(r"(^|/)(case|hfmr|evidence|__pycache__)/|dossier|public_records|records_adapter|"
                  r"opendata/fetch\.py$|opendata/test_fetch\.py$|sweep_width|search_theory|optimal_search")

def game_paths(golden):
    dirs = set()
    for s in golden["suites"]:
        cwd = s["cwd"]
        if cwd == "sar":  # module-style suites: python3 -m unittest pkg.test_x / pytest dir
            for a in s["cmd"][3:]:
                if a.startswith("-"):
                    continue
                p = a.split(".")[0] if "/" not in a else a.split("/")[0]
                dirs.add(ROOT / "sar" / p) if (ROOT / "sar" / p).is_dir() else dirs.add(ROOT / "sar" / (p + ".py"))
        else:
            dirs.add(ROOT / cwd)
    return sorted(dirs)

def scan(paths, root=ROOT):
    hits = []
    for d in paths:
        files = [d] if d.is_file() else sorted(d.rglob("*.py"))
        for f in files:
            rel = f.relative_to(root).as_posix()
            if SKIP.search(rel):
                continue
            for n, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
                for name, rx in TARGETS.items():
                    if re.search(rx, line):
                        hits.append((rel, n, name, line.strip()[:120]))
    return hits

def main():
    golden = json.loads((ROOT / "sensecrew" / "golden.json").read_text())
    hits = scan(game_paths(golden))
    for rel, n, name, line in hits:
        print(f"HIT {rel}:{n} [{name}] {line}")
    print(f"forbidden-imports gate: {len(hits)} hit(s)")
    return 1 if hits else 0

if __name__ == "__main__":
    sys.exit(main())
