# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Grok Bot as Sense-Quartz pair -- Quartz-N (Navigator, wrote these tests first) and
#       Quartz-D (Driver), for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  Prove the shipped USGS splib07 PD subset loads offline, stays in AREF [0,1], and
#       that constrained_nnls_unmix recovers known abundances from a synthetic mixture of
#       two real endmembers (task B). Component NEW-22 / registry 2360.
# What: unittest + pytest-style functions (adapter pattern from test_engines.py).
# Notes: No network. No LUCAS. Fixture under fixtures/splib07_subset/ is public-domain
#       USGS data (doi:10.3133/ds1035). Our code UNLICENSED (private; licence pending Audrey).
# ══════════════════════════════════════════════════════════════════════════════════════════
import unittest

import numpy as np

from .nnls_unmix import constrained_nnls_unmix
from .sam import spectral_angle
from .splib07_endmembers import (
    fixture_dir,
    list_endmember_names,
    load_endmembers,
    load_manifest,
    wavelength_grid_um,
)

SEED = 20261104
MIX_NAMES = ("kaolinite", "hematite")


def test_fixture_files_present():
    d = fixture_dir()
    assert d.is_dir()
    for name in (
        "README.md",
        "manifest.json",
        "wavelengths_um.csv",
        "endmembers_reflectance.csv",
        "endmembers_aviris2014.npz",
    ):
        assert (d / name).is_file(), name
    ascii_src = d / "ascii_src"
    assert ascii_src.is_dir()
    assert (ascii_src / "s07_AV14_Wavelengths_in_microns_224_ch_AVIRIS14a.txt").is_file()


def test_manifest_cites_usgs_pd():
    m = load_manifest()
    assert "10.3133/ds1035" in m["report_doi"]
    assert "public domain" in m["licence"].lower()
    assert "LUCAS" in m["not_included"][0] or any("LUCAS" in x for x in m["not_included"])
    assert m["band_selection"]["n_kept"] == wavelength_grid_um().shape[0]


def test_load_shapes_and_range():
    em = load_endmembers()
    names = list_endmember_names()
    assert set(em) == set(names)
    assert 6 <= len(names) <= 12
    wl = wavelength_grid_um()
    assert wl.ndim == 1 and wl.shape[0] >= 100
    assert float(wl[0]) < float(wl[-1])
    # Wavelengths documented in micrometres (VNIR–SWIR).
    assert 0.3 < float(wl[0]) < 0.5
    assert 2.0 < float(wl[-1]) < 2.6
    for n, v in em.items():
        assert v.shape == wl.shape, (n, v.shape, wl.shape)
        assert np.isfinite(v).all()
        assert float(v.min()) >= 0.0
        assert float(v.max()) <= 1.0 + 1e-6


def test_load_subset_and_matrix():
    em = load_endmembers(["quartz", "calcite"])
    assert list(em.keys()) == ["quartz", "calcite"]
    wl, R, names = load_endmembers(["quartz", "calcite"], as_matrix=True)
    assert names == ["quartz", "calcite"]
    assert R.shape == (wl.shape[0], 2)
    np.testing.assert_allclose(R[:, 0], em["quartz"])


def test_load_is_deterministic():
    a = load_endmembers()
    b = load_endmembers()
    for k in a:
        assert a[k].tobytes() == b[k].tobytes()


def test_nnls_recovers_two_endmember_mixture_noise_free():
    em_all = load_endmembers(list(MIX_NAMES))
    a, b = em_all[MIX_NAMES[0]], em_all[MIX_NAMES[1]]
    # Known abundances on a tiny cube.
    truth_a = np.array([[0.7, 0.3], [1.0, 0.0]])
    truth_b = 1.0 - truth_a
    cube = np.zeros((2, 2, a.shape[0]))
    for r in range(2):
        for c in range(2):
            cube[r, c] = truth_a[r, c] * a + truth_b[r, c] * b
    fracs, rms = constrained_nnls_unmix(cube, em_all)
    np.testing.assert_allclose(fracs[MIX_NAMES[0]], truth_a, atol=1e-6)
    np.testing.assert_allclose(fracs[MIX_NAMES[1]], truth_b, atol=1e-6)
    assert float(rms.max()) < 1e-8


def test_nnls_recovers_two_endmember_mixture_noisy():
    rng = np.random.default_rng(SEED)
    em_all = load_endmembers(list(MIX_NAMES))
    a, b = em_all[MIX_NAMES[0]], em_all[MIX_NAMES[1]]
    truth_a = np.array([[0.65, 0.40], [0.85, 0.15]])
    truth_b = 1.0 - truth_a
    cube = np.zeros((2, 2, a.shape[0]))
    for r in range(2):
        for c in range(2):
            cube[r, c] = truth_a[r, c] * a + truth_b[r, c] * b
    cube = cube + rng.normal(0.0, 1e-3, cube.shape)
    fracs, rms = constrained_nnls_unmix(cube, em_all)
    for name, truth in ((MIX_NAMES[0], truth_a), (MIX_NAMES[1], truth_b)):
        err = np.abs(fracs[name] - truth)
        assert float(err.max()) < 1e-2, (name, float(err.max()))
    total = fracs[MIX_NAMES[0]] + fracs[MIX_NAMES[1]]
    np.testing.assert_allclose(total, 1.0, atol=1e-9)


def test_sam_pure_pixel_near_zero():
    em = load_endmembers(["kaolinite", "hematite"])
    cube = np.zeros((1, 2, em["kaolinite"].shape[0]))
    cube[0, 0] = em["kaolinite"]
    cube[0, 1] = em["hematite"]
    ang_k = spectral_angle(cube, em["kaolinite"])
    ang_h = spectral_angle(cube, em["hematite"])
    assert float(ang_k[0, 0]) < 1e-6
    assert float(ang_h[0, 1]) < 1e-6
    assert float(ang_k[0, 1]) > 0.05
    assert float(ang_h[0, 0]) > 0.05


class Splib07Endmembers(unittest.TestCase):
    """unittest adapter so pytest-style functions run under component 100 discover."""

    def test_fixture_files_present(self):
        test_fixture_files_present()

    def test_manifest_cites_usgs_pd(self):
        test_manifest_cites_usgs_pd()

    def test_load_shapes_and_range(self):
        test_load_shapes_and_range()

    def test_load_subset_and_matrix(self):
        test_load_subset_and_matrix()

    def test_load_is_deterministic(self):
        test_load_is_deterministic()

    def test_nnls_noise_free(self):
        test_nnls_recovers_two_endmember_mixture_noise_free()

    def test_nnls_noisy(self):
        test_nnls_recovers_two_endmember_mixture_noisy()

    def test_sam_pure_pixel(self):
        test_sam_pure_pixel_near_zero()


if __name__ == "__main__":
    unittest.main()
