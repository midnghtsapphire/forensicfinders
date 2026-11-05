# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Grok Bot as Sense-Quartz pair (Quartz-N wrote tests first, Quartz-D drove) for Audrey Evans
# When: 2026-11-04
# Why:  HySUPP comparison harness (NEW-22 / registry 2360): baseline always runs, HySUPP
#       path skips cleanly when not configured. Offline, deterministic.
# Notes: Our code UNLICENSED (private repo; licence pending Audrey).
# ══════════════════════════════════════════════════════════════════════════════════════════
import json
import unittest

import numpy as np

from .hysupp_compare import (HySUPPUnavailable, _gaussian_endmembers, compare,
                             load_hysupp_fcls, make_mixtures, run_baseline_nnls,
                             abundance_rmse)


def test_baseline_runs_and_is_accurate():
    r = compare(include_hysupp=False)
    b = r["results"]["nnls_baseline"]
    assert b["status"] == "ok"
    assert b["abundance_rmse"] < 0.05
    json.dumps(r)


def test_deterministic_same_seed():
    assert compare(seed=7, include_hysupp=False) == compare(seed=7, include_hysupp=False)


def test_gaussian_noise_free_exact():
    E, names = _gaussian_endmembers(3, 120, np.random.default_rng(0))
    Y, A = make_mixtures(E, 32, seed=1)
    assert abundance_rmse(A, run_baseline_nnls(Y, E, names)) < 1e-6


def test_hysupp_reported_or_skipped():
    h = compare()["results"]["hysupp_fcls"]
    assert h["status"] in ("ok", "skipped")
    if h["status"] == "ok":
        assert h["abundance_rmse"] < 0.05


def test_no_spams_import_in_repo_harness():
    import pathlib, re
    src = (pathlib.Path(__file__).parent / "hysupp_compare.py").read_text()
    assert not re.search(r"^\s*(import|from)\s+spams", src, re.M)
    assert "exec_module" not in src


def test_external_runner_reads_result_json(tmp_path, monkeypatch):
    import sys
    script = tmp_path / "fake_cli.py"  # stands in for the out-of-repo runner
    script.write_text("import sys,json,numpy as np\nfrom scipy.optimize import nnls\n"
                      "d=np.load(sys.argv[1]);Y,E=d['Y'],d['E']\n"
                      "A=np.stack([nnls(E,y)[0] for y in Y.T],1)\n"
                      "json.dump({'A':A.tolist()},open(sys.argv[2],'w'))\n")
    monkeypatch.setenv("HYSUPP_ROOT", str(tmp_path))
    monkeypatch.setenv("SPAMS_COMPARE_CMD", f"{sys.executable} {script}")
    E, _ = _gaussian_endmembers(3, 60, np.random.default_rng(0))
    Y, A = make_mixtures(E, 8, seed=3)
    assert abundance_rmse(A, load_hysupp_fcls(workdir=str(tmp_path / "out"))(Y, E)) < 1e-6


class HySUPPCompareTests(unittest.TestCase):
    def test_baseline(self):
        test_baseline_runs_and_is_accurate()

    def test_deterministic(self):
        test_deterministic_same_seed()

    def test_gaussian(self):
        test_gaussian_noise_free_exact()

    def test_reported_or_skipped(self):
        test_hysupp_reported_or_skipped()

    def test_hysupp_fcls_matches_truth(self):
        try:
            fcls = load_hysupp_fcls()
        except HySUPPUnavailable as exc:
            self.skipTest(str(exc))
        E, _ = _gaussian_endmembers(3, 120, np.random.default_rng(0))
        Y, A = make_mixtures(E, 16, seed=2)
        self.assertLess(abundance_rmse(A, fcls(Y, E)), 1e-3)


if __name__ == "__main__":
    unittest.main()
