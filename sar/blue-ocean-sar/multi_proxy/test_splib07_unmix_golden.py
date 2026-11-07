# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Grok Bot as Sense-Quartz pair -- Quartz-N (Navigator, wrote tests first) and
#       Quartz-D (Driver, ran them against production), for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  test_nnls_sam_golden.py (PR #20) proves NNLS/SAM against synthetic Gaussian
#       endmembers. This file wires the same golden checks to REAL USGS splib07 spectra
#       vendored in PR #29, so recovered-abundance error is measured on lab spectra.
#       Registry component: 2360 (mineral-spectral-unmix; Verity: NEW-22 → 2360).
# What: Seeded (np.random.default_rng(20261104)) cube of 2-3 endmember mixtures of
#       kaolinite / calcite / goethite from reference_oracle/splib07_subset (offline only).
#       Asserts NNLS recovery (noise-free atol 1e-6, noisy atol 1e-2) and SAM ~0 for a
#       matching pure pixel vs larger for a mismatched reference.
#       pytest functions + unittest.TestCase adapter.
# Licence: UNLICENSED (private repo; licence pending Audrey)
# Source data: USGS Spectral Library Version 7, Kokaly et al. 2017, USGS Data Series 1035,
#       doi:10.3133/ds1035; data release doi:10.5066/F7RR1WDJ (public domain).
#       Existing synthetic Gaussian golden tests are left untouched.
# ══════════════════════════════════════════════════════════════════════════════════════════
import unittest

import numpy as np

from .nnls_unmix import constrained_nnls_unmix
from .sam import spectral_angle
from .splib07_endmembers import load_endmembers

SEED = 20261104
NAMES = ["kaolinite", "calcite", "goethite"]
H, W = 5, 6


def make_cube(noise_sigma=0.0, seed=SEED):
    ems = load_endmembers(NAMES)
    A = np.stack([ems[n] for n in NAMES], axis=1)  # (B, K)
    rng = np.random.default_rng(seed)
    truth = rng.dirichlet(np.ones(len(NAMES)), size=(H, W))  # 3-EM mixtures
    # Row 0: 2-EM mixtures (goethite absent); pixel (0,0) pure kaolinite.
    two = rng.uniform(0.2, 0.8, size=W)
    truth[0, :, 0], truth[0, :, 1], truth[0, :, 2] = two, 1 - two, 0.0
    truth[0, 0] = [1.0, 0.0, 0.0]
    cube = truth @ A.T
    if noise_sigma:
        cube = cube + rng.normal(0.0, noise_sigma, cube.shape)
    return ems, truth, cube


def _check_recovery(cube, ems, truth, atol):
    fracs, rms = constrained_nnls_unmix(cube, ems)
    for i, n in enumerate(NAMES):
        np.testing.assert_allclose(fracs[n], truth[..., i], atol=atol)
    return rms


def test_fixture_offline_and_shape():
    ems = load_endmembers(NAMES)
    lens = {v.shape for v in ems.values()}
    assert len(lens) == 1 and next(iter(lens))[0] > 10
    for v in ems.values():
        assert np.all(np.isfinite(v)) and v.min() >= 0 and v.max() <= 1


def test_seed_reproducible():
    _, _, c1 = make_cube(1e-3)
    _, _, c2 = make_cube(1e-3)
    assert np.array_equal(c1, c2)


def test_nnls_noise_free():
    ems, truth, cube = make_cube(0.0)
    rms = _check_recovery(cube, ems, truth, atol=1e-6)
    assert rms.max() < 1e-8


def test_nnls_noisy():
    ems, truth, cube = make_cube(1e-3)
    rms = _check_recovery(cube, ems, truth, atol=1e-2)
    assert rms.max() < 5e-3


def test_sam_match_vs_mismatch():
    ems, _, cube = make_cube(0.0)
    match = spectral_angle(cube, ems["kaolinite"])
    other = spectral_angle(cube, ems["goethite"])
    assert match[0, 0] < 1e-3
    assert other[0, 0] > 0.05
    assert other[0, 0] > 10 * max(match[0, 0], 1e-6)
    assert np.all((match >= 0) & (match <= np.pi))


class Splib07UnmixGolden(unittest.TestCase):
    def test_fixture_offline_and_shape(self):
        test_fixture_offline_and_shape()

    def test_seed_reproducible(self):
        test_seed_reproducible()

    def test_nnls_noise_free(self):
        test_nnls_noise_free()

    def test_nnls_noisy(self):
        test_nnls_noisy()

    def test_sam_match_vs_mismatch(self):
        test_sam_match_vs_mismatch()


if __name__ == "__main__":
    unittest.main()
