#!/usr/bin/env python3
"""SenseCrew forbidden-imports gate — import ALLOWLIST (Verity-N, 2026-11-04).

Scans the SenseCrew game path (registry 2300–2399) plus every local module it
imports. A module may be imported only if it is:

  * on the safe-stdlib list (below), or
  * numpy, or
  * inside the 2300 block, or
  * on the Verity adapter allowlist (sensecrew/adapter_allowlist.json).

Anything else is a hit. In addition these are ALWAYS hits, even if somehow
reachable: importlib (any submodule), pkgutil, zipimport, runpy, subprocess,
os.system / os.exec* / os.spawn* / os.popen, marshal, pickle, ctypes, code;
any use of __builtins__, builtins.*, __loader__, __spec__, __dict__, vars(),
globals(), locals(), or sys.modules; calls through names rebound to exec /
eval / compile / getattr / __import__ / open / sys.modules; open / io.open /
Path.read_* / Path.open whose path is not a plain string literal, or any path
(literal or not) that points into a forbidden directory.

Exit 1 on any hit. --strict (auto when a 2300-block component exists) also
fails when the game path is empty. When a 2300-block entry is registered,
main() also runs a fresh-subprocess loaded-modules check against DENY_MODULES.
"""
import ast, json, pathlib, re, subprocess, sys, textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
SAR = ROOT / "sar"
BLOCK = range(2300, 2400)

SAFE_STDLIB = frozenset({
    "math", "random", "json", "hashlib", "dataclasses", "typing", "itertools",
    "functools", "collections", "struct", "enum", "abc", "copy", "statistics",
    "array", "bisect", "heapq", "decimal", "fractions", "numbers", "re",
    "string", "textwrap", "os.path",
})
ALWAYS_DENY_IMPORTS = frozenset({
    "importlib", "pkgutil", "zipimport", "runpy", "subprocess",
    "marshal", "pickle", "ctypes", "code", "builtins",
})
# os itself is NOT allowlisted; only os.path. These attrs on os are always hits.
OS_DANGEROUS_ATTRS = frozenset({
    "system", "popen", "exec", "execl", "execle", "execlp", "execlpe",
    "execv", "execve", "execvp", "execvpe", "spawnl", "spawnle", "spawnlp",
    "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
})
DANGEROUS_BUILTINS = frozenset({
    "exec", "eval", "compile", "getattr", "__import__", "open",
    "vars", "globals", "locals",
})
DANGEROUS_NAMES = frozenset({
    "__builtins__", "__loader__", "__spec__", "__dict__",
})
DENY_MODULES = {
    "case", "hfmr", "evidence", "dossier", "public_records_engine", "fetch",
    "sweep_width", "search_theory", "optimal_search", "case-files", "case_files",
}
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


def _top(name):
    return name.split(".")[0] if name else ""


def _path_forbidden(s):
    s = s.replace("\\", "/")
    for folder in DENY_FOLDERS:
        if re.search(rf"(^|/)({re.escape(folder)})(/|$)", s):
            return folder
    for mod in ("dossier", "public_records_engine", "sweep_width",
                "search_theory", "optimal_search"):
        if re.search(rf"\b{mod}\.py\b", s) or s == mod or s.startswith(mod + "."):
            return mod
    return None


def _allowed_module(name, level, game_pkgs, allow_mods):
    """Return True if this absolute/relative import is on the allowlist."""
    if level and not name:
        return True  # `from . import x` — resolved locally later
    if level:
        return True  # relative; file resolve decides
    if not name:
        return False
    if name == "os.path" or name.startswith("os.path."):
        return True
    top = _top(name)
    if top in ALWAYS_DENY_IMPORTS or name.split(".")[0] in ALWAYS_DENY_IMPORTS:
        return False
    if top == "os":
        return False  # bare os / os.system etc.; only os.path is safe
    if name in SAFE_STDLIB or top in SAFE_STDLIB:
        return True
    if top == "numpy" or name.startswith("numpy."):
        return True
    if top in game_pkgs or name in game_pkgs:
        return True
    if name in allow_mods or top in allow_mods:
        return True
    return False


def _collect_aliases(tree):
    """Map local names -> what they currently refer to (best-effort, lexical)."""
    aliases = {
        "__import__": "__import__", "getattr": "getattr",
        "exec": "exec", "eval": "eval", "compile": "compile",
        "open": "open", "vars": "vars", "globals": "globals", "locals": "locals",
    }
    # First pass: imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                aliases[a.asname or a.name.split(".")[0]] = a.name
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for a in node.names:
                full = f"{mod}.{a.name}" if mod else a.name
                aliases[a.asname or a.name] = full
    # Assignments / aliases of dangerous callables and sys.modules
    dangerous_targets = DANGEROUS_BUILTINS | {"sys.modules"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            val = node.value
            src = None
            if isinstance(val, ast.Name):
                src = aliases.get(val.id, val.id)
            elif isinstance(val, ast.Attribute):
                src = _call_qualname(val, aliases)
            if src in dangerous_targets or (src and src.split(".")[-1] in DANGEROUS_BUILTINS):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        aliases[t.id] = src if src in dangerous_targets else src.split(".")[-1]
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name) and node.value.id == "__builtins__":
            for t in node.targets:
                if isinstance(t, ast.Name):
                    aliases[t.id] = "__builtins__"
    return aliases


def scan(entry, root=ROOT, allow=()):
    hits, seen, files = [], set(), []
    roots = sorted({p.parent for p in (root / "sar").glob("*/__init__.py")} | {
        root / "sar", root / "sar" / "blue-ocean-sar",
        root / "sar" / "blue-ocean-sar" / "realdata",
        root / "sar" / "blue-ocean-sar" / "opendata",
    })
    # Package names belonging to the 2300-block entry points.
    game_pkgs = set()
    for e in entry:
        try:
            r = rel(e if e.is_dir() else e.parent, root)
        except ValueError:
            continue
        parts = pathlib.PurePosixPath(r).parts
        if len(parts) >= 2 and parts[0] == "sar":
            game_pkgs.add(parts[1])
        elif parts:
            game_pkgs.add(parts[0])
    # Adapter allowlist → importable module names (stem / package under sar/).
    allow_mods = set()
    allow_set = set(allow)
    for a in allow_set:
        p = pathlib.PurePosixPath(a)
        if p.suffix == ".py":
            allow_mods.add(p.stem)
        # also allow parent package references like realdata.terrain via stem
        if "realdata" in p.parts:
            allow_mods.add(p.stem)
        if "opendata" in p.parts:
            allow_mods.add(p.stem)

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
        if r.startswith(GATED_DIRS) and r not in allow_set:
            hits.append((r, 0, "opendata/realdata module not in adapter allowlist", r)); continue
        files.append(r)
        src = f.read_text(errors="ignore")
        for n, line in enumerate(src.splitlines(), 1):
            if REF.search(line):
                hits.append((r, n, "path reference", line.strip()[:120]))
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:
            hits.append((r, exc.lineno or 0, "unparseable (cannot verify imports)", str(exc)))
            continue

        aliases = _collect_aliases(tree)

        for node in ast.walk(tree):
            # --- imports ---
            if isinstance(node, ast.Import):
                for a in node.names:
                    name = a.name
                    if _top(name) in ALWAYS_DENY_IMPORTS or name.split(".")[0] in ALWAYS_DENY_IMPORTS:
                        hits.append((r, node.lineno, f"denied import {name}", name)); continue
                    if not _allowed_module(name, 0, game_pkgs, allow_mods):
                        hits.append((r, node.lineno, f"import not on allowlist: {name}", name)); continue
                    t = resolve(name, 0, f, roots)
                    if t:
                        queue.append(t)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                level = node.level
                # from os import system / path
                if mod == "os" and level == 0:
                    for a in node.names:
                        if a.name == "path":
                            continue  # os.path allowed
                        if a.name in OS_DANGEROUS_ATTRS or a.name != "path":
                            hits.append((r, node.lineno, f"denied import os.{a.name}", f"os.{a.name}"))
                    # if ONLY path, ok; if mixed, already hit above
                    if all(a.name == "path" for a in node.names):
                        pass
                    continue
                full = mod
                if _top(full) in ALWAYS_DENY_IMPORTS or (full and full.split(".")[0] in ALWAYS_DENY_IMPORTS):
                    hits.append((r, node.lineno, f"denied import {full}", full)); continue
                if level == 0 and full and not _allowed_module(full, 0, game_pkgs, allow_mods):
                    # also check each imported name as submodule (numpy.x etc. already covered)
                    hits.append((r, node.lineno, f"import not on allowlist: {full}", full)); continue
                # follow local resolves
                for a in node.names:
                    name = f"{mod}.{a.name}" if mod else a.name
                    t = resolve(name if level == 0 else a.name, level, f, roots)
                    if t is None and level == 0 and mod:
                        t = resolve(mod, 0, f, roots)
                    if t:
                        queue.append(t)
                    elif level:
                        t = resolve(a.name, level, f, roots)
                        if t:
                            queue.append(t)

            # --- name / attribute uses that are always hits ---
            if isinstance(node, ast.Name) and node.id in DANGEROUS_NAMES:
                hits.append((r, node.lineno, f"use of {node.id}", node.id))
            if isinstance(node, ast.Attribute):
                if node.attr in ("__dict__", "__loader__", "__spec__", "__class__"):
                    # __class__ on __loader__ etc.
                    base = _call_qualname(node.value, aliases)
                    if node.attr == "__class__" and (base in ("__loader__",) or
                            (isinstance(node.value, ast.Name) and node.value.id == "__loader__")):
                        hits.append((r, node.lineno, "use of __loader__.__class__", "__loader__.__class__"))
                    elif node.attr in ("__dict__", "__loader__", "__spec__"):
                        hits.append((r, node.lineno, f"use of {node.attr}", node.attr))
                if node.attr == "__import__" or (isinstance(node.value, ast.Name) and
                        aliases.get(node.value.id) in ("builtins", "__builtins__") and
                        node.attr in DANGEROUS_BUILTINS | {"__import__"}):
                    hits.append((r, node.lineno, f"use of builtins.{node.attr}", node.attr))
                # os.system / exec* / spawn* / popen
                base = _call_qualname(node.value, aliases)
                if (base == "os" or (isinstance(node.value, ast.Name) and
                        aliases.get(node.value.id, node.value.id) == "os")) and \
                        node.attr in OS_DANGEROUS_ATTRS:
                    hits.append((r, node.lineno, f"denied os.{node.attr}", f"os.{node.attr}"))
                # sys.modules
                if node.attr == "modules" and (
                    base == "sys" or (isinstance(node.value, ast.Name) and
                                      aliases.get(node.value.id, node.value.id) == "sys")
                ):
                    hits.append((r, node.lineno, "use of sys.modules", "sys.modules"))
                # builtins.* 
                if base in ("builtins", "__builtins__") or (
                    isinstance(node.value, ast.Name) and
                    aliases.get(node.value.id) in ("builtins", "__builtins__")
                ):
                    hits.append((r, node.lineno, f"use of builtins.{node.attr}", f"builtins.{node.attr}"))

            # --- subscript: b['__import__'], vars(...)['__import__'], m['hfmr'] ---
            if isinstance(node, ast.Subscript):
                base_q = _call_qualname(node.value, aliases)
                key = _const_str(node.slice)
                # aliases pointing at __builtins__ or sys.modules
                if isinstance(node.value, ast.Name):
                    aliased = aliases.get(node.value.id, node.value.id)
                    if aliased in ("__builtins__", "builtins"):
                        hits.append((r, node.lineno, "use of __builtins__", node.value.id))
                    if aliased == "sys.modules":
                        hits.append((r, node.lineno, "use of sys.modules (alias)", node.value.id))
                        if key and _path_forbidden(key) or (key and key in DENY_MODULES):
                            hits.append((r, node.lineno, f"sys.modules lookup of {key}", key))
                if base_q in ("sys.modules",) or (
                    isinstance(node.value, ast.Attribute) and node.value.attr == "modules"
                ):
                    hits.append((r, node.lineno, "use of sys.modules", "sys.modules"))
                if isinstance(node.value, ast.Attribute) and node.value.attr == "__dict__":
                    hits.append((r, node.lineno, "use of __dict__", "__dict__"))

            # --- calls ---
            if isinstance(node, ast.Call):
                q = _call_qualname(node.func, aliases)
                target = aliases.get(q, q) if q else None
                # resolve Name through aliases
                if isinstance(node.func, ast.Name):
                    target = aliases.get(node.func.id, node.func.id)
                    q = target

                # vars / globals / locals
                if target in ("vars", "globals", "locals") or q in ("vars", "globals", "locals"):
                    hits.append((r, node.lineno, f"call to {target or q}", target or q))

                # exec / eval / compile / __import__ (direct or aliased)
                if target in ("exec", "eval", "compile", "__import__") or \
                        (q and q.split(".")[-1] in ("exec", "eval", "compile", "__import__")):
                    kind = (target or q).split(".")[-1]
                    arg = node.args[0] if node.args else None
                    fixed = _const_str(arg) if arg is not None else None
                    if fixed is None:
                        hits.append((r, node.lineno, f"dynamic {kind}",
                                     ast.dump(arg) if arg else "(no arg)"))
                    else:
                        hits.append((r, node.lineno, f"{kind} of fixed string", fixed[:80]))
                        _rescan_payload(fixed, hits, r, node.lineno, kind)

                # getattr (direct or aliased) — always hit when used on game path
                # (Verity-N: g=getattr; also getattr(importlib, nonliteral))
                if target in ("getattr", "builtins.getattr") or q in ("getattr", "builtins.getattr"):
                    hits.append((r, node.lineno, "call to getattr", "getattr"))
                    if len(node.args) >= 2 and _const_str(node.args[1]) is None:
                        hits.append((r, node.lineno, "dynamic getattr",
                                     ast.dump(node.args[1])))

                # open / io.open
                if target in ("open", "io.open") or q in ("open", "io.open") or \
                        (isinstance(node.func, ast.Attribute) and node.func.attr == "open"):
                    arg = node.args[0] if node.args else None
                    fixed = _const_str(arg) if arg is not None else None
                    if fixed is None:
                        hits.append((r, node.lineno, "open with non-literal path",
                                     ast.dump(arg) if arg else "(no arg)"))
                    else:
                        bad = _path_forbidden(fixed)
                        if bad:
                            hits.append((r, node.lineno, f"open of forbidden path ({bad})", fixed[:120]))

                # Path(...).read_text / read_bytes / open
                if isinstance(node.func, ast.Attribute) and node.func.attr in (
                        "read_text", "read_bytes", "open", "write_text", "write_bytes"):
                    # Path('x'+'y') or Path(var)
                    recv = node.func.value
                    if isinstance(recv, ast.Call):
                        rq = _call_qualname(recv.func, aliases)
                        if rq in ("Path", "pathlib.Path") or (rq and rq.endswith(".Path")):
                            parg = recv.args[0] if recv.args else None
                            fixed = _const_str(parg) if parg is not None else None
                            if fixed is None:
                                hits.append((r, node.lineno,
                                             "Path with non-literal path",
                                             ast.dump(parg) if parg else "(no arg)"))
                            else:
                                bad = _path_forbidden(fixed)
                                if bad:
                                    hits.append((r, node.lineno,
                                                 f"Path into forbidden ({bad})", fixed[:120]))

                # importlib.* / runpy / pkgutil / zipimport / subprocess calls
                if q:
                    top = _top(aliases.get(q, q))
                    if top in ALWAYS_DENY_IMPORTS or any(
                        aliases.get(q, q).startswith(d + ".") for d in ALWAYS_DENY_IMPORTS
                    ):
                        hits.append((r, node.lineno, f"call into denied module {top}", q))

            # --- string constants: forbidden folders anywhere ---
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                bad = _path_forbidden(node.value)
                if bad:
                    hits.append((r, getattr(node, "lineno", 0), "path reference", node.value[:120]))

    uniq, seen_h = [], set()
    for h in hits:
        key = (h[0], h[1], h[2], h[3])
        if key not in seen_h:
            seen_h.add(key); uniq.append(h)
    return uniq, files


def _rescan_payload(src, hits, r, lineno, via):
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
            top = _top(name)
            if top in ALWAYS_DENY_IMPORTS or top in DENY_MODULES or name in DENY_MODULES \
                    or not _allowed_module(name, 0, set(), set()):
                label = top if top in DENY_MODULES or top in ALWAYS_DENY_IMPORTS else name
                hits.append((r, lineno, f"import of {label} (via {via})", name))
        if isinstance(node, ast.Call):
            q = _call_qualname(node.func, {"__import__": "__import__"})
            if q in ("__import__", "importlib.import_module", "import_module"):
                arg = node.args[0] if node.args else None
                fixed = _const_str(arg) if arg is not None else None
                if fixed is None:
                    hits.append((r, lineno, f"dynamic import ({q}) (via {via})", "(non-literal)"))
                else:
                    hits.append((r, lineno, f"import of {_top(fixed)} (via {via})", fixed))


def runtime_loaded_modules_check(entry_paths, root=ROOT, python=sys.executable):
    """Import each game entry in a fresh subprocess; fail if a DENY_MODULES name is loaded."""
    hits = []
    denied = sorted(DENY_MODULES)
    sar = root / "sar"
    for e in entry_paths:
        if e.is_file():
            candidates = [e]
        else:
            candidates = sorted(e.rglob("*.py"))
            preferred = [c for c in candidates if c.name in ("__main__.py", "entry.py", "__init__.py")]
            candidates = (preferred or candidates)[:1]
            if not candidates:
                continue
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
    allow = {a["path"] for a in json.loads(
        (ROOT / "sensecrew" / "adapter_allowlist.json").read_text())["adapters"]}
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
