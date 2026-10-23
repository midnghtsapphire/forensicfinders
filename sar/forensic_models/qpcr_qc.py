"""qPCR run QC from real instrument export CSVs (QuantStudio / Bio-Rad CFX column layouts, or a mapping).
  standard curve: Cq = slope*log10(qty) + b;  E = 10^(-1/slope) - 1;  R^2
  NTC / extraction-blank (EB): clean when no Cq (Undetermined/blank/N/A) or Cq >= cq_cutoff
  IPC inhibition: delta_Cq = IPC_Cq(sample) - IPC_Cq(reference, e.g. NTC/standards mean); inhibited if > threshold
Acceptance defaults (efficiency 90-110 %, R^2 >= 0.98, IPC delta 1.0 Cq) are common lab practice, configurable;
see MIQE: Bustin et al. (2009) Clin Chem 55(4):611-622, doi:10.1373/clinchem.2008.112797.
There are no built-in results. Every number comes from the file you load."""
import csv, io, math

LAYOUTS = {
    "quantstudio": {"sample": "Sample Name", "target": "Target Name", "cq": "CT", "task": "Task", "qty": "Quantity",
                    "tasks": {"STANDARD": "std", "NTC": "ntc", "UNKNOWN": "unknown"}},
    "biorad_cfx": {"sample": "Sample", "target": "Target", "cq": "Cq", "task": "Content", "qty": "Starting Quantity (SQ)",
                   "tasks": {"Std": "std", "NTC": "ntc", "Unkn": "unknown", "NRT": "ntc"}},
}
DEFAULTS = {"eff_min": 0.90, "eff_max": 1.10, "r2_min": 0.98, "cq_cutoff": 40.0, "ipc_delta_max": 1.0, "eb_prefix": "EB"}


def _num(v):
    v = (v or "").strip()
    if v == "" or v.lower() in ("undetermined", "n/a", "na", "nan", "-"):
        return None
    return float(v.replace(",", ""))


def read_export(text, layout):
    L = LAYOUTS[layout] if isinstance(layout, str) else layout
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if L["sample"] in l and L["cq"] in l)  # skip instrument header block
    rows = []
    for r in csv.DictReader(io.StringIO("\n".join(lines[start:]))):
        if not r.get(L["sample"]):
            continue
        raw = (r.get(L["task"]) or "").strip()
        task = L["tasks"].get(raw, L["tasks"].get(raw.split("-")[0].strip(), "unknown"))  # CFX uses Std-01, Unkn-03
        rows.append({"sample": r[L["sample"]].strip(), "target": r.get(L["target"], "").strip(), "task": task,
                     "cq": _num(r.get(L["cq"])), "qty": _num(r.get(L["qty"]))})
    return rows


def standard_curve(rows, target):
    pts = [(math.log10(r["qty"]), r["cq"]) for r in rows if r["target"] == target and r["task"] == "std" and r["cq"] is not None and r["qty"]]
    if len({x for x, _ in pts}) < 3:
        raise ValueError(f"{target}: need standards at >= 3 distinct quantities")
    n = len(pts); mx = sum(x for x, _ in pts) / n; my = sum(y for _, y in pts) / n
    sxx = sum((x - mx) ** 2 for x, _ in pts); sxy = sum((x - mx) * (y - my) for x, y in pts)
    slope = sxy / sxx; b = my - slope * mx
    ss_res = sum((y - (slope * x + b)) ** 2 for x, y in pts); ss_tot = sum((y - my) ** 2 for _, y in pts)
    r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")
    return {"target": target, "points": n, "slope": slope, "intercept": b, "r2": r2, "efficiency": 10 ** (-1 / slope) - 1}


def qc(rows, assay_target, ipc_target=None, **cfg):
    c = {**DEFAULTS, **cfg}
    sc = standard_curve(rows, assay_target)
    sc["pass"] = c["eff_min"] <= sc["efficiency"] <= c["eff_max"] and sc["r2"] >= c["r2_min"]
    def clean(r): return r["cq"] is None or r["cq"] >= c["cq_cutoff"]
    ntc = [r for r in rows if r["task"] == "ntc" and r["target"] == assay_target]
    eb = [r for r in rows if r["sample"].upper().startswith(c["eb_prefix"]) and r["target"] == assay_target]
    out = {"standard_curve": sc,
           "ntc": {"n": len(ntc), "clean": bool(ntc) and all(clean(r) for r in ntc), "hits": [r["sample"] for r in ntc if not clean(r)]},
           "extraction_blanks": {"n": len(eb), "clean": bool(eb) and all(clean(r) for r in eb), "hits": [r["sample"] for r in eb if not clean(r)]},
           "settings": c}
    if ipc_target:
        ref = [r["cq"] for r in rows if r["target"] == ipc_target and r["task"] in ("ntc", "std") and r["cq"] is not None]
        if not ref:
            raise ValueError("no IPC reference wells (NTC/standards with IPC Cq)")
        ref_cq = sum(ref) / len(ref)
        samples = []
        for r in rows:
            if r["target"] == ipc_target and r["task"] == "unknown":
                d = None if r["cq"] is None else r["cq"] - ref_cq
                samples.append({"sample": r["sample"], "ipc_cq": r["cq"], "delta_cq": d,
                                "inhibited": d is None or d > c["ipc_delta_max"]})
        out["ipc"] = {"reference_cq": ref_cq, "samples": samples}
    out["pass"] = sc["pass"] and out["ntc"]["clean"] and (out["extraction_blanks"]["clean"] or not eb)
    if not ntc:
        out["pass"] = False; out["ntc"]["note"] = "no NTC wells found; a run without NTCs cannot pass"
    return out
