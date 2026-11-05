#!/usr/bin/env python3
"""SenseCrew forbidden-imports gate — import ALLOWLIST (Verity-N, 2026-11-04).

Game-path imports are allowlisted: safe stdlib, numpy (explicit attrs only),
scipy.optimize.nnls (R34), the 2300 block, and Verity adapters. See module
constants for the always-deny set, dunder rules, and os.path binding rules.
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
OS_DANGEROUS_ATTRS = frozenset({
    "system", "popen", "exec", "execl", "execle", "execlp", "execlpe",
    "execv", "execve", "execvp", "execvpe", "spawnl", "spawnle", "spawnlp",
    "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
})
# numpy: only these attributes (and np.linalg.*, np.random.default_rng) are allowed.
NUMPY_OK_ATTRS = frozenset({
    # array creation / shape
    "array", "asarray", "ascontiguousarray", "asfortranarray", "asanyarray",
    "empty", "empty_like", "zeros", "zeros_like", "ones", "ones_like",
    "full", "full_like", "eye", "identity", "arange", "linspace", "logspace",
    "geomspace", "meshgrid", "stack", "vstack", "hstack", "dstack",
    "concatenate", "column_stack", "row_stack", "split", "array_split",
    "tile", "repeat", "broadcast_to", "reshape", "ravel", "transpose",
    "moveaxis", "swapaxes", "expand_dims", "squeeze", "atleast_1d",
    "atleast_2d", "atleast_3d", "ndarray", "ndindex", "ndim", "shape", "size",
    # math / reductions
    "sqrt", "cbrt", "square", "power", "reciprocal", "abs", "absolute", "fabs",
    "sign", "clip", "round", "around", "floor", "ceil", "trunc",
    "exp", "expm1", "log", "log10", "log2", "log1p",
    "sin", "cos", "tan", "arcsin", "arccos", "arctan", "arctan2",
    "sinh", "cosh", "tanh", "arcsinh", "arccosh", "arctanh",
    "mean", "sum", "prod", "min", "max", "amin", "amax", "ptp",
    "std", "var", "median", "percentile", "quantile",
    "nanmean", "nansum", "nanstd", "nanvar", "nanmin", "nanmax", "nanmedian",
    "where", "maximum", "minimum", "fmax", "fmin", "nan_to_num",
    "all", "any", "argmax", "argmin", "argsort", "sort", "unique",
    "isnan", "isfinite", "isinf", "isclose", "allclose", "copy", "copyto",
    "dot", "matmul", "inner", "outer", "tensordot", "einsum", "cross", "vdot",
    # dtypes
    "dtype", "float16", "float32", "float64", "int8", "int16", "int32", "int64",
    "uint8", "uint16", "uint32", "uint64", "bool_", "bool8", "complex64",
    "complex128", "finfo", "iinfo", "promote_types", "can_cast", "result_type",
    "int_", "float_", "complex_", "number", "integer", "floating", "inexact",
    # submodules we permit selective use of
    "linalg", "random",
})
NUMPY_LINALG_OK = frozenset({
    "inv", "solve", "lstsq", "svd", "eig", "eigh", "eigvals", "eigvalsh",
    "det", "matrix_rank", "norm", "pinv", "cholesky", "qr", "multi_dot",
})
NUMPY_DENY_ATTRS = frozenset({
    "fromfile", "load", "loadtxt", "genfromtxt", "memmap",
    "save", "savez", "savez_compressed", "tofile", "DataSource",
    "ctypeslib",
})
NUMPY_DENY_LIB = frozenset({"format", "utils", "npyio"})
DANGEROUS_BUILTINS = frozenset({
    "exec", "eval", "compile", "getattr", "__import__", "open",
    "vars", "globals", "locals", "help", "breakpoint", "input",
})
DANGEROUS_NAMES = frozenset({
    "__builtins__", "__loader__", "__spec__", "__dict__",
})
DUNDER_ALLOW = frozenset({"__name__", "__init__"})
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
    if level:
        return True
    if not name:
        return False
    if name == "os.path" or name.startswith("os.path."):
        return True
    # R34: scipy.optimize (nnls only — attribute use checked separately)
    if name in ("scipy", "scipy.optimize") or name.startswith("scipy.optimize."):
        return True
    if name.startswith("scipy.") and not name.startswith("scipy.optimize"):
        return False
    top = _top(name)
    if top in ALWAYS_DENY_IMPORTS:
        return False
    if top == "os":
        return False
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
    aliases = {
        "__import__": "__import__", "getattr": "getattr",
        "exec": "exec", "eval": "eval", "compile": "compile",
        "open": "open", "vars": "vars", "globals": "globals", "locals": "locals",
        "help": "help", "breakpoint": "breakpoint", "input": "input",
    }
    for node in tree.body if isinstance(tree, ast.Module) else ast.walk(tree):
        pass
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                bound = a.asname or a.name.split(".")[0]
                # `import os.path` binds the name `os` to the whole os module.
                if a.name == "os.path" or a.name.startswith("os.path."):
                    if a.asname:
                        aliases[a.asname] = "os.path"
                    else:
                        aliases["os"] = "os"
                elif a.name == "numpy" or a.name.startswith("numpy."):
                    aliases[bound] = a.name if a.asname else "numpy"
                    if not a.asname:
                        aliases["numpy"] = "numpy"
                elif a.name.startswith("scipy"):
                    # `import scipy.optimize` binds the name `scipy` to the scipy package.
                    if a.asname:
                        aliases[a.asname] = a.name
                    else:
                        aliases["scipy"] = "scipy"
                else:
                    aliases[bound] = a.name
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for a in node.names:
                full = f"{mod}.{a.name}" if mod else a.name
                aliases[a.asname or a.name] = full
                # `from os.path import os` hands out the whole os module.
                if mod in ("os.path", "os") and a.name == "os":
                    aliases[a.asname or "os"] = "os"
    dangerous_targets = DANGEROUS_BUILTINS | {"sys.modules", "os"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            val = node.value
            src = None
            if isinstance(val, ast.Name):
                src = aliases.get(val.id, val.id)
            elif isinstance(val, ast.Attribute):
                src = _call_qualname(val, aliases)
            if src and (src in dangerous_targets or src.split(".")[-1] in DANGEROUS_BUILTINS
                        or src == "os" or src.startswith("os.")):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        aliases[t.id] = src if src in dangerous_targets or src == "os" else src.split(".")[-1]
            if isinstance(val, ast.Name) and val.id == "__builtins__":
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        aliases[t.id] = "__builtins__"
    return aliases


def _numpy_root(q, aliases):
    """Return True if qualname is numpy / np / alias thereof (the module root)."""
    if not q:
        return False
    root = aliases.get(q, q)
    return root in ("numpy", "np") or q in ("numpy", "np") or _top(root) == "numpy"


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


def scan(entry, root=ROOT, allow=()):
    hits, seen, files = [], set(), []
    roots = sorted({p.parent for p in (root / "sar").glob("*/__init__.py")} | {
        root / "sar", root / "sar" / "blue-ocean-sar",
        root / "sar" / "blue-ocean-sar" / "realdata",
        root / "sar" / "blue-ocean-sar" / "opendata",
    })
    game_pkgs = set()
    for e in entry:
        try:
            rr = rel(e if e.is_dir() else e.parent, root)
        except ValueError:
            continue
        parts = pathlib.PurePosixPath(rr).parts
        if len(parts) >= 2 and parts[0] == "sar":
            game_pkgs.add(parts[1])
        elif parts:
            game_pkgs.add(parts[0])
    allow_mods = set()
    allow_set = set(allow)
    for a in allow_set:
        p = pathlib.PurePosixPath(a)
        if p.suffix == ".py":
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
            if isinstance(node, ast.Import):
                for a in node.names:
                    name = a.name
                    if _top(name) in ALWAYS_DENY_IMPORTS:
                        hits.append((r, node.lineno, f"denied import {name}", name)); continue
                    if name.startswith("scipy.") and not (
                        name == "scipy.optimize" or name.startswith("scipy.optimize.")
                    ):
                        hits.append((r, node.lineno, f"scipy not nnls: {name}", name)); continue
                    if not _allowed_module(name, 0, game_pkgs, allow_mods):
                        hits.append((r, node.lineno, f"import not on allowlist: {name}", name)); continue
                    t = resolve(name, 0, f, roots)
                    if t:
                        queue.append(t)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                level = node.level
                if mod == "os" and level == 0:
                    for a in node.names:
                        if a.name != "path":
                            hits.append((r, node.lineno, f"denied import os.{a.name}", f"os.{a.name}"))
                    continue
                if mod == "os.path" and level == 0:
                    for a in node.names:
                        if a.name == "os":
                            hits.append((r, node.lineno, "from os.path import os", "os"))
                    # other names like join/basename are fine (os.path.*)
                    continue
                # R34: from scipy.optimize import nnls only
                if mod == "scipy.optimize" and level == 0:
                    for a in node.names:
                        if a.name != "nnls":
                            hits.append((r, node.lineno,
                                         f"scipy.optimize.{a.name} not allowed (R34)", a.name))
                    continue
                if mod == "scipy" or (mod and mod.startswith("scipy.") and
                                      mod != "scipy.optimize" and
                                      not mod.startswith("scipy.optimize.")):
                    hits.append((r, node.lineno, f"scipy not nnls: {mod}", mod)); continue
                if _top(mod) in ALWAYS_DENY_IMPORTS:
                    hits.append((r, node.lineno, f"denied import {mod}", mod)); continue
                if level == 0 and mod and not _allowed_module(mod, 0, game_pkgs, allow_mods):
                    hits.append((r, node.lineno, f"import not on allowlist: {mod}", mod)); continue
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

            # Names
            if isinstance(node, ast.Name) and node.id in DANGEROUS_NAMES:
                hits.append((r, node.lineno, f"use of {node.id}", node.id))

            # Attributes
            if isinstance(node, ast.Attribute):
                attr = node.attr
                base_q = _call_qualname(node.value, aliases)

                # dunder: flag all except __name__/__init__
                if attr.startswith("__") and attr.endswith("__") and attr not in DUNDER_ALLOW:
                    hits.append((r, node.lineno, f"dunder attribute {attr}", attr))

                # os.* — only os.path.* is allowed
                resolved_base = None
                if isinstance(node.value, ast.Name):
                    resolved_base = aliases.get(node.value.id, node.value.id)
                elif base_q:
                    resolved_base = aliases.get(base_q, base_q)
                if resolved_base == "os" or base_q == "os":
                    if attr != "path":
                        hits.append((r, node.lineno, f"denied os.{attr}", f"os.{attr}"))
                # os.path is fine; deeper os.path.* fine; but os.X via Attribute chain
                # already handled. Flag os.path.os if it appears.
                if (resolved_base == "os.path" or base_q == "os.path") and attr == "os":
                    hits.append((r, node.lineno, "os.path.os", "os.path.os"))

                # numpy attribute policy
                if isinstance(node.value, ast.Name) and \
                        aliases.get(node.value.id, node.value.id) in ("numpy", "np"):
                    if attr in NUMPY_DENY_ATTRS:
                        hits.append((r, node.lineno, f"denied numpy.{attr}", f"numpy.{attr}"))
                    elif attr == "lib":
                        hits.append((r, node.lineno, "denied numpy.lib", "numpy.lib"))
                    elif attr not in NUMPY_OK_ATTRS:
                        hits.append((r, node.lineno, f"numpy attr not allowlisted: {attr}", attr))
                # np.linalg.X
                if isinstance(node.value, ast.Attribute) and node.value.attr == "linalg":
                    root_v = node.value.value
                    if isinstance(root_v, ast.Name) and \
                            aliases.get(root_v.id, root_v.id) in ("numpy", "np"):
                        if attr not in NUMPY_LINALG_OK:
                            hits.append((r, node.lineno, f"numpy.linalg.{attr} not allowlisted", attr))
                # np.random — only default_rng
                if isinstance(node.value, ast.Attribute) and node.value.attr == "random":
                    root_v = node.value.value
                    if isinstance(root_v, ast.Name) and \
                            aliases.get(root_v.id, root_v.id) in ("numpy", "np"):
                        if attr != "default_rng":
                            hits.append((r, node.lineno, f"numpy.random.{attr} not allowlisted", attr))
                # np.lib.*
                if isinstance(node.value, ast.Attribute) and node.value.attr == "lib":
                    root_v = node.value.value
                    if isinstance(root_v, ast.Name) and \
                            aliases.get(root_v.id, root_v.id) in ("numpy", "np"):
                        hits.append((r, node.lineno, f"denied numpy.lib.{attr}", attr))
                # ndarray.tofile (any .tofile)
                if attr == "tofile":
                    hits.append((r, node.lineno, "denied *.tofile", "tofile"))
                # np.ctypeslib already denied via attr; also flag as Attribute chain
                if attr == "ctypeslib":
                    hits.append((r, node.lineno, "denied numpy.ctypeslib", "ctypeslib"))

                # scipy — only .optimize.nnls (R34)
                if isinstance(node.value, ast.Name) and \
                        aliases.get(node.value.id, node.value.id) in ("scipy",):
                    if attr != "optimize":
                        hits.append((r, node.lineno, f"scipy.{attr} not allowed (R34)", attr))
                if isinstance(node.value, ast.Attribute) and node.value.attr == "optimize":
                    root_v = node.value.value
                    root_ok = (
                        (isinstance(root_v, ast.Name) and
                         aliases.get(root_v.id, root_v.id) in ("scipy",))
                        or (isinstance(root_v, ast.Name) and
                            str(aliases.get(root_v.id, "")).startswith("scipy"))
                    )
                    # also `import scipy.optimize` binds name
                    if isinstance(root_v, ast.Name):
                        ra = aliases.get(root_v.id, root_v.id)
                        if ra in ("scipy", "scipy.optimize") or ra.startswith("scipy"):
                            root_ok = True
                    if isinstance(node.value, ast.Name):
                        pass
                    if root_ok and attr != "nnls":
                        hits.append((r, node.lineno, f"scipy.optimize.{attr} not allowed (R34)", attr))
                # `import scipy.optimize as so; so.nnls` — so is scipy.optimize
                if isinstance(node.value, ast.Name):
                    ra = aliases.get(node.value.id, "")
                    if ra == "scipy.optimize" and attr != "nnls":
                        hits.append((r, node.lineno, f"scipy.optimize.{attr} not allowed (R34)", attr))

                if attr in ("__dict__", "__loader__", "__spec__"):
                    hits.append((r, node.lineno, f"use of {attr}", attr))
                if attr == "__class__" and isinstance(node.value, ast.Name) and node.value.id == "__loader__":
                    hits.append((r, node.lineno, "use of __loader__.__class__", "__loader__.__class__"))
                if attr == "__import__" or (
                    isinstance(node.value, ast.Name) and
                    aliases.get(node.value.id) in ("builtins", "__builtins__") and
                    attr in DANGEROUS_BUILTINS | {"__import__"}
                ):
                    hits.append((r, node.lineno, f"use of builtins.{attr}", attr))
                if (resolved_base == "os" or base_q == "os") and attr in OS_DANGEROUS_ATTRS:
                    hits.append((r, node.lineno, f"denied os.{attr}", f"os.{attr}"))
                if attr == "modules" and (
                    resolved_base == "sys" or base_q == "sys" or
                    (isinstance(node.value, ast.Name) and
                     aliases.get(node.value.id, node.value.id) == "sys")
                ):
                    hits.append((r, node.lineno, "use of sys.modules", "sys.modules"))
                if resolved_base in ("builtins", "__builtins__") or base_q in ("builtins", "__builtins__"):
                    hits.append((r, node.lineno, f"use of builtins.{attr}", f"builtins.{attr}"))

            # Subscripts
            if isinstance(node, ast.Subscript):
                key = _const_str(node.slice)
                if isinstance(node.value, ast.Name):
                    aliased = aliases.get(node.value.id, node.value.id)
                    if aliased in ("__builtins__", "builtins"):
                        hits.append((r, node.lineno, "use of __builtins__", node.value.id))
                    if aliased == "sys.modules":
                        hits.append((r, node.lineno, "use of sys.modules (alias)", node.value.id))
                base_q = _call_qualname(node.value, aliases)
                if base_q == "sys.modules" or (
                    isinstance(node.value, ast.Attribute) and node.value.attr == "modules"
                ):
                    hits.append((r, node.lineno, "use of sys.modules", "sys.modules"))
                if isinstance(node.value, ast.Attribute) and node.value.attr == "__dict__":
                    hits.append((r, node.lineno, "use of __dict__", "__dict__"))

            # Calls
            if isinstance(node, ast.Call):
                q = _call_qualname(node.func, aliases)
                target = aliases.get(q, q) if q else None
                if isinstance(node.func, ast.Name):
                    target = aliases.get(node.func.id, node.func.id)
                    q = target

                if target in ("vars", "globals", "locals", "help", "breakpoint", "input") or \
                        q in ("vars", "globals", "locals", "help", "breakpoint", "input"):
                    hits.append((r, node.lineno, f"call to {target or q}", target or q))

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

                if target in ("getattr", "builtins.getattr") or q in ("getattr", "builtins.getattr"):
                    hits.append((r, node.lineno, "call to getattr", "getattr"))
                    if len(node.args) >= 2 and _const_str(node.args[1]) is None:
                        hits.append((r, node.lineno, "dynamic getattr", ast.dump(node.args[1])))
                    # getattr(os, 'system') etc.
                    if len(node.args) >= 1:
                        host = node.args[0]
                        host_q = _call_qualname(host, aliases)
                        host_r = aliases.get(host_q, host_q) if host_q else None
                        if isinstance(host, ast.Name):
                            host_r = aliases.get(host.id, host.id)
                        if host_r == "os":
                            hits.append((r, node.lineno, "getattr on os", "os"))

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

                if isinstance(node.func, ast.Attribute) and node.func.attr in (
                        "read_text", "read_bytes", "open", "write_text", "write_bytes"):
                    recv = node.func.value
                    if isinstance(recv, ast.Call):
                        rq = _call_qualname(recv.func, aliases)
                        if rq in ("Path", "pathlib.Path") or (rq and rq.endswith(".Path")):
                            parg = recv.args[0] if recv.args else None
                            fixed = _const_str(parg) if parg is not None else None
                            if fixed is None:
                                hits.append((r, node.lineno, "Path with non-literal path",
                                             ast.dump(parg) if parg else "(no arg)"))
                            else:
                                bad = _path_forbidden(fixed)
                                if bad:
                                    hits.append((r, node.lineno, f"Path into forbidden ({bad})", fixed[:120]))

                # functools.partial(os.system, ...) — flag if any arg is os.* dangerous
                if target in ("partial", "functools.partial") or q in ("partial", "functools.partial"):
                    for arg in node.args:
                        aq = _call_qualname(arg, aliases)
                        if aq and (aq.startswith("os.") or aq == "os.system" or
                                   (aq.split(".")[-1] in OS_DANGEROUS_ATTRS and
                                    _top(aliases.get(_top(aq), _top(aq))) == "os")):
                            hits.append((r, node.lineno, f"partial of {aq}", aq))
                        if isinstance(arg, ast.Attribute):
                            b = aliases.get(_call_qualname(arg.value, aliases),
                                            _call_qualname(arg.value, aliases))
                            if b == "os" and arg.attr in OS_DANGEROUS_ATTRS:
                                hits.append((r, node.lineno, f"partial of os.{arg.attr}",
                                             f"os.{arg.attr}"))

                if q:
                    top = _top(aliases.get(q, q))
                    if top in ALWAYS_DENY_IMPORTS or any(
                        str(aliases.get(q, q)).startswith(d + ".") for d in ALWAYS_DENY_IMPORTS
                    ):
                        hits.append((r, node.lineno, f"call into denied module {top}", q))

            # Constants: forbidden folders; allow '__main__' string
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value == "__main__":
                    continue
                bad = _path_forbidden(node.value)
                if bad:
                    hits.append((r, getattr(node, "lineno", 0), "path reference", node.value[:120]))

    uniq, seen_h = [], set()
    for h in hits:
        key = (h[0], h[1], h[2], h[3])
        if key not in seen_h:
            seen_h.add(key); uniq.append(h)
    return uniq, files


def runtime_loaded_modules_check(entry_paths, root=ROOT, python=sys.executable):
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
            rr = subprocess.run([python, "-c", harness], capture_output=True, text=True, timeout=60)
            try:
                data = json.loads(rr.stdout.strip().splitlines()[-1] if rr.stdout.strip() else "{}")
            except (json.JSONDecodeError, IndexError):
                hits.append((rel(mod_file, root), 0, "runtime check failed",
                             (rr.stderr or rr.stdout or "no output")[:200]))
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
