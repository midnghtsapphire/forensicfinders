# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Grok Bot as Sense-Quartz pair -- Quartz-N (Navigator, wrote these tests first) and
#       Quartz-D (Driver, ran them against production), for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  nnls_unmix.py and sam.py had only one smoke test (nnls) and no SAM test at all.
#       A smoke test proves the code runs; it does not prove the recovered abundances are
#       right. Golden tests against KNOWN synthetic abundances measure unmixing error.
#       Registry component: NEW-22 (mineral-spectral-unmix, provisional id from Strata).
# What: Seeded (np.random.default_rng(20261104)) synthetic cube built from 4 analytic
#       endmembers over 16 bands, with stored ground-truth abundance maps. Asserts:
#         - NNLS fractions match truth (atol 1e-2 with noise, 1e-6 noise-free)
#         - RMS residual is low on pure pixels
#         - SAM angle ~0 for a matching reference, larger for a mismatched one
#         - same seed -> byte-identical cube
#       Bare pytest functions plus a unittest.TestCase adapter (same pattern as
#       test_engines.py) so component 100's `unittest discover` collects them.
# Notes: ENDMEMBERS ARE SYNTHETIC STAND-INS for USGS Spectral Library v7 (splib07,
#       public domain, https://doi.org/10.5066/F7RR1WDJ). Shapes are textbook analytic
#       forms: Gaussian absorption features (Clark et al. 1990, JGR 95(B8):12653) on a
#       flat or linear-ramp continuum. A real splib07 subset fixture is task B.
#       No production module was changed; both passed as written.
# ══════════════════════════════════════════════════════════════════════════════════════════
import unittest

import numpy as np

from .nnls_unmix import constrained_nnls_unmix
from .sam import spectral_angle

SEED = 20261104
BANDS = 16
H, W = 6, 7
WL = np.linspace(0.4, 2.5, BANDS)  # micrometres, VNIR-SWIR span of splib07


def _gauss_absorption(center, width, depth, continuum):
    return continuum * (1.0 - depth * np.exp(-0.5 * ((WL - center) / width) ** 2))


def make_endmembers():
    """Four synthetic stand-ins for splib07 mineral spectra (reflectance 0..1)."""
    return {
        "kaolinite_like": _gauss_absorption(2.2, 0.08, 0.5, np.full(BANDS, 0.8)),
        "hematite_like": _gauss_absorption(0.9, 0.15, 0.6, 0.2 + 0.25 * (WL - 0.4)),
        "calcite_like": _gauss_absorption(2.34, 0.06, 0.4, np.full(BANDS, 0.6)),
        "vegetation_like": np.where(WL < 0.7, 0.05, 0.5) * (1.0 - 0.3 * (WL > 1.4)),
    }


def make_cube(noise_sigma=1e-3, seed=SEED):
    rng = np.random.default_rng(seed)
    em = make_endmembers()
    keys = list(em)
    A = np.stack([em[k] for k in keys], axis=1)
    ab = rng.dirichlet(np.ones(len(keys)), size=(H, W))  # (H, W, K), sums to 1
    # Pure pixels on the first row for residual / SAM checks.
    for i in range(len(keys)):
        ab[0, i] = np.eye(len(keys))[i]
    cube = ab @ A.T
    if noise_sigma:
        cube = cube + rng.normal(0.0, noise_sigma, cube.shape)
    truth = {k: ab[..., i] for i, k in enumerate(keys)}
    return cube, em, truth


def test_seed_reproducible():
    a, _, _ = make_cube()
    b, _, _ = make_cube()
    assert a.tobytes() == b.tobytes()


def test_nnls_recovers_known_abundances_noise_free():
    cube, em, truth = make_cube(noise_sigma=0.0)
    fracs, rms = constrained_nnls_unmix(cube, em)
    for k in em:
        np.testing.assert_allclose(fracs[k], truth[k], atol=1e-6)
    assert rms.max() < 1e-8


def test_nnls_recovers_known_abundances_noisy():
    cube, em, truth = make_cube(noise_sigma=1e-3)
    fracs, rms = constrained_nnls_unmix(cube, em)
    for k in em:
        err = np.abs(fracs[k] - truth[k])
        assert err.max() < 1e-2, (k, err.max())
    total = sum(fracs.values())
    np.testing.assert_allclose(total, 1.0, atol=1e-9)
    assert rms[0, :4].max() < 3e-3  # pure pixels: residual ~ noise floor


def test_sam_match_vs_mismatch():
    cube, em, _ = make_cube(noise_sigma=1e-3)
    ang_match = spectral_angle(cube, em["kaolinite_like"])
    ang_other = spectral_angle(cube, em["hematite_like"])
    assert ang_match[0, 0] < 0.01  # pixel (0,0) is pure kaolinite_like
    assert ang_other[0, 0] > 0.1
    assert ang_other[0, 0] > 10 * ang_match[0, 0]
    assert np.all((ang_match >= 0) & (ang_match <= np.pi))


class NnlsSamGolden(unittest.TestCase):
    """unittest adapter so the pytest-style functions above run under component 100."""

    def test_seed_reproducible(self):
        test_seed_reproducible()

    def test_nnls_noise_free(self):
        test_nnls_recovers_known_abundances_noise_free()

    def test_nnls_noisy(self):
        test_nnls_recovers_known_abundances_noisy()

    def test_sam_match_vs_mismatch(self):
        test_sam_match_vs_mismatch()


if __name__ == "__main__":
    unittest.main()
