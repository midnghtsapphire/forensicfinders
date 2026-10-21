#!/usr/bin/env python3
# PROPRIETARY - ALL RIGHTS RESERVED. (c) 2026 Audrey Evans / Walter-Evans Forensic Intelligence Systems.
# No license is granted. Pre-patent-filing; keep the repository private. See LICENSE and docs/PATENT_PREP.md.
# STATUS: PROTOTYPE. All numbers this module prints in demos are SYNTHETIC; see search_system/README.md "Audit".
"""
coldcase_master.py - case orchestration + BLIND retrospective validation.

Subcommands:
  new <root> <case_id> --config case.json    scaffold a case (truth sealed if resolved)
  run <case_dir>                             full pipeline -> candidates + report + evidence log
  validate <root>                            run every resolved case BLIND, score vs sealed truth
  demo                                       end-to-end synthetic validation study (3 cases)
  blueocean                                  print researched adjacent-tech registry

BLINDING PROTOCOL (the part that makes retrospective testing scientific):
  truth.json is written once, then truth.sha256 seals it. run_case() NEVER
  reads truth.*. Only validate() opens the seal, and it recomputes the hash
  first. Score the run BEFORE unsealing; seal again immediately after.
"""
import sys, os, json, hashlib, pickle, math, argparse, datetime
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from remains_anomaly_pipeline import (make_tile, probability_raster,
    county_sweep, candidates_from_prob, dedupe_candidates, _gistar_z_stratified,
    change_confidence_raster, fuse, slope_degrees, grave_signature_score,
    ndvi_anomaly, report_density, nitrate_hotspot, feature_dataframe,
    block_groups, calibrate_probability)
from field_confirmation import interpret_sample

# ---------------------------------------------------------- evidence log ---
class EvidenceLog:
    """SHA-256 hash-chained log (stdlib). Each entry commits the previous
    hash -> tamper-evident chain. Ed25519 signing plugs in here when the
    cryptography package is available."""
    def __init__(self, path):
        self.path = path; self.prev = "GENESIS"
        if os.path.exists(path):
            for line in open(path):
                self.prev = json.loads(line)["hash"]
    def record(self, action, path, meta=None):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        payload = {"seq": self._seq(), "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   "action": action, "file": os.path.basename(path),
                   "sha256": file_hash, "prev": self.prev, "meta": meta or {}}
        h.update(json.dumps(payload, sort_keys=True).encode())
        payload["hash"] = h.hexdigest()
        try:
            with open(self.path, "a") as f:
                f.write(json.dumps(payload) + "\n")
        except OSError:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "a") as f:
                f.write(json.dumps(payload) + "\n")
        self.prev = payload["hash"]
        return payload["hash"]
    def _seq(self):
        if not os.path.exists(self.path): return 0
        return sum(1 for _ in open(self.path))

def seal(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()

# ---------------------------------------------------- blue-ocean registry --
# UNVERIFIED IN PORT: sources below are the original author's short labels, not full citations;
# re-check each before quoting (see docs/BLUE_OCEAN_RESEARCH.md).
BLUE_OCEAN = [
 {"name": "Gravesoil necrobiome PBI/PTI engine", "maturity": "emerging (2025 reviews call for validation)",
  "what": "16S/MPS soil microbiome shift marks burial (post-burial interval) AND translocation "
          "(post-translocation interval) - detects remains even after removal; CDI microbial "
          "profiles persist months-years. Natural extension of our eDNA layer to microbial community fingerprints.",
  "cost": "$2-5k/case (sequencing)", "patent_space": "HIGH - PTI is a new concept, few filings",
  "source": "Frontiers Microbiology 2025 (forensic ecogenomics review)"},
 {"name": "Adipocere dielectric fingerprint", "maturity": "field-observed, under-quantified",
  "what": "Grave wax persists decades and is GPR-visible; a dielectric-signature library "
          "(adipocere vs. root vs. stone hyperbolas) would extend GPR usefulness to 15+ year cold cases.",
  "cost": "software over existing GPR", "patent_space": "MEDIUM - needs own dataset",
  "source": "YSU/Proceq GS8000 grave research program"},
 {"name": "LABRADOR-class field e-nose", "maturity": "NIJ-validated prototype, $1-1.5k/unit",
  "what": "12-sensor VOC array; <60 s qualitative read comparable to GC-MS headspace. PRIOR ART - "
          "cite, don't claim; our value-add is fusing e-nose hits with the probability map.",
  "cost": "$1.5k hardware", "patent_space": "LOW (published) - integrate, don't claim",
  "source": "NIJ/Oak Ridge LABRADOR detector"},
 {"name": "VOC persistence-after-removal (PTI chemistry)", "maturity": "published (7-month persistence)",
  "what": "Soil VOC profile still discriminates experimental vs control soil 125-214 days after "
          "removal of remains -> confirms a site was USED even if the body was moved. Pairs with necrobiome PTI.",
  "cost": "lab GC-MS", "patent_space": "MEDIUM-HIGH for the fusion workflow",
  "source": "Forensic Sci Med Pathol 2015 (soil VOC persistence)"},
 {"name": "Muon tomography for deep voids", "maturity": "2025 field demo (Jerusalem), mobile units ~30 m range",
  "what": "Cosmic-ray muon attenuation maps voids through rock/soil to ~100 m. PRIOR ART since 1960s "
          "(pyramids) - not claimable; relevant only for deep culvert/vault cases beyond GPR.",
  "cost": "$50k+ per detector station", "patent_space": "LOW (prior art) - cite",
  "source": "Benhammou et al., J. Applied Physics 2025"},
 {"name": "Hyperspectral 700-1800 nm grave imaging", "maturity": "controlled studies (Mexico); >=3 months post-burial",
  "what": "Narrow-band vegetation/soil response detects simulated graves; needs >=3 months. PRIOR ART - "
          "but airborne hyperspectral + our fusion is unexplored.",
  "cost": "$10-40k/survey", "patent_space": "LOW-MEDIUM for fusion claims",
  "source": "Silvan et al., Yautepec pig-grave studies"},
 {"name": "EMI conductivity + moisture co-survey", "maturity": "established geophysics, underused in forensics",
  "what": "Early decomposition raises soil conductivity (porewater ions), late adipocere lowers it - "
          "EMI temporal trend = decomposition clock. Cheap towed array, complements GPR.",
  "cost": "$15-30k instrument", "patent_space": "MEDIUM for the temporal-inversion method",
  "source": "Youngstown State pig body farm geophysics program"},
]

# ------------------------------------------------------------- case build --
def new_case(root, case_id, cfg):
    d = os.path.join(root, case_id); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "case.json"), "w") as f:
        json.dump(cfg, f, indent=2)
    if cfg.get("resolved"):
        truth = {"easting": cfg["truth_e"], "northing": cfg["truth_n"],
                 "burial_year": cfg.get("truth_year"), "case_id": case_id}
        with open(os.path.join(d, "truth.json"), "w") as f:
            json.dump(truth, f, indent=2)
        with open(os.path.join(d, "truth.sha256"), "w") as f:
            f.write(seal(os.path.join(d, "truth.json")) + "\n")
    return d

def build_case_scene(cfg):
    """Synthetic scene per case (real-data path: run_county.build_tile)."""
    shape = tuple(cfg.get("shape", [300, 300]))
    tile = make_tile(cfg["seed"], shape=shape, graves=[tuple(g) for g in cfg["graves"]],
                     years=tuple(cfg["years"]))
    if cfg.get("nitrate_fps"):
        tile[1]["nitrate"] = np.maximum(tile[1]["nitrate"],
            nitrate_hotspot([tuple(s) for s in cfg["nitrate_fps"]], shape, 1.0))
    return tile

def train_reference(path=None):
    path = path or os.path.join(os.environ.get("SEARCH_SYSTEM_OUT", "out/search_system"), "reference_model.pkl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    """One reference model, trained on a calibration scene; reused across cases
    (in practice: recalibrate per region after enough resolved cases exist)."""
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    years = [2018, 2020, 2023, 2026]
    cal = make_tile(11, graves=[(100,100,2019),(200,220,2021),(150,260,2023)])
    lab = np.zeros(cal[2].shape, int)
    for r, c, _ in [(100,100,2019),(200,220,2021),(150,260,2023)]:
        lab[max(0,r-2):r+3, max(0,c-2):c+3] = 1
    df = feature_dataframe(cal[1], lab, groups=block_groups(cal[2].shape, 25), seed=5)
    model, metrics = calibrate_probability(df, list(cal[1].keys()), model_type="gbm")
    bundle = {"model": model, "feats": list(cal[1].keys()), "metrics": metrics}
    try:                                            # cache is best-effort; the model
        with open(path, "wb") as f:                 # works in memory regardless
            pickle.dump(bundle, f)
    except OSError:
        print("  [warn] model cache write failed - continuing in-memory")
    return bundle

def run_case(case_dir, ref=None):
    ref = ref or train_reference()
    cfg = json.load(open(os.path.join(case_dir, "case.json")))
    log = EvidenceLog(os.path.join(case_dir, "evidence.jsonl"))
    tile = build_case_scene(cfg)
    prob = probability_raster(ref["model"], tile[1], ref["feats"])
    cand = candidates_from_prob(prob, tile[1]["change_conf"], 1.0, tuple(cfg["origin_xy"]))
    cand = dedupe_candidates(cand) if len(cand) else cand
    cand.to_csv(os.path.join(case_dir, "candidates.csv"), index=False)
    log.record("candidates", os.path.join(case_dir, "candidates.csv"),
               {"model": "gbm", "ref_metrics": ref["metrics"]})
    # void layer (culvert/vault case)
    from field_confirmation import detect_culverts
    voids, vdf = detect_culverts(tile[0][-1], 1.0)
    vdf.to_csv(os.path.join(case_dir, "voids.csv"), index=False)
    # report
    lines = [f"# Case report: {os.path.basename(case_dir)}", "",
             f"model blocked-CV: {ref['metrics']}", "", "## Ranked candidates (world coords)"]
    if len(cand):
        lines.append(cand.to_string(index=False))
        for _, r in cand.head(5).iterrows():
            lines.append(f"- ({r.easting:.0f},{r.northing:.0f}) P={r.P_grave:.2f}: "
                         + ("GPR + dog team + nitrate probe grid, then qPCR if confirmed"
                            if r.P_grave > 0.5 else "desk review; low-cost revisit only"))
    else:
        lines.append("No candidates above gate. Recommend: expand AOI or lower confidence threshold with justification.")
    lines += ["", "## Void scan (culvert/vault)"]
    lines.append(vdf.to_string(index=False) if len(vdf) else "no significant voids")
    lines += ["", "## Assay QC gates for any dig", "- triplicates within 1.5 Ct; IPC dCt <= 1.5",
              "- LOD95/LOQ from validation curve before interpreting negatives",
              "- interpret_sample() from field_confirmation.py is the decision point"]
    with open(os.path.join(case_dir, "case_report.md"), "w") as f:
        f.write("\n".join(lines))
    log.record("report", os.path.join(case_dir, "case_report.md"))
    return cand, vdf

# ------------------------------------------------------- blind validation --
def validate(root, ref=None):
    ref = ref or train_reference()
    rows = []
    for case_id in sorted(os.listdir(root)):
        d = os.path.join(root, case_id)
        seal_f, truth_f = os.path.join(d, "truth.sha256"), os.path.join(d, "truth.json")
        if not (os.path.exists(seal_f) and os.path.exists(truth_f)): continue
        assert open(seal_f).read().strip() == seal(truth_f), f"SEAL BROKEN: {case_id}"
        truth = json.load(open(truth_f))
        cand, _ = run_case(d, ref)                       # BLIND: run before reading truth fields
        p_near = []; rank = None
        for i, (_, r) in enumerate(cand.iterrows()):
            dist = math.hypot(r.easting - truth["easting"], r.northing - truth["northing"])
            if dist <= 10: p_near.append(r.P_grave); rank = rank if rank is not None else i + 1
        top1_err = (math.hypot(cand.iloc[0].easting - truth["easting"],
                               cand.iloc[0].northing - truth["northing"])
                    if len(cand) else float("nan"))
        rows.append({"case": case_id, "P_at_truth": round(max(p_near), 3) if p_near else 0.0,
                     "truth_rank": rank, "top1_error_m": round(top1_err, 1) if top1_err == top1_err else None,
                     "n_candidates": len(cand)})
    rep = pd.DataFrame(rows)
    agg = {"cases": len(rep),
           "detection_rate_P>0.5": round(float((rep.P_at_truth > 0.5).mean()), 3) if len(rep) else 0,
           "median_top1_error_m": float(rep.top1_error_m.median()) if len(rep) else None,
           "truth_in_top3": int((rep.truth_rank <= 3).sum()) if len(rep) else 0}
    with open(os.path.join(root, "validation_report.md"), "w") as f:
        f.write("# Retrospective validation (BLIND, sealed-truth)\n\n")
        f.write(json.dumps(agg, indent=2) + "\n\n" + rep.to_string(index=False) + "\n")
    return rep, agg

# ------------------------------------------------------------------- demo --
def demo(root=None):
    root = root or os.path.join(os.environ.get("SEARCH_SYSTEM_OUT", "out/search_system"), "coldcase_demo")
    import shutil
    if os.path.exists(root): shutil.rmtree(root)
    os.makedirs(root)
    ref = train_reference()
    # SYNTHETIC demo cases: truth_e/n are derived from the planted grave + origin, so this
    # "validation" only checks plumbing. It is NOT evidence of real-case performance.
    cases = [
        {"case_id": "CASE-001-resolved", "seed": 21, "years": [2018, 2020, 2023, 2026],
         "graves": [[140, 160, 2020]], "origin_xy": [500000, 4000000], "resolved": True,
         "truth_e": 500160, "truth_n": 4000140, "truth_year": 2020,
         "nitrate_fps": [[40, 40, 130]]},
        {"case_id": "CASE-002-resolved", "seed": 31, "years": [2018, 2020, 2023, 2026],
         "graves": [[200, 90, 2022]], "origin_xy": [510000, 4010000], "resolved": True,
         "truth_e": 510090, "truth_n": 4010200, "truth_year": 2022,
         "nitrate_fps": [[250, 250, 120]]},
        {"case_id": "CASE-003-resolved", "seed": 41, "years": [2018, 2020, 2023, 2026],
         "graves": [[90, 220, 2019]], "origin_xy": [520000, 4020000], "resolved": True,
         "truth_e": 520220, "truth_n": 4020090, "truth_year": 2019,
         "nitrate_fps": [[150, 60, 140]]},
    ]
    for c in cases:
        cid = c.pop("case_id")
        new_case(root, cid, c)
        run_case(os.path.join(root, cid), ref)
        print(f"ran {cid}")
    rep, agg = validate(root, ref)
    print("\n== RETROSPECTIVE VALIDATION (3 resolved cases, blind) ==")
    print(rep.to_string(index=False))
    print(json.dumps(agg, indent=2))

def main():
    ap = argparse.ArgumentParser(description="Cold-case master application")
    sub = ap.add_subparsers(dest="cmd")
    pn = sub.add_parser("new"); pn.add_argument("root"); pn.add_argument("case_id"); pn.add_argument("--config", required=True)
    pr = sub.add_parser("run"); pr.add_argument("case_dir")
    pv = sub.add_parser("validate"); pv.add_argument("root")
    sub.add_parser("demo"); sub.add_parser("blueocean")
    a = ap.parse_args()
    if a.cmd == "new": new_case(a.root, a.case_id, json.load(open(a.config)))
    elif a.cmd == "run": run_case(a.case_dir)
    elif a.cmd == "validate": print(validate(a.root)[1])
    elif a.cmd == "demo": demo()
    elif a.cmd == "blueocean":
        for t in BLUE_OCEAN:
            print(f"* {t['name']}  [{t['maturity']}]  patent-space: {t['patent_space']}\n    {t['what']}\n    src: {t['source']}")



# -------------------------------------------- PRIORITY ANCHORING (rewards) ---
def verify_chain(log_path):
    """Recompute the entire hash chain from genesis. Returns (ok, report).
    A single tampered byte anywhere breaks the first bad link - this is what
    makes the ledger tamper-evident. (Port note: tamper-evidence is not the same as legal
    admissibility; that is for counsel to judge.)"""
    prev, seq, bad = "GENESIS", -1, None
    for line in open(log_path):
        e = json.loads(line)
        if e["prev"] != prev: bad = e["seq"]; break
        if e["seq"] != seq + 1: bad = e["seq"]; break
        h = e.pop("hash")
        if hashlib.sha256(json.dumps(e, sort_keys=True).encode()).hexdigest() != h:
            bad = e["seq"]; break
        prev, seq = h, e["seq"]
    return bad is None, {"entries": seq + 1, "head": prev, "first_bad": bad}

def export_anchor_manifest(root, out="anchor_manifest.json"):
    """Collect every chain head into one manifest -> timestamp THIS file.
    Anchoring options (cheapest first):
      1. OpenTimestamps (free, Bitcoin-anchored): `pip install opentimestamps-
         client`, then `ots stamp anchor_manifest.json` - proves existence at
         a date without revealing contents, and without creating patent-prior-
         art (the manifest is hash-only).
      2. RFC 3161 TSA (your patent spec already claims this): submit via any
         TSA accepting RFC 3161 TimeStampReq (e.g. sectigo/freetsa).
      3. Notary / attorney escrow for paper trails.
    Anchor cadence: at case close, and before any tip submission."""
    heads = {}
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f == "evidence.jsonl":
                ok, rep = verify_chain(os.path.join(dp, f))
                heads[os.path.relpath(dp, root)] = {"chain_ok": ok, **rep}
    manifest = {"root": os.path.basename(os.path.abspath(root)),
                "exported_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "heads": heads}
    p = os.path.join(root, out)
    with open(p, "w") as f:
        json.dump(manifest, f, indent=2)
    return p, heads

if __name__ == "__main__":
    main()
