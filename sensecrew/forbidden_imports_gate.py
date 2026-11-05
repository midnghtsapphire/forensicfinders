#!/usr/bin/env python3
"""SenseCrew forbidden-imports gate (narrow scope, adopted by Strata 2026-11-04).

Scans ONLY the SenseCrew game path: the paths of the sensegame 2300 block (registry ids
2300-2399) plus every local module they import, followed transitively. opendata/ and realdata/
are reachable only through adapters in adapter_allowlist.json (starts empty). Forbidden files
and denylisted modules are never opened; a reference to one is a hit.

Also flags dynamic imports (importlib.import_module / __import__ / runpy.*) whose argument
is not a fixed string, fixed-string dynamic imports of denied names, and sys.modules lookups
of denied names. Forbidden folder names (case, hfmr, evidence, case-files, case_files, …)
match anywhere inside string literals and paths.

Exit 1 on any hit, 0 if clean. --strict (or auto when a 2300-block component exists) also
fails when the game path is empty."""
import ast, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SAR = ROOT / "sar"
BLOCK = range(2300, 2400)
DENY_MODULES = {"case", "hfmr", "evidence", "dossier", "public_records_engine", "fetch",
                "sweep_width", "search_theory", "optimal_search", "case-files", "case_files"}
DENY_FOLDERS = ("case", "hfmr", "evidence", "case-files", "case_files")
DENY_PATH = re.compile(
    r"(^|/)(case|hfmr|evidence|case-files|case_files)(/|$)|dossier\.py$|public_records|"
    r"records_adapter|opendata/fetch\.py$|sweep_width|search_theory|optimal_search"
)
GATED_DIRS = ("sar/blue-ocean-sar/opendata/", "sar/blue-ocean-sar/realdata/")
# Forbidden folder names anywhere inside a string/path (not only at the start).
REF = re.compile(
    r"[\"'][^\"']*/?(?:case|hfmr|evidence|case-files|case_files)/|"
    r"\b(?:dossier|public_records_engine|sweep_width|search_theory|optimal_search)\.py\b|"
    r"opendata[/.]fetch\b"
)
DYNAMIC_FUNCS = {
    ("importlib", "import_module"),
    ("importlib.import_module",),  # after `from importlib import import_module` tracked via alias
    ("__", "import__"),  # placeholder; handled as Name '__import__'
}
RUNPY = {("runpy", "run_module"), ("runpy", "run_path")}

def rel(p, root):
    return p.resolve().relative_to(root.resolve()).as_posix()

def block_paths(registry, root):
    out = []
    for k, v in registry.get("components", {}).items():
        if k.isdigit() and int(k) in BLOCK and v.get("path"):
            out.append(root / "sar" / v["path"])
    return out

def should_be_strict(registry, argv):
    """Strict when --strict is passed, or auto when a 2300-block component exists."""
    if "--strict" in argv:
        return True
    if "--no-strict" in argv:
        return False
    return any(k.isdigit() and int(k) in BLOCK and v.get("path")
               for k, v in registry.get("components", {}).items())

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

def _const_str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None

def _denied_in_name(name):
    return DENY_MODULES & set(name.replace("-", "_").split(".")) | (
        DENY_MODULES & set(name.split("."))
    ) | ({p for p in DENY_MODULES if p in name.split(".") or name == p or name.startswith(p + ".")})

def _call_qualname(node, aliases):
    """Return a dotted name for Call.func if resolvable (e.g. 'importlib.import_module')."""
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        base = _call_qualname(node.value, aliases)
        return f"{base}.{node.attr}" if base else node.attr
    return None

def _scan_dynamic(node, aliases, hits, r):
    if not isinstance(node, ast.Call):
        return
    q = _call_qualname(node.func, aliases)
    if q is None:
        return
    dynamic_names = {"importlib.import_module", "__import__", "runpy.run_module", "runpy.run_path",
                     "import_module"}  # bare after `from importlib import import_module`
    # Also catch aliases that map to those.
    target = aliases.get(q, q)
    if target not in dynamic_names and q not in dynamic_names:
        return
    kind = target if target in dynamic_names else q
    arg = node.args[0] if node.args else None
    fixed = _const_str(arg) if arg is not None else None
    if fixed is None:
        hits.append((r, node.lineno, f"dynamic import ({kind})", ast.dump(arg) if arg else "(no arg)"))
        return
    bad = {p for p in DENY_MODULES if p in fixed.split(".") or fixed == p or fixed.startswith(p + ".")}
    # also catch hyphenated path forms
    for folder in DENY_FOLDERS:
        if folder in fixed.replace("\\", "/").split("/"):
            bad.add(folder)
    if bad:
        hits.append((r, node.lineno, f"import of {sorted(bad)[0]}", f"{kind}({fixed!r})"))

def _scan_sys_modules(node, aliases, hits, r):
    """Flag sys.modules['denied'] or sys.modules.get('denied', ...)."""
    if not isinstance(node, (ast.Subscript, ast.Call)):
        return
    if isinstance(node, ast.Subscript):
        q = _call_qualname(node.value, aliases)
        if q not in ("sys.modules", "modules") and aliases.get(q, q) not in ("sys.modules",):
            # allow `import sys; sys.modules[...]`
            if not (isinstance(node.value, ast.Attribute) and
                    isinstance(node.value.value, ast.Name) and
                    aliases.get(node.value.value.id, node.value.value.id) == "sys" and
                    node.value.attr == "modules"):
                return
        sl = node.slice
        key = _const_str(sl)
        if key is None:
            hits.append((r, node.lineno, "dynamic sys.modules lookup", ast.dump(sl)))
            return
        bad = {p for p in DENY_MODULES if p in key.split(".") or key == p or key.startswith(p + ".")}
        if bad:
            hits.append((r, node.lineno, f"sys.modules lookup of {sorted(bad)[0]}", key))
        return
    # sys.modules.get('denied')
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
        q = _call_qualname(node.func.value, aliases)
        if q != "sys.modules" and not (
            isinstance(node.func.value, ast.Attribute) and
            isinstance(node.func.value.value, ast.Name) and
            aliases.get(node.func.value.value.id, node.func.value.value.id) == "sys" and
            node.func.value.attr == "modules"
        ):
            return
        arg = node.args[0] if node.args else None
        key = _const_str(arg) if arg is not None else None
        if key is None:
            hits.append((r, node.lineno, "dynamic sys.modules lookup", "sys.modules.get(...)"))
            return
        bad = {p for p in DENY_MODULES if p in key.split(".") or key == p or key.startswith(p + ".")}
        if bad:
            hits.append((r, node.lineno, f"sys.modules lookup of {sorted(bad)[0]}", key))

def scan(entry, root=ROOT, allow=()):
    hits, seen, files = [], set(), []
    roots = sorted({p.parent for p in (root / "sar").glob("*/__init__.py")} | {
        root / "sar", root / "sar" / "blue-ocean-sar",
        root / "sar" / "blue-ocean-sar" / "realdata",
        root / "sar" / "blue-ocean-sar" / "opendata",
    })
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
        # Track import aliases so `import importlib as il; il.import_module(...)` resolves.
        aliases = {"__import__": "__import__"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    aliases[a.asname or a.name.split(".")[0]] = a.name
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for a in node.names:
                    full = f"{mod}.{a.name}" if mod else a.name
                    aliases[a.asname or a.name] = full
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [(a.name, 0) for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [(node.module or "", node.level)] + [
                    (((node.module + ".") if node.module else "") + a.name, node.level) for a in node.names
                ]
            for name, level in mods:
                bad = DENY_MODULES & set(name.split("."))
                # fetch is only forbidden as opendata.fetch / bare fetch used as that adapter
                if bad and not (name.split(".")[-1] == "fetch" and "opendata" not in name
                                and level == 0 and name != "fetch" and "fetch" in bad and len(bad) == 1
                                and name != "fetch"):
                    # refine: only flag fetch when it's clearly the opendata adapter
                    if bad == {"fetch"} and name != "fetch" and "opendata" not in name:
                        pass
                    else:
                        hits.append((r, node.lineno, f"import of {sorted(bad)[0]}", name)); continue
                t = resolve(name, level, f, roots)
                if t:
                    queue.append(t)
            _scan_dynamic(node, aliases, hits, r)
            _scan_sys_modules(node, aliases, hits, r)
        # Also walk string constants for mid-path folder names (ast, not just line regex).
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value.replace("\\", "/")
                for folder in DENY_FOLDERS:
                    # anywhere in the path, not only at the start
                    if re.search(rf"(^|/)({re.escape(folder)})(/|$)", s):
                        hits.append((r, getattr(node, "lineno", 0), "path reference", node.value[:120]))
                        break
                for mod in ("dossier", "public_records_engine", "sweep_width", "search_theory", "optimal_search"):
                    if re.search(rf"\b{mod}\.py\b", s) or s == mod or s.startswith(mod + "."):
                        hits.append((r, getattr(node, "lineno", 0), "path reference", node.value[:120]))
                        break
    # de-dupe hits that the line regex and the Constant walk both catch
    uniq, seen_h = [], set()
    for h in hits:
        key = (h[0], h[1], h[2], h[3])
        if key not in seen_h:
            seen_h.add(key); uniq.append(h)
    return uniq, files

def main(argv=sys.argv[1:]):
    reg = json.loads((SAR / "registry.json").read_text())
    allow = {a["path"] for a in json.loads((ROOT / "sensecrew" / "adapter_allowlist.json").read_text())["adapters"]}
    entry = block_paths(reg, ROOT)
    hits, files = scan(entry, ROOT, allow)
    for r, n, why, what in hits:
        print(f"HIT {r}:{n} [{why}] {what}")
    print(f"game path: {len(entry)} sensegame 2300-block entr{'y' if len(entry)==1 else 'ies'}, "
          f"{len(files)} file(s) scanned; allowlist: {len(allow)} adapter(s)")
    strict = should_be_strict(reg, argv)
    if not entry:
        msg = "WARNING: no 2300-block component registered; game path is empty"
        print(msg + (" (strict: fail)" if strict else " (vacuous pass)"))
    print(f"forbidden-imports gate: {len(hits)} hit(s)" + (" [strict]" if strict else ""))
    return 1 if hits or (strict and not entry) else 0

if __name__ == "__main__":
    sys.exit(main())
