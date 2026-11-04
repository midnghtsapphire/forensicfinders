import numpy as np
import pytest
# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  This file had never executed. Two independent reasons, both now fixed:
#       (1) registry.json had no component covering forensic_pipeline/, so
#           `python3 sar/registry.py --test-all` never reached it. Now component 990.
#       (2) the import below could not resolve. `from sar.forensic_pipeline...` needs a
#           top-level package named `sar` on sys.path, and there is none -- sar/ is the
#           ROOT every component runs from (test_cwd "." means sar/), not a package. It
#           has no __init__.py and giving it one would re-root the whole registry. So the
#           import failed with `ModuleNotFoundError: No module named 'sar'` from every
#           directory it could be launched in.
# What: The module path loses its `sar.` prefix and becomes package-relative to sar/.
#       The original line is preserved verbatim in the REVVEL-DISABLED block below per
#       RVS-AGENT-001 (COMMENT-DONT-DELETE) -- nothing was removed. The imported names,
#       every test body, every assertion and every tolerance are untouched; the only
#       change is where Python looks for the module.
# What Worked: `from forensic_pipeline.snow_wells_pipes import ...` together with the two
#       new __init__.py files. Measured: 12 tests collected and passing, where the file
#       previously errored during collection.
# Notes: This suite runs under PYTEST, not unittest -- it is written pytest-style (bare
#       test_* functions, plain assert, pytest.approx on line 46). `unittest discover`
#       collects only TestCase subclasses, so registering this directory under a unittest
#       component would have collected ZERO tests and reported success. Component 990 uses
#       pytest for exactly that reason; see the entry in registry.json.
# ══════════════════════════════════════════════════════════════════════════════════════════

# REVVEL-DISABLED | AGENT: claude-code | MODEL: claude-opus-5 | WR: UNASSIGNED | DATE: 2026-11-04 | STATUS: REPLACED
# REASON: absolute import through a non-existent top-level `sar` package. sar/ is the
#         directory every registry component treats as its root, not an importable
#         package, so this line raised ModuleNotFoundError: No module named 'sar' and the
#         whole file errored during collection. Replaced by the package-relative import
#         below; the names bound are identical, so no test behaviour changes.
# PREVIOUS IMPORT, kept verbatim:
# from sar.forensic_pipeline.snow_wells_pipes import (
# OWNER: @midnghtsapphire
# REVVEL-DISABLED-END
from forensic_pipeline.snow_wells_pipes import (
    tree_well_residual,
    rootball_trench_residual,
    culvert_ice_trajectory,
    pipe_airflow_residual,
    local_image_accent,
    isrid_prior_map,
    finder_confirmation,
)

def test_tree_well_positive_void():
    ch = np.ones((40, 40)) * 3
    ch[10:15, 10:15] = 8
    sd = np.ones((40, 40)) * 1.5
    sd[10:15, 10:15] = 0.2
    out = tree_well_residual(ch, sd)
    assert out["residual"].max() > 0
    assert out["residual"][0, 0] == 0

def test_tree_well_no_trees():
    ch = np.ones((20, 20))
    sd = np.ones((20, 20))
    out = tree_well_residual(ch, sd)
    assert out["residual"].sum() == 0

def test_rootball_trench():
    dem = np.random.randn(30, 30)
    tree = np.zeros((30, 30), dtype=bool)
    tree[10:12, 10:12] = True
    trench = np.zeros((30, 30), dtype=bool)
    trench[15:18, :] = True
    out = rootball_trench_residual(dem, tree, trench)
    assert out["residual"].shape == dem.shape
    assert out["residual"].min() >= 0

def test_culvert_fighting_vs_stationary():
    stat = culvert_ice_trajectory(0.3, 1.0, 1.0, fighting=0)
    fight = culvert_ice_trajectory(0.3, 1.0, 1.0, fighting=1)
    assert fight["held_probability"] > stat["held_probability"]
    assert 0 <= fight["held_probability"] <= 1

def test_culvert_no_ice():
    out = culvert_ice_trajectory(0.5, 1.0, 0.0, fighting=0)
    assert out["exit_speed"] == pytest.approx(1.0)

def test_pipe_inversion_reduces_odor():
    normal = pipe_airflow_residual(0.5, 1.0, 5, 15, inversion=0)
    inverted = pipe_airflow_residual(0.5, 1.0, 5, 15, inversion=1)
    assert inverted["odor_strength"] < normal["odor_strength"]

def test_pipe_low_velocity_detectable():
    out = pipe_airflow_residual(0.4, 0.2, 0, 20, inversion=0)
    assert out["dog_detectable"] is True

def test_accent_invert_preserves_outside():
    img = np.full((30, 30), 100, dtype=np.uint8)
    mask = np.zeros((30, 30), dtype=bool)
    mask[5:10, 5:10] = True
    out = local_image_accent(img, mask, mode="invert")
    assert np.all(out[~mask] == 100)
    assert np.all(out[mask] == 155)  # 255-100

def test_accent_blowout_clips():
    img = np.random.randint(0, 50, (20, 20), dtype=np.uint8)
    mask = np.ones((20, 20), dtype=bool)
    out = local_image_accent(img, mask, mode="blowout")
    assert out.dtype == img.dtype
    assert out.max() <= 255

def test_isrid_prior_peaks_at_center():
    prior = isrid_prior_map((40, 40), (20, 20), category_radius=80)
    assert prior[20, 20] == prior.max()
    assert prior[0, 0] < prior[20, 20]

def test_isrid_different_radius():
    small = isrid_prior_map((30, 30), (15, 15), 50)
    large = isrid_prior_map((30, 30), (15, 15), 200)
    assert small[0, 0] < large[0, 0]

def test_finder_confirmation():
    mask = np.array([[True, False], [True, True]])
    assert not np.any(finder_confirmation(mask, False))
    confirmed = finder_confirmation(mask, True)
    assert np.array_equal(confirmed, mask)
