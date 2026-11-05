"""FUSION_SPEC v0.2 §6 tests (registry 2371, provisional). Synthetic only."""
from __future__ import annotations

import ast
import hashlib
import json
import math
from pathlib import Path

import pytest

from sensegame.fusion import combine as C
from sensegame.fusion import anomaly as A
from sensegame.fusion import run as R

PKG = Path(__file__).resolve().parents[1]
FIX = PKG / "fixtures"
CONFIG = FIX / "fusion_config_synthetic.json"
SEED = 1002


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# 1 determinism_bytes
def test_determinism_bytes(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    R.run(SEED, CONFIG, a)
    R.run(SEED, CONFIG, b)
    for name in (f"fusion_{SEED}.json", f"uncertainty_map_{SEED}.tif"):
        assert _sha(a / name) == _sha(b / name)
    txt = (a / f"fusion_{SEED}.json").read_text()
    for banned in ("timestamp", "created", "datetime", "2026-"):
        assert banned not in txt


# 2 score_has_uncertainty
def test_score_has_uncertainty_and_n_boot(tmp_path):
    R.run(SEED, CONFIG, tmp_path)
    out = json.loads((tmp_path / f"fusion_{SEED}.json").read_text())
    assert out["anomaly"]["n_boot"] == 1000 == A.N_BOOT
    for rec in out["cells"]:
        an = rec["anomaly"]
        for k in ("anomaly_score", "p_anomaly_calibrated", "ci_low", "ci_high", "n_boot", "ece_holdout"):
            assert k in an
        assert an["n_boot"] == 1000
        assert an["ci_low"] <= an["p_anomaly_calibrated"] <= an["ci_high"]


def test_writer_refuses_score_without_band():
    with pytest.raises(A.FusionError):
        A.check_banded({"anomaly_score": 0.1, "p_anomaly_calibrated": 0.2})


# 3 calibration_holdout
def test_calibration_ece_gate():
    cfg = C.load_config(CONFIG)
    model = A.fit_calibrated(cfg, seed=SEED)
    assert model.ece_holdout <= 0.05, model.ece_holdout
    assert 0.0 <= model.brier_holdout <= 1.0


def test_ece_known_values():
    assert A.ece([0.0, 1.0], [0, 1]) == 0.0
    assert math.isclose(A.ece([0.5] * 4, [1, 1, 1, 1]), 0.5)


# 4 scorer_contract_passthrough (fusion is a hint layer; never changes POA)
def test_scorer_contract_passthrough(tmp_path):
    from sensegame.search_core import CleanScorer, Segment
    segs = [Segment("A", 1.0, 0.6, 0.5), Segment("B", 2.0, 0.3, 0.5), Segment("ROW", 1.0, 0.1, None, is_row=True)]
    before = list(segs)
    R.run(SEED, CONFIG, tmp_path)
    out = json.loads((tmp_path / f"fusion_{SEED}.json").read_text())
    mapping = {r["site_id"]: ("A" if r["row"] < 10 else "B") for r in out["cells"]}
    hints = C.segment_hints(out["cells"], mapping, segs)
    assert set(hints) == {"A", "B"}
    assert segs == before and all(s.poa == b.poa for s, b in zip(segs, before))
    assert "poa" not in json.dumps(hints)
    assert not hasattr(C, "update")  # only CleanScorer.update moves POA
    assert CleanScorer().update(segs, {"A": 0.0, "B": 0.0})[0].poa == pytest.approx(0.6, abs=1e-12)


# 5 combine_handcomputed
def test_robust_z_handcomputed():
    z, deg = C.robust_z([1.0, 2.0, 3.0, 4.0, 100.0])
    assert not deg
    # median 3, MAD 1 -> scale 1.4826
    assert z[0] == pytest.approx(-2 / 1.4826, abs=1e-12)
    assert z[4] == pytest.approx(97 / 1.4826, abs=1e-12)


def test_combine_handcomputed():
    cfg = {
        "grid": {"rows": 1, "cols": 5, "cell_m": 10.0},
        "missing_policy": "renormalise",
        "layers": [
            {"name": "a", "weight": 2.0, "direction": "higher", "values": [[1, 2, 3, 4, 100]]},
            {"name": "b", "weight": 1.0, "direction": "lower", "values": [[1, 2, 3, 4, 100]]},
        ],
    }
    recs, meta = C.combine(C.validate_config(cfg))
    s = 1.4826
    assert recs[0]["score"] == pytest.approx((2 * (-2 / s) + 1 * (2 / s)) / 3, abs=1e-12)
    assert recs[0]["contributions"]["a"]["contribution"] == pytest.approx(2 * (-2 / s) / 3, abs=1e-12)
    assert recs[0]["score_kind"] == C.SCORE_KIND


def test_flat_layer_flagged_not_zeroed():
    cfg = {
        "grid": {"rows": 1, "cols": 4, "cell_m": 10.0},
        "missing_policy": "renormalise",
        "layers": [
            {"name": "flat", "weight": 1.0, "direction": "higher", "values": [[5, 5, 5, 5]]},
            {"name": "ok", "weight": 1.0, "direction": "higher", "values": [[1, 2, 3, 4]]},
        ],
    }
    recs, meta = C.combine(C.validate_config(cfg))
    assert meta["layers"]["flat"]["degenerate"] is True
    assert meta["layers"]["flat"]["excluded"] is True
    c = recs[0]["contributions"]["flat"]
    assert c["normalised"] is None and c["contribution"] is None  # flagged, not zeroed
    assert c["raw"] == 5.0


def test_missing_policy_zero_vs_renormalise():
    base = {
        "grid": {"rows": 1, "cols": 5, "cell_m": 10.0},
        "layers": [
            {"name": "a", "weight": 1.0, "direction": "higher", "values": [[1, 2, 3, 4, 5]]},
            {"name": "b", "weight": 1.0, "direction": "higher", "values": [[None, 2, 3, 4, 5]]},
        ],
    }
    r1, _ = C.combine(C.validate_config(dict(base, missing_policy="renormalise")))
    r0, _ = C.combine(C.validate_config(dict(base, missing_policy="zero")))
    assert r0[0]["score"] == pytest.approx(r1[0]["score"] / 2, abs=1e-12)


# 6 no_geographic_fields
@pytest.mark.parametrize("key", ["lat", "lon", "latitude", "longitude", "address", "Lat", "lng"])
def test_rejects_geographic_fields(key):
    cfg = {"grid": {"rows": 1, "cols": 2, "cell_m": 1.0}, "missing_policy": "zero",
           "layers": [{"name": "a", "weight": 1.0, "direction": "higher", "values": [[1, 2]], key: 1.0}]}
    with pytest.raises(C.FusionError):
        C.validate_config(cfg)


def test_rejects_bad_site_id():
    with pytest.raises(C.FusionError):
        C.parse_site_id("trailhead_7")
    assert C.parse_site_id("cell_3_4") == (3, 4)


# 7 fixtures_synthetic_only
@pytest.mark.parametrize("bad", ["data/real.json", "fixtures/real.json", "case/synthetic.json", "elsewhere/x_synthetic.json"])
def test_fixtures_synthetic_only(tmp_path, bad):
    p = tmp_path / bad
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{}")
    with pytest.raises(C.FusionError):
        C.guard_path(p)


def test_all_shipped_fixtures_are_synthetic():
    files = sorted(FIX.iterdir())
    assert files
    for f in files:
        assert "synthetic" in f.name
        C.guard_path(f)


# 8 no_forbidden_imports
FORBIDDEN = ("search_theory", "optimal_search", "lost_person_behavior", "forensic_pipeline", "dossier",
             "evidence_fusion", "evidence_scoring", "public_records", "realdata", "terratorch",
             "ultralytics", "hfmr", "case", "evidence", "torch")


def test_no_forbidden_imports():
    for py in sorted(PKG.rglob("*.py")):
        tree = ast.parse(py.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            for n in names:
                parts = n.split(".")
                for bad in FORBIDDEN:
                    assert not any(p == bad or p.startswith(bad) for p in parts), f"{py}: {n}"


def test_embeddings_off():
    assert A.FUSION_EMBEDDINGS == 0
