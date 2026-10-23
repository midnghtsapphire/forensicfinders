#!/usr/bin/env python3
"""Master sources table (registry 2200).

data/sources.json is the single list of every paper, review, thesis, dataset or
API endpoint, repo, product page, guide, video, patent and article cited in sar/.
This module loads it, renders docs/research/SOURCES.md, and scans sar/ for DOIs
so a test can fail when a doc or code file cites a DOI that is not in the table.

Usage:
  python3 sources.py --render   rebuild docs/research/SOURCES.md
  python3 sources.py --check    list cited DOIs missing from the table (exit 1 if any)
  python3 sources.py <id|doi>   print one row
"""
import json, os, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "sources.json"
MD = HERE / "docs" / "research" / "SOURCES.md"
SKIP_DIRS = {"node_modules", "fixtures", "__pycache__", ".git", "out", ".pytest_cache"}
EXT = {".md", ".py", ".json", ".txt", ".cff", ".template", ".yml", ".yaml", ".ts", ".tsx", ".js", ".html", ".toml", ".cfg"}
# DOI suffix: no whitespace or markdown/quote delimiters; balanced (...) groups allowed, e.g. 10.1016/S0379-0738(01)00418-2
DOI_RE = re.compile(r'10\.\d{4,9}/(?:[^\s()\[\]|>"`,;<\']|\([^\s()]*\))+')
VERIFIED = {"yes", "no", "partial"}
TYPES = {"paper", "review", "thesis", "dataset", "repo", "product", "guide", "video", "patent", "article"}

def load(path=DATA):
    d = json.loads(Path(path).read_text())
    return d

def norm_doi(s):
    s = s.strip().lower().rstrip(".,;:*)]")
    return re.sub(r"(\.pdf|\.html?)$", "", s)

def by_doi(d=None):
    d = d or load()
    return {norm_doi(r["doi"]): r for r in d["sources"] if r.get("doi")}

def scan_dois(root=HERE):
    """Return {doi: [relative file, ...]} for every DOI cited under root (the table and SOURCES.md excluded)."""
    out = {}
    for dp, dn, fs in os.walk(root):
        dn[:] = [x for x in dn if x not in SKIP_DIRS]
        for f in fs:
            if os.path.splitext(f)[1] not in EXT or f in ("sources.json", "SOURCES.md") or f.endswith("package-lock.json"):
                continue
            p = os.path.join(dp, f)
            try: s = open(p, errors="ignore").read()
            except OSError: continue
            for m in DOI_RE.findall(s):
                d = norm_doi(m)
                if d.count("(") != d.count(")"): d = d.rstrip(")")
                out.setdefault(d, set()).add(os.path.relpath(p, root))
    return {k: sorted(v) for k, v in out.items()}

def missing(d=None, root=HERE):
    d = d or load()
    have = set(by_doi(d)) | {norm_doi(x) for x in d.get("excluded_placeholder_dois", [])}
    return {k: v for k, v in scan_dois(root).items() if k not in have}

def validate(d=None):
    """Structural problems as a list of strings (empty means OK)."""
    d = d or load(); errs = []; ids = set(); dois = set()
    for r in d["sources"]:
        sid = r.get("source_id")
        if not isinstance(sid, int) or sid in ids: errs.append(f"bad/duplicate source_id {sid}")
        ids.add(sid)
        if r.get("type") not in TYPES: errs.append(f"{sid}: type {r.get('type')}")
        if r.get("verified") not in VERIFIED: errs.append(f"{sid}: verified {r.get('verified')}")
        if not r.get("verified_date"): errs.append(f"{sid}: no verified_date")
        if not (r.get("doi") or r.get("url")): errs.append(f"{sid}: no doi or url")
        if not r.get("title"): errs.append(f"{sid}: no title")
        if r.get("type") in ("repo", "dataset") and not r.get("license"): errs.append(f"{sid}: repo/dataset without license")
        if r.get("doi"):
            k = norm_doi(r["doi"])
            if k in dois: errs.append(f"{sid}: duplicate doi {k}")
            dois.add(k)
    return errs

def _cell(s):
    return str(s or "").replace("|", "\\|").replace("\n", " ")

def render(d=None):
    d = d or load(); rows = d["sources"]
    from collections import Counter
    t = Counter(r["type"] for r in rows); v = Counter(r["verified"] for r in rows)
    L = ["# Master sources table (registry 2200)", "",
         "**Generated file. Do not edit by hand.** Edit `sar/data/sources.json`, then run `python3 sar/sources.py --render`.", "",
         f"{len(rows)} sources. By type: " + ", ".join(f"{k} {n}" for k, n in sorted(t.items())) + ". "
         f"Verified: yes {v.get('yes', 0)}, partial {v.get('partial', 0)}, no {v.get('no', 0)}.", "",
         "Verified means **yes** = the DOI record or page was opened and matches the citation; **partial** = the link resolves or was recorded but the content was not fully re-checked, or there is a caveat; **no** = it could not be confirmed. Nothing here is a claimed result.", "",
         "| ID | Type | Title | Authors / year | Venue | DOI / URL | Tags | Verified | Licence | Registry | Notes |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        a = r.get("authors") or []
        au = (", ".join(a[:3]) + (" et al." if len(a) > 3 else "")) if a else ""
        link = f"[{r['doi']}](https://doi.org/{r['doi']})" if r.get("doi") else (f"<{r['url']}>" if r.get("url") else "")
        L.append("| " + " | ".join(_cell(x) for x in [r["source_id"], r["type"], r["title"], f"{au} {r.get('year') or ''}".strip(), r.get("venue"), link,
                 ", ".join(r.get("tags", [])), f"{r['verified']} ({r['verified_date']})", r.get("license"), ", ".join(r.get("registry_ids", [])), r.get("notes")]) + " |")
    return "\n".join(L) + "\n"

if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--render"]:
        MD.write_text(render()); print(f"wrote {MD.relative_to(HERE)}")
    elif a == ["--check"]:
        m = missing(); e = validate()
        for k, v in m.items(): print("MISSING", k, v)
        for x in e: print("INVALID", x)
        sys.exit(1 if (m or e) else 0)
    elif a:
        d = load(); q = a[0].lower()
        for r in d["sources"]:
            if str(r["source_id"]) == q or (r.get("doi") or "").lower() == q: print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print(__doc__)
