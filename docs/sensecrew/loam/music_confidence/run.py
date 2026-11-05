"""Deterministic re-score with revvel-standards fraud-signal-verification-fleet/src/confidence.py (read-only copy at CONFIDENCE_PY path; not vendored).
Config values transcribed from docs/CONFIDENCE_FRAMEWORK.md."""
import json, os, sys, importlib.util
spec = importlib.util.spec_from_file_location("confidence", os.environ.get("CONFIDENCE_PY", "/tmp/confidence.py"))
c = importlib.util.module_from_spec(spec); sys.modules["confidence"] = c; spec.loader.exec_module(c)
cfg = {"tiers": {5:{"name":"adjudicated record","weight":1.00},4:{"name":"primary official","weight":0.80},
                 3:{"name":"direct reporting","weight":0.60},2:{"name":"opinion/secondary","weight":0.35},1:{"name":"social/anonymous","weight":0.15}},
       "adjudication_ceilings":{"unknowable":0.20,"alleged":0.45,"investigated":0.55,"charged":0.75,"guilty_plea":0.90,"settled_no_admission":0.65,"convicted":0.98},
       "corroboration":{"per_source_bonus":0.06,"max_bonus":0.24},"contradiction":{"per_source_penalty":0.12,"max_penalty":0.48},
       "provenance":{"filing":1.00,"on_record_statement":0.95,"official_leak":0.70,"unattributed_leak":0.40,"anonymous_report":0.25}}
case = json.load(open(os.path.join(os.path.dirname(__file__), "case.json")))
for s in c.score_case(case, cfg):
    print(f"{s.claim_id}\t{s.confidence:.3f}\t{s.band}\t{' | '.join(s.rationale)}")
