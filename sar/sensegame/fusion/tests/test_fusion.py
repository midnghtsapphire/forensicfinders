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
    # Cited synthetic widths for the zero-effort identity check. Not M1, and not a geometric swath.
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


# Decision B (Discussion #28 comment 19445708). Woolpert OH 2019 Table 2-4
# stated swath is geometric coverage only. Nine-tenths of that swath is still not W.
_DECISION_B = (
    "https://github.com/midnghtsapphire/forensicfinders/discussions/28"
    "#discussioncomment-19445708"
)
_M1_GEOMETRIC_SWATH_KM = 1.456
_NINE_TENTHS = 0.9


def test_fusion_m1_null_w_is_coverage_and_budget_only(monkeypatch):
    """Fusion does not assume a numeric M1 effective width and does not score null-W M1 as detection.

    M1_W_KM is None until a cited W exists. The exponential coverage fallback is
    the labelled model in GDD v0.5 §4 / §4a, not an M1 detection score.
    """
    import sensegame.tests.test_scorer_golden as gold
    from ledgerplay.scoring import Scorer
    from sensegame.search_core import CleanScorer, Segment, UncitedSweepWidth

    phrase = "M1_W_KM is None until a cited W exists"
    assert gold.M1_W_KM is None
    assert gold.M1_W_SOURCE == _DECISION_B
    assert gold.M1_GEOMETRIC_SWATH_KM == _M1_GEOMETRIC_SWATH_KM
    assert Scorer is CleanScorer
    assert (_NINE_TENTHS * _M1_GEOMETRIC_SWATH_KM) != gold.M1_W_KM
    model_doc = CleanScorer.exponential_coverage_model.__doc__ or ""
    assert "GDD v0.5" in model_doc
    assert "not calibrated detection" in model_doc.lower()
    assert "None until a cited W exists" in model_doc
    assert "M1_W_KM" in model_doc

    repo = PKG.parents[2]
    for name in ("LEDGER.md", "CHANGELOG.md"):
        body = (repo / "docs" / "sensecrew" / "fusion" / name).read_text()
        assert phrase in body
        assert "GDD v0.5 §4 / §4a" in body
        assert "21774e2215ea07aadddac62a4085d841b488a401" in body
        assert "permanent" not in body.lower()

    forbidden = (
        "M1_W_KM",
        "1.456",
        "0.9",
        ".pod(",
        ".pos(",
        ".optimal(",
        ".update(",
        "exponential_coverage_model",
        "geometric_swath",
        "geometric_coverage",
        "permanent",
    )
    pkg_init = PKG / "__init__.py"
    for py in sorted(p for p in PKG.rglob("*.py") if p.name != "test_fusion.py"):
        text = py.read_text()
        if py.resolve() == pkg_init.resolve():
            assert text.count(phrase) == 1
            assert "GDD v0.5 §4 / §4a" in text
            text = text.replace(phrase, "")
        for needle in forbidden:
            assert needle not in text, f"{py.name} contains {needle}"

    segs = [
        Segment("S1", 1.0, 0.4, None),
        Segment("S2", 2.0, 0.25, None),
        Segment("S3", 1.5, 0.15, None),
        Segment("S4", 0.5, 0.1, None),
        Segment("ROW", 0.0, 0.1, 0.0, is_row=True),
    ]
    assert all(g.w_km is None for g in segs if not g.is_row)
    assert all(g.w_km not in (_M1_GEOMETRIC_SWATH_KM, _NINE_TENTHS * _M1_GEOMETRIC_SWATH_KM) for g in segs)
    hints = C.segment_hints(
        [{"site_id": "cell_0_0", "score": 1.0, "row": 0, "col": 0}],
        {"cell_0_0": "S1"},
        segs,
    )
    assert hints["S1"]["kind"].startswith("hint")
    assert "poa" not in json.dumps(hints)
    assert [g.poa for g in segs] == [0.4, 0.25, 0.15, 0.1, 0.1]

    scorer = Scorer()

    def boom(*_args, **_kwargs):
        raise AssertionError("coverage path called a detection or model method")

    for name in ("pod", "pos", "optimal", "update", "exponential_coverage_model"):
        monkeypatch.setattr(CleanScorer, name, boom)
    assert scorer.track_budget_spent_km(gold.M1_PLAN_KM) == pytest.approx(10.0, abs=1e-12)
    assert scorer.geometric_survey_km2(_M1_GEOMETRIC_SWATH_KM, 2.5) == pytest.approx(3.64, abs=1e-12)
    assert scorer.geometric_coverage(_M1_GEOMETRIC_SWATH_KM, 2.5, 1.0) == pytest.approx(3.64, abs=1e-12)
    monkeypatch.undo()
    with pytest.raises(UncitedSweepWidth):
        scorer.pos(segs, gold.M1_PLAN_KM)
    with pytest.raises(UncitedSweepWidth):
        scorer.optimal(segs, gold.M1_BUDGET_KM)
    with pytest.raises(UncitedSweepWidth):
        scorer.update(segs, gold.M1_PLAN_KM)


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
_SENTINEL = "SECRET-SENTINEL-VALUE"


def _geo_cfg(key, where):
    cfg = {"grid": {"rows": 1, "cols": 2, "cell_m": 1.0}, "missing_policy": "zero",
           "layers": [{"name": "a", "weight": 1.0, "direction": "higher", "values": [[1, 2]]}]}
    if where == "root":
        cfg[key] = _SENTINEL
    elif where == "dict":
        cfg["nested"] = {key: _SENTINEL}
    else:
        cfg["nested"] = [{key: _SENTINEL}]
    return cfg


@pytest.mark.parametrize("key", sorted(C.GEO_KEYS))
@pytest.mark.parametrize("where", ["root", "dict", "list"])
def test_rejects_geographic_fields(key, where):
    with pytest.raises(C.FusionError) as ei:
        C.validate_config(_geo_cfg(key, where))
    assert _SENTINEL not in str(ei.value)


def _mixed_case(name: str) -> str:
    return "".join(ch.upper() if i % 2 == 0 else ch.lower() for i, ch in enumerate(name))


@pytest.mark.parametrize("key", sorted(C.GEO_KEYS))
def test_rejects_mixed_case_geographic_fields(key):
    shown = _mixed_case(key)
    assert shown != key
    with pytest.raises(C.FusionError) as ei:
        C.validate_config(_geo_cfg(shown, "root"))
    text = str(ei.value)
    assert _SENTINEL not in text
    assert shown not in text


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


def _seed_argv(tmp_path, *extra):
    out = tmp_path / "seedout" / "once"
    argv = ["--seed", "7", "--config", str(tmp_path / "cfg.json"), "--out", str(out), *extra]
    return out.parent / "seeds.jsonl", argv


def test_seed_drift_refuses_to_append(tmp_path, monkeypatch, capsys):
    from sensegame.fusion import __main__ as cli
    ledger, argv = _seed_argv(tmp_path)
    old = {"config_sha256": "aaa", "fusion_7.json": "old", "seed": 7}
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps(old, sort_keys=True) + "\n")
    before = ledger.read_bytes()
    monkeypatch.setattr(cli, "run", lambda *a, **k: {"config_sha256": "aaa", "fusion_7.json": "new", "seed": 7})
    assert cli.main(argv) == 1
    err = capsys.readouterr().err
    assert "DRIFT" in err
    assert ledger.read_bytes() == before


def test_seed_accept_drift_appends_with_drift_from(tmp_path, monkeypatch):
    from sensegame.fusion import __main__ as cli
    ledger, argv = _seed_argv(tmp_path, "--accept-drift")
    old = {"config_sha256": "aaa", "fusion_7.json": "old", "seed": 7}
    old_line = json.dumps(old, sort_keys=True)
    ledger.parent.mkdir(parents=True)
    ledger.write_text(old_line + "\n")
    monkeypatch.setattr(cli, "run", lambda *a, **k: {"config_sha256": "aaa", "fusion_7.json": "new", "seed": 7})
    assert cli.main(argv) == 0
    lines = ledger.read_text().splitlines()
    assert lines[0] == old_line
    fresh = json.loads(lines[1])
    assert fresh["fusion_7.json"] == "new"
    assert fresh["drift_from"] == cli._record_hash(old)
    assert len(lines) == 2


def test_seed_same_hash_does_not_append(tmp_path, monkeypatch):
    from sensegame.fusion import __main__ as cli
    ledger, argv = _seed_argv(tmp_path)
    same = {"config_sha256": "aaa", "fusion_7.json": "same", "seed": 7}
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps(same, sort_keys=True) + "\n")
    before = ledger.read_bytes()
    monkeypatch.setattr(cli, "run", lambda *a, **k: dict(same))
    assert cli.main(argv) == 0
    assert ledger.read_bytes() == before
