#!/usr/bin/env python3
"""SenseCrew forbidden-imports gate (narrow scope, adopted by Strata 2026-11-04).

Scans ONLY the SenseCrew game path: the paths of the sensegame 2300 block (registry ids
2300-2399) plus every local module they import, followed transitively. opendata/ and realdata/
are reachable only through adapters in adapter_allowlist.json (starts empty). Forbidden files
and denylisted modules are never opened; a reference to one is a hit.

Also flags:
- dynamic imports (importlib.import_module / __import__ / runpy.*) whose argument is not a
  fixed string; fixed-string args are checked against the denylist
- sys.modules lookups of denied names
- any exec / eval / compile call (fixed-string args are re-parsed and re-scanned)
- getattr on importlib, builtins or sys when the attribute name is not a fixed string
- Forbidden folder names (case, hfmr, evidence, case-files, case_files, …) anywhere inside
  string literals and paths

When a 2300-block game entry is registered, also runs a fresh-subprocess loaded-modules check
against that entry. Exit 1 on any hit, 0 if clean. --strict (or auto when a 2300-block
component exists) also fails when the game path is empty."""
import ast, json, pathlib, re, subprocess, sys, textwrap

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
REF = re.compile(
    r"[\"'][^\"']*/?(?:case|hfmr|evidence|case-files|case_files)/|"
    r"\b(?:dossier|public_records_engine|sweep_width|search_theory|optimal_search)\.py\b|"
    r"opendata[/.]fetch\b"
)
DYNAMIC_TARGETS = {"importlib.import_module", "__import__", "runpy.run_module", "runpy.run_path",
                   "import_module"}
EXEC_TARGETS = {"exec", "eval", "compile", "builtins.exec", "builtins.eval", "builtins.compile"}
GETATTR_HOSTS = {"importlib", "builtins", "sys"}


def rel(p, root):
    return p.resolve().relative_to(root.resolve()).as_posix()


def block_paths(registry, root):
    out = []
    for k, v in registry.get("components", {}).items():
        if k.isdigit() and int(k) in BLOCK and v.get("path"):
            out.append(root / "sar" / v["path"])
    return out


def should_be_strict(registry, argv):
    if "--strict" in argv:
        return True
    if "--no-strict" in argv:
        return False
    return any(k.isdigit() and int(k) in BLOCK and v.get("path")
               for k, v in registry.get("components", {}).items())


def resolve(name, level, here, roots):
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


def _call_qualname(node, aliases):
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        base = _call_qualname(node.value, aliases)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _denied_in(name):
    parts = set(name.replace("\\", "/").replace("-", "_").split(".")) | set(name.replace("\\", "/").split("."))
    bad = DENY_MODULES & parts
    for p in DENY_MODULES:
        if name == p or name.startswith(p + ".") or f"/{p}/" in f"/{name.replace(chr(92), '/')}/":
            bad.add(p)
    for folder in DENY_FOLDERS:
        if re.search(rf"(^|/)({re.escape(folder)})(/|$)", name.replace("\\", "/")):
            bad.add(folder)
    return bad


def _scan_source_snippet(src, hits, r, lineno, via):
    """Re-parse a fixed-string exec/eval/compile argument and report forbidden imports in it."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        hits.append((r, lineno, f"{via} (unparseable payload)", src[:80]))
        return
    for node in ast.walk(tree):
        mods = []
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mods = [node.module or ""] + [
                ((node.module + ".") if node.module else "") + a.name for a in node.names
            ]
        for name in mods:
            bad = _denied_in(name)
            if bad:
                hits.append((r, lineno, f"import of {sorted(bad)[0]} (via {via})", name))
        if isinstance(node, ast.Call):
            q = _call_qualname(node.func, {"__import__": "__import__"})
            if q in DYNAMIC_TARGETS or q == "__import__":
                arg = node.args[0] if node.args else None
                fixed = _const_str(arg) if arg is not None else None
                if fixed is None:
                    hits.append((r, lineno, f"dynamic import ({q}) (via {via})", "(non-literal)"))
                else:
                    bad = _denied_in(fixed)
                    if bad:
                        hits.append((r, lineno, f"import of {sorted(bad)[0]} (via {via})", fixed))


def _scan_dynamic(node, aliases, hits, r):
    if not isinstance(node, ast.Call):
        return
    q = _call_qualname(node.func, aliases)
    if q is None:
        return
    target = aliases.get(q, q)
    if target not in DYNAMIC_TARGETS and q not in DYNAMIC_TARGETS:
        return
    kind = target if target in DYNAMIC_TARGETS else q
    arg = node.args[0] if node.args else None
    fixed = _const_str(arg) if arg is not None else None
    if fixed is None:
        hits.append((r, node.lineno, f"dynamic import ({kind})",
                     ast.dump(arg) if arg else "(no arg)"))
        return
    bad = _denied_in(fixed)
    if bad:
        hits.append((r, node.lineno, f"import of {sorted(bad)[0]}", f"{kind}({fixed!r})"))


def _scan_exec_eval_compile(node, aliases, hits, r):
    if not isinstance(node, ast.Call):
        return
    q = _call_qualname(node.func, aliases)
    if q is None:
        return
    target = aliases.get(q, q)
    if target not in EXEC_TARGETS and q not in EXEC_TARGETS:
        return
    kind = target.split(".")[-1]
    arg = node.args[0] if node.args else None
    fixed = _const_str(arg) if arg is not None else None
    if fixed is None:
        hits.append((r, node.lineno, f"dynamic {kind}",
                     ast.dump(arg) if arg else "(no arg)"))
        return
    # Always a hit for exec/eval/compile on the game path; also rescan the payload.
    hits.append((r, node.lineno, f"{kind} of fixed string", fixed[:80]))
    _scan_source_snippet(fixed, hits, r, node.lineno, kind)


def _scan_getattr(node, aliases, hits, r):
    if not isinstance(node, ast.Call):
        return
    q = _call_qualname(node.func, aliases)
    if q is None:
        return
    target = aliases.get(q, q)
    if target not in ("getattr", "builtins.getattr") and q not in ("getattr", "builtins.getattr"):
        return
    if len(node.args) < 2:
        return
    host = _call_qualname(node.args[0], aliases)
    host_resolved = aliases.get(host, host) if host else None
    # Also accept Name('importlib') etc.
    if isinstance(node.args[0], ast.Name):
        host_resolved = aliases.get(node.args[0].id, node.args[0].id)
    if not host_resolved:
        return
    host_root = host_resolved.split(".")[0]
    if host_root not in GETATTR_HOSTS and host_resolved not in GETATTR_HOSTS:
        return
    attr = _const_str(node.args[1])
    if attr is None:
        hits.append((r, node.lineno, f"dynamic getattr on {host_root}",
                     ast.dump(node.args[1])))
        return
    # Fixed attr on a gated host: flag if it builds a dynamic-import entry point
    if attr in ("import_module", "__import__", "modules", "exec", "eval", "compile"):
        hits.append((r, node.lineno, f"getattr({host_root}, {attr!r})", attr))


def _scan_sys_modules(node, aliases, hits, r):
    if not isinstance(node, (ast.Subscript, ast.Call)):
        return
    if isinstance(node, ast.Subscript):
        ok = False
        if isinstance(node.value, ast.Attribute) and node.value.attr == "modules":
            if isinstance(node.value.value, ast.Name) and \
                    aliases.get(node.value.value.id, node.value.value.id) == "sys":
                ok = True
        q = _call_qualname(node.value, aliases)
        if q == "sys.modules":
            ok = True
        if not ok:
            return
        key = _const_str(node.slice)
        if key is None:
            hits.append((r, node.lineno, "dynamic sys.modules lookup", ast.dump(node.slice)))
            return
        bad = _denied_in(key)
        if bad:
            hits.append((r, node.lineno, f"sys.modules lookup of {sorted(bad)[0]}", key))
        return
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
        if not (isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "modules" and
                isinstance(node.func.value.value, ast.Name) and
                aliases.get(node.func.value.value.id, node.func.value.value.id) == "sys"):
            return
        arg = node.args[0] if node.args else None
        key = _const_str(arg) if arg is not None else None
        if key is None:
            hits.append((r, node.lineno, "dynamic sys.modules lookup", "sys.modules.get(...)"))
            return
        bad = _denied_in(key)
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
        aliases = {"__import__": "__import__", "getattr": "getattr",
                   "exec": "exec", "eval": "eval", "compile": "compile"}
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
                    (((node.module + ".") if node.module else "") + a.name, node.level)
                    for a in node.names
                ]
            for name, level in mods:
                bad = DENY_MODULES & set(name.split("."))
                if bad == {"fetch"} and name != "fetch" and "opendata" not in name:
                    pass
                elif bad:
                    hits.append((r, node.lineno, f"import of {sorted(bad)[0]}", name)); continue
                t = resolve(name, level, f, roots)
                if t:
                    queue.append(t)
            _scan_dynamic(node, aliases, hits, r)
            _scan_exec_eval_compile(node, aliases, hits, r)
            _scan_getattr(node, aliases, hits, r)
            _scan_sys_modules(node, aliases, hits, r)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value.replace("\\", "/")
                for folder in DENY_FOLDERS:
                    if re.search(rf"(^|/)({re.escape(folder)})(/|$)", s):
                        hits.append((r, getattr(node, "lineno", 0), "path reference", node.value[:120]))
                        break
                for mod in ("dossier", "public_records_engine", "sweep_width",
                            "search_theory", "optimal_search"):
                    if re.search(rf"\b{mod}\.py\b", s) or s == mod or s.startswith(mod + "."):
                        hits.append((r, getattr(node, "lineno", 0), "path reference", node.value[:120]))
                        break
    uniq, seen_h = [], set()
    for h in hits:
        key = (h[0], h[1], h[2], h[3])
        if key not in seen_h:
            seen_h.add(key); uniq.append(h)
    return uniq, files


def runtime_loaded_modules_check(entry_paths, root=ROOT, python=sys.executable):
    """Import each game entry in a fresh subprocess; fail if any denied module is loaded.
    Returns a list of hit tuples. No-op (empty) when entry_paths is empty."""
    hits = []
    denied = sorted(DENY_MODULES)
    sar = root / "sar"
    for e in entry_paths:
        # Prefer a package root under sar/ so `import sensegame` works.
        if e.is_file():
            candidates = [e]
        else:
            candidates = sorted(e.rglob("*.py"))
            # Prefer __init__.py / obvious entry names; fall back to first module.
            preferred = [c for c in candidates if c.name in ("__main__.py", "entry.py", "__init__.py")]
            candidates = preferred or candidates
            if not candidates:
                continue
            candidates = candidates[:1]
        for mod_file in candidates:
            try:
                rel_mod = mod_file.resolve().relative_to(sar.resolve())
            except ValueError:
                continue
            if rel_mod.name == "__init__.py":
                mod_name = ".".join(rel_mod.parts[:-1])
            else:
                mod_name = ".".join(rel_mod.with_suffix("").parts)
            if not mod_name:
                continue
            harness = textwrap.dedent(f"""\
                import sys, json
                sys.path.insert(0, {str(sar)!r})
                try:
                    __import__({mod_name!r})
                except Exception as exc:
                    print(json.dumps({{"error": type(exc).__name__ + ': ' + str(exc), "loaded": []}}))
                    raise SystemExit(0)
                denied = {denied!r}
                loaded = [m for m in sys.modules
                          if any(p == m or m.startswith(p + '.') for p in denied)]
                print(json.dumps({{"loaded": loaded, "error": None}}))
            """)
            r = subprocess.run([python, "-c", harness], capture_output=True, text=True, timeout=60)
            try:
                data = json.loads(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "{}")
            except (json.JSONDecodeError, IndexError):
                hits.append((rel(mod_file, root), 0, "runtime check failed",
                             (r.stderr or r.stdout or "no output")[:200]))
                continue
            for m in data.get("loaded") or []:
                hits.append((rel(mod_file, root), 0, f"runtime loaded denied module {m}", m))
    return hits


def main(argv=sys.argv[1:]):
    reg = json.loads((SAR / "registry.json").read_text())
    allow = {a["path"] for a in json.loads((ROOT / "sensecrew" / "adapter_allowlist.json").read_text())["adapters"]}
    entry = block_paths(reg, ROOT)
    hits, files = scan(entry, ROOT, allow)
    if entry:
        hits.extend(runtime_loaded_modules_check(entry, ROOT))
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
