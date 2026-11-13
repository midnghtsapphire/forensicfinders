"""FUSION_SPEC v0.2 §6 tests (registry 2371, provisional). Synthetic only."""
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import subprocess
import sys
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
        assert an["ci_low"] <= an["ci_high"]
        # p may sit outside the raw 2.5/97.5 band (#52); do not require it inside.


def test_writer_refuses_score_without_band():
    with pytest.raises(A.FusionError):
        A.check_banded({"anomaly_score": 0.1, "p_anomaly_calibrated": 0.2})


def _banded(**overrides):
    rec = {"anomaly_score": 0.0, "p_anomaly_calibrated": 0.5,
           "ci_low": 0.1, "ci_high": 0.9, "n_boot": 1000, "ece_holdout": 0.01}
    rec.update(overrides)
    return rec


def test_check_banded_accepts_p_outside_raw_percentiles():
    """Raw 2.5/97.5 bands may omit p; the writer must still publish them (#52)."""
    rec = _banded(p_anomaly_calibrated=0.95, ci_low=0.10, ci_high=0.20)
    assert rec["p_anomaly_calibrated"] > rec["ci_high"]
    assert A.check_banded(rec) is rec
    rec = _banded(p_anomaly_calibrated=0.01, ci_low=0.10, ci_high=0.20)
    assert rec["p_anomaly_calibrated"] < rec["ci_low"]
    assert A.check_banded(rec) is rec


def test_published_ci_are_raw_bootstrap_percentiles():
    """ci_low/ci_high are the raw 2.5/97.5 percentiles, not widened to contain p."""
    import numpy as np
    cfg = C.load_config(CONFIG)
    scene = A._load_scene(CONFIG.parent, cfg["scenes"]["run"].format(seed=SEED))
    model = A.fit_calibrated(cfg, seed=SEED)
    X = A.features(cfg, scene)
    recs = A.score_scene(model, X)
    s = model.detector.decision_function(X)
    n = len(model.cal_s)
    boots = np.empty((A.N_BOOT, len(s)))
    for i in range(A.N_BOOT):
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([model.seed, i])))
        j = rng.integers(0, n, n)
        from sklearn.isotonic import IsotonicRegression
        boots[i] = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit(
            model.cal_s[j], model.cal_y[j]).predict(s)
    lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
    for k, rec in enumerate(recs):
        assert rec["ci_low"] == float(lo[k])
        assert rec["ci_high"] == float(hi[k])
        # Published ci must equal the raw percentiles (the clamp-detecting
        # regressions are the stub tests, including p-below-band).
    n_outside = sum(
        1 for k, rec in enumerate(recs)
        if not (lo[k] <= rec["p_anomaly_calibrated"] <= hi[k])
    )
    # Informational only (Verity note on #63): not a hard assertion. A fixture
    # or dependency bump may move this count. WR #61 evidence recorded 0/400.
    print(f"informational: seed 1002 raw-band out-of-band count is {n_outside}/{len(recs)}")


def test_score_scene_does_not_widen_band_to_contain_p():
    import numpy as np
    from types import SimpleNamespace
    n = 200
    model = A.Calibrated(
        detector=SimpleNamespace(decision_function=lambda X: np.array([0.3, 0.7])),
        iso=SimpleNamespace(predict=lambda s: np.array([0.9, 0.9])),   # p outside the band
        cal_s=np.linspace(0.0, 1.0, n), cal_y=np.zeros(n),             # every bootstrap fit predicts 0.0
        ece_holdout=0.01, brier_holdout=0.0, seed=SEED)
    recs = A.score_scene(model, np.zeros((2, 1)))
    for r in recs:
        assert r["p_anomaly_calibrated"] == 0.9
        assert r["ci_low"] == 0.0 and r["ci_high"] == 0.0   # old clamp would give ci_high == 0.9


def test_score_scene_does_not_widen_band_when_p_is_below():
    """Symmetric stub: p below the raw band. A restored min(lo, p) clamp would set ci_low == 0.1."""
    import numpy as np
    from types import SimpleNamespace
    n = 200
    model = A.Calibrated(
        detector=SimpleNamespace(decision_function=lambda X: np.array([0.3, 0.7])),
        iso=SimpleNamespace(predict=lambda s: np.array([0.1, 0.1])),  # p below the band
        cal_s=np.linspace(0.0, 1.0, n), cal_y=np.ones(n),              # every bootstrap fit predicts 1.0
        ece_holdout=0.01, brier_holdout=0.0, seed=SEED)
    recs = A.score_scene(model, np.zeros((2, 1)))
    for r in recs:
        assert r["p_anomaly_calibrated"] == 0.1
        assert r["ci_low"] == 1.0 and r["ci_high"] == 1.0  # old clamp would give ci_low == 0.1


def test_seed_1003_has_no_cell_outside_the_raw_band():
    """Seed 1003: published ci equals the raw band; out-of-band count is informational.

    Does not detect a reintroduced clamp (the clamp is a no-op on this seed too).
    """
    import numpy as np
    from sklearn.isotonic import IsotonicRegression
    seed = 1003
    cfg = C.load_config(CONFIG)
    scene = A._load_scene(CONFIG.parent, cfg["scenes"]["run"].format(seed=seed))
    model = A.fit_calibrated(cfg, seed=seed)
    X = A.features(cfg, scene)
    recs = A.score_scene(model, X)
    s = model.detector.decision_function(X)
    n = len(model.cal_s)
    boots = np.empty((A.N_BOOT, len(s)))
    for i in range(A.N_BOOT):
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([model.seed, i])))
        j = rng.integers(0, n, n)
        boots[i] = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit(
            model.cal_s[j], model.cal_y[j]).predict(s)
    lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
    n_outside = 0
    for k, rec in enumerate(recs):
        assert rec["ci_low"] == float(lo[k])
        assert rec["ci_high"] == float(hi[k])
        if not (lo[k] <= rec["p_anomaly_calibrated"] <= hi[k]):
            n_outside += 1
    # Informational only (Verity note on #63): not a hard assertion.
    print(f"informational: seed 1003 raw-band out-of-band count is {n_outside}/{len(recs)}")
    assert len(recs) == 400


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


def _rec(file_hash, **extra):
    rec = {"config_sha256": "aaa", "fusion_7.json": file_hash, "seed": 7}
    rec.update(extra)
    return rec


def test_replay_after_accept_drift_passes(tmp_path, monkeypatch, capsys):
    from sensegame.fusion import __main__ as cli
    ledger, argv = _seed_argv(tmp_path)
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps(_rec("old-hash"), sort_keys=True) + "\n")
    fresh = _rec("new-hash")
    monkeypatch.setattr(cli, "run", lambda *a, **k: dict(fresh))
    assert cli.main([*argv, "--accept-drift"]) == 0
    before = ledger.read_bytes()
    assert json.loads(ledger.read_text().splitlines()[-1])["drift_from"]
    assert cli.main([*argv, "--replay"]) == 0
    assert ledger.read_bytes() == before
    assert "replay OK" in capsys.readouterr().out


def test_replay_after_chained_accept_drift_passes(tmp_path, monkeypatch, capsys):
    from sensegame.fusion import __main__ as cli
    ledger, argv = _seed_argv(tmp_path)
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps(_rec("hash-a"), sort_keys=True) + "\n")
    steps = iter([_rec("hash-b"), _rec("hash-c"), _rec("hash-c")])
    monkeypatch.setattr(cli, "run", lambda *a, **k: dict(next(steps)))
    assert cli.main([*argv, "--accept-drift"]) == 0
    assert cli.main([*argv, "--accept-drift"]) == 0
    assert len(ledger.read_text().splitlines()) == 3
    before = ledger.read_bytes()
    assert cli.main([*argv, "--replay"]) == 0
    assert ledger.read_bytes() == before
    assert "replay OK" in capsys.readouterr().out


def test_replay_output_mismatch_exits_nonzero_and_appends_nothing(tmp_path, monkeypatch, capsys):
    from sensegame.fusion import __main__ as cli
    ledger, argv = _seed_argv(tmp_path)
    secret = "RAW-VALUE-SHOULD-NOT-LEAK-99"
    other = "OTHER-RAW-VALUE-SHOULD-NOT-LEAK-99"
    stored = _rec(secret, drift_from="previous-record-hash")
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps(stored, sort_keys=True) + "\n")
    before = ledger.read_bytes()
    monkeypatch.setattr(cli, "run", lambda *a, **k: _rec(other))
    assert cli.main([*argv, "--replay"]) != 0
    assert ledger.read_bytes() == before
    captured = capsys.readouterr()
    blob = captured.out + captured.err
    assert "REPLAY_MISMATCH" in captured.err
    assert "fusion_7.json" in captured.err
    assert "expected_sha256=" in captured.err
    assert "got_sha256=" in captured.err
    assert secret not in blob
    assert other not in blob
    assert "drift_from" not in captured.err


def _tamper_last_hex(ledger: Path, key: str) -> tuple[str, str]:
    """Change the last hex digit of one stored hash. Returns (original, tampered)."""
    lines = ledger.read_text().splitlines()
    rec = json.loads(lines[-1])
    original = rec[key]
    tampered = original[:-1] + ("0" if original[-1] != "0" else "1")
    if lines[-1].count(original) != 1:
        raise AssertionError(f"{key} hash is not unique on the last ledger line")
    lines[-1] = lines[-1].replace(original, tampered, 1)
    ledger.write_text("\n".join(lines) + "\n")
    return original, tampered


def _fusion_cli(sar: Path, *args):
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    env["PYTHONHASHSEED"] = "0"
    return subprocess.run(
        [sys.executable, "-m", "sensegame.fusion",
         "--seed", "1003",
         "--config", "sensegame/fusion/fixtures/fusion_config_synthetic.json",
         *args],
        cwd=sar, env=env, capture_output=True, text=True, check=False,
    )


def test_strata_seed_1003_accept_drift_then_replay(tmp_path):
    """Strata's reproduction: tamper, accept-drift, replay. cwd is sar/.

    Uses a temporary seeds.jsonl beside the run directories, never the repo ledger.
    """
    sar = PKG.parents[1]
    repo_ledger = sar.parent / "out" / "fusion" / "seeds.jsonl"
    repo_before = repo_ledger.read_bytes() if repo_ledger.exists() else None
    work = tmp_path / "strata"
    work.mkdir()
    ledger = work / "seeds.jsonl"

    first = _fusion_cli(sar, "--out", str(work / "run1"))
    assert first.returncode == 0, first.stderr
    assert ledger.is_file()
    assert len(ledger.read_text().splitlines()) == 1

    _tamper_last_hex(ledger, "fusion_1003.json")
    accepted = _fusion_cli(sar, "--accept-drift", "--out", str(work / "run2"))
    assert accepted.returncode == 0, accepted.stderr
    lines = ledger.read_text().splitlines()
    assert len(lines) == 2
    assert "drift_from" in json.loads(lines[-1])

    replay = _fusion_cli(sar, "--replay", "--out", str(work / "run3"))
    assert replay.returncode == 0, replay.stderr
    assert "replay OK" in replay.stdout
    assert len(ledger.read_text().splitlines()) == 2

    # Chained: tamper the accepted record, accept again, replay again.
    _tamper_last_hex(ledger, "fusion_1003.json")
    accepted_again = _fusion_cli(sar, "--accept-drift", "--out", str(work / "run4"))
    assert accepted_again.returncode == 0, accepted_again.stderr
    lines = ledger.read_text().splitlines()
    assert len(lines) == 3
    assert "drift_from" in json.loads(lines[-1])
    before_replay = ledger.read_bytes()
    replay_again = _fusion_cli(sar, "--replay", "--out", str(work / "run5"))
    assert replay_again.returncode == 0, replay_again.stderr
    assert ledger.read_bytes() == before_replay

    # A real mismatch still fails closed and does not dump the records.
    original, tampered = _tamper_last_hex(ledger, "fusion_1003.json")
    before_mismatch = ledger.read_bytes()
    mismatch = _fusion_cli(sar, "--replay", "--out", str(work / "run6"))
    assert mismatch.returncode != 0
    assert ledger.read_bytes() == before_mismatch
    blob = mismatch.stdout + mismatch.stderr
    assert "REPLAY_MISMATCH" in mismatch.stderr
    assert "keys=fusion_1003.json" in mismatch.stderr
    assert "expected_sha256=" in mismatch.stderr
    assert "got_sha256=" in mismatch.stderr
    assert "{" not in blob
    assert original not in blob
    assert tampered not in blob
    if repo_before is None:
        assert not repo_ledger.exists()
    else:
        assert repo_ledger.read_bytes() == repo_before


# 9 dependency pins (issue #53 / Cubic finding 4 on PR #42)
# Direct scientific pins plus pytest and scipy. A change to this set must fail the test.
FUSION_PINS = {
    "numpy": "2.2.6",
    "scikit-learn": "1.6.1",
    "pyod": "3.6.7",
    "rasterio": "1.4.3",
    "pytest": "9.2.0",
    "scipy": "1.18.1",
}


def _requirement_pins(path: Path = PKG / "requirements-fusion.txt") -> dict[str, str]:
    pins: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "==" not in line:
            raise AssertionError(f"unpinned requirement: {raw!r}")
        name, ver = line.split("==", 1)
        name, ver = name.strip(), ver.strip()
        if not name or not ver:
            raise AssertionError(f"empty name or version: {raw!r}")
        if name in pins:
            raise AssertionError(f"duplicate pin: {name}")
        pins[name] = ver
    return pins


def test_fusion_requirement_pins():
    assert _requirement_pins() == FUSION_PINS

