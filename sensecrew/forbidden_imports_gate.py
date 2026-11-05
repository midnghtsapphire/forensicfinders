#!/usr/bin/env python3
"""SenseCrew forbidden-imports gate (narrow scope, adopted by Strata 2026-11-04).

Scans ONLY the SenseCrew game path: the paths of the sensegame 2300 block (registry ids
2300-2399) plus every local module they import, followed transitively. opendata/ and realdata/
are reachable only through adapters in adapter_allowlist.json (starts empty). Forbidden files
and denylisted modules are never opened; a reference to one is a hit.
Exit 1 on any hit, 0 if clean. Use --strict to also fail when the game path is empty."""
import ast, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SAR = ROOT / "sar"
BLOCK = range(2300, 2400)
DENY_MODULES = {"case", "hfmr", "evidence", "dossier", "public_records_engine", "fetch",
                "sweep_width", "search_theory", "optimal_search"}
DENY_PATH = re.compile(r"(^|/)(case|hfmr|evidence)(/|$)|dossier\.py$|public_records|records_adapter|"
                       r"opendata/fetch\.py$|sweep_width|search_theory|optimal_search")
GATED_DIRS = ("sar/blue-ocean-sar/opendata/", "sar/blue-ocean-sar/realdata/")
REF = re.compile(r"[\"'](\.\./)*(case|hfmr|evidence)/|\b(dossier|public_records_engine|sweep_width|"
                 r"search_theory|optimal_search)\.py\b|opendata[/.]fetch\b")

def rel(p, root):
    return p.resolve().relative_to(root.resolve()).as_posix()

def block_paths(registry, root):
    out = []
    for k, v in registry.get("components", {}).items():
        if k.isdigit() and int(k) in BLOCK and v.get("path"):
            out.append(root / "sar" / v["path"])
    return out

def resolve(name, level, here, roots):
    """Map an import to a local .py file, or None if not local."""
    parts = name.split(".") if name else []
    bases = [here.parent] if level == 0 else [here.parents[level - 1]]
    if level == 0:
        bases += roots
    for b in bases:
        cand = b.joinpath(*parts) if parts else b
        for f in (cand.with_suffix(".py"), cand / "__init__.py"):
            if parts and f.exists():
                return f
    return None

def scan(entry, root=ROOT, allow=()):
    hits, seen, files = [], set(), []
    roots = sorted({p.parent for p in (root / "sar").glob("*/__init__.py")} | {root / "sar", root / "sar" / "blue-ocean-sar",
                    root / "sar" / "blue-ocean-sar" / "realdata", root / "sar" / "blue-ocean-sar" / "opendata"})
    queue = []
    for e in entry:
        queue += [e] if e.is_file() else sorted(e.rglob("*.py"))
    while queue:
        f = queue.pop()
        r = rel(f, root)
        if r in seen or "__pycache__" in r:
            continue
        seen.add(r)
        if DENY_PATH.search(r):
            hits.append((r, 0, "denylisted file on game path", r)); continue
        if r.startswith(GATED_DIRS) and r not in allow:
            hits.append((r, 0, "opendata/realdata module not in adapter allowlist", r)); continue
        files.append(r)
        src = f.read_text(errors="ignore")
        for n, line in enumerate(src.splitlines(), 1):
            if REF.search(line):
                hits.append((r, n, "path reference", line.strip()[:120]))
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:
            hits.append((r, exc.lineno or 0, "unparseable (cannot verify imports)", str(exc))); continue
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [(a.name, 0) for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [(node.module or "", node.level)] + [(((node.module + ".") if node.module else "") + a.name, node.level) for a in node.names]
            for name, level in mods:
                bad = DENY_MODULES & set(name.split("."))
                if bad and not (name.split(".")[-1] == "fetch" and "opendata" not in name and level == 0 and name != "fetch"):
                    hits.append((r, node.lineno, f"import of {sorted(bad)[0]}", name)); continue
                t = resolve(name, level, f, roots)
                if t:
                    queue.append(t)
    return hits, files

def main(argv=sys.argv[1:]):
    reg = json.loads((SAR / "registry.json").read_text())
    allow = {a["path"] for a in json.loads((ROOT / "sensecrew" / "adapter_allowlist.json").read_text())["adapters"]}
    entry = block_paths(reg, ROOT)
    hits, files = scan(entry, ROOT, allow)
    for r, n, why, what in hits:
        print(f"HIT {r}:{n} [{why}] {what}")
    print(f"game path: {len(entry)} sensegame 2300-block entr{'y' if len(entry)==1 else 'ies'}, {len(files)} file(s) scanned; allowlist: {len(allow)} adapter(s)")
    if not entry:
        print("WARNING: no 2300-block component registered; game path is empty (vacuous pass)")
    print(f"forbidden-imports gate: {len(hits)} hit(s)")
    return 1 if hits or ("--strict" in argv and not entry) else 0

if __name__ == "__main__":
    sys.exit(main())
