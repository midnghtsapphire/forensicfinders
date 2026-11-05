"""Failing-first goldens for the DEM-derived grid layer (proposed registry 2380).

Spec: ../dem-layer-spec.md
Collection fails with ImportError until sar/sensegame/dem_layer.py exists.
Same-seed cases also import sensegame.dem (registry 2320). No sweep width is set here.
"""
import math
import struct

import pytest

from sensegame.dem_layer import (  # noqa: E402  (module is not in this PR)
    REGISTRY_ID,
    REJECTED_GEO_KEYS,
    Layer,
    LayerError,
    derive,
)

RAMP3 = [[1000.0, 1000.5, 1001.0] for _ in range(3)]
RAMP3_SLOPE = [
    [0.125, 0.25, 0.125],
    [0.125, 0.25, 0.125],
    [0.125, 0.25, 0.125],
]
RAMP3_ROUGH = [
    [0.23570226039551584, 0.408248290463863, 0.23570226039551584],
    [0.23570226039551584, 0.408248290463863, 0.23570226039551584],
    [0.23570226039551584, 0.408248290463863, 0.23570226039551584],
]
RAMP4_ROW = [0.125, 0.25, 0.25, 0.125]
VAR = [
    [0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 2.0],
]
VAR_SLOPE = [
    [0.1767766952966369, 0.25, 0.1767766952966369],
    [0.25, 0.3535533905932738, 0.75],
    [0.1767766952966369, 0.75, 0.8838834764831844],
]
RAMP_SLOPE_JSON = (
    '{"cell_m":2,"degenerate":true,"excluded":true,"kind":"slope","provenance":{},'
    '"registry_id":2380,"shape":[3,3],"units":"m/m",'
    '"values":[[0.125,0.25,0.125],[0.125,0.25,0.125],[0.125,0.25,0.125]]}\n'
)
FLAT_SLOPE_JSON = (
    '{"cell_m":1,"degenerate":true,"excluded":true,"kind":"slope","provenance":{},'
    '"registry_id":2380,"shape":[4,4],"units":"m/m",'
    '"values":[[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]}\n'
)
PROV = {
    "epoch": None,
    "fixture": "fixtures/dem_synthetic_1001.tif",
    "generator_version": "0",
    "seed": 1001,
}


def _rows(layer):
    return [[float(v) for v in row] for row in layer.values]


def _assert_grid(layer, kind, units, cell_m, shape, degenerate):
    assert isinstance(layer, Layer)
    assert layer.kind == kind and layer.units == units
    assert layer.cell_m == cell_m
    assert layer.values.shape == shape
    assert layer.values.dtype.str == "<f8"
    assert layer.values.flags.c_contiguous
    assert layer.values.flags.writeable is False
    assert layer.degenerate is degenerate
    assert layer.excluded is degenerate
    assert REGISTRY_ID == 2380


def test_registry_and_geo_key_set():
    assert REGISTRY_ID == 2380
    for key in ("lat", "lon", "latitude", "longitude", "address"):
        assert key in REJECTED_GEO_KEYS


def test_flat_slope_flagged_values_stay_zero():
    dem = [[1000.0, 1000.0, 1000.0, 1000.0] for _ in range(4)]
    layer = derive(dem, kind="slope", cell_m=1.0)
    _assert_grid(layer, "slope", "m/m", 1.0, (4, 4), True)
    assert _rows(layer) == [[0.0, 0.0, 0.0, 0.0] for _ in range(4)]
    text = layer.to_json()
    assert text == FLAT_SLOPE_JSON
    assert "normalised" not in text and "contribution" not in text


def test_flat_roughness_flagged_values_stay_zero():
    dem = [[1000.0] * 3 for _ in range(3)]
    layer = derive(dem, kind="roughness", cell_m=1.0)
    _assert_grid(layer, "roughness", "m", 1.0, (3, 3), True)
    assert _rows(layer) == [[0.0, 0.0, 0.0] for _ in range(3)]


def test_ramp_slope_nonzero_but_mad_zero():
    """Six 0.125 and three 0.25 → median 0.125 → MAD 0. Values are kept."""
    layer = derive(RAMP3, kind="slope", cell_m=2.0)
    _assert_grid(layer, "slope", "m/m", 2.0, (3, 3), True)
    assert _rows(layer) == RAMP3_SLOPE
    assert layer.to_json() == RAMP_SLOPE_JSON
    assert any(v == 0.25 for row in _rows(layer) for v in row)
    assert layer.values.tobytes()[:8] == struct.pack("<d", 0.125)


def test_ramp_roughness_closed_form():
    layer = derive(RAMP3, kind="roughness", cell_m=2.0)
    _assert_grid(layer, "roughness", "m", 2.0, (3, 3), True)
    assert _rows(layer) == RAMP3_ROUGH
    assert _rows(layer)[0][0] == math.sqrt(1.0 / 18.0)
    assert _rows(layer)[0][1] == math.sqrt(1.0 / 6.0)


def test_ramp_3x4_even_median_not_degenerate():
    """6 and 6 split: median (0.125+0.25)/2 = 0.1875, MAD 0.0625."""
    dem = [[1000.0, 1000.5, 1001.0, 1001.5] for _ in range(3)]
    layer = derive(dem, kind="slope", cell_m=2.0)
    _assert_grid(layer, "slope", "m/m", 2.0, (3, 4), False)
    assert _rows(layer) == [RAMP4_ROW for _ in range(3)]


def test_varied_slope_mad_nonzero():
    layer = derive(VAR, kind="slope", cell_m=1.0)
    _assert_grid(layer, "slope", "m/m", 1.0, (3, 3), False)
    assert _rows(layer) == VAR_SLOPE
    assert layer.values.tobytes() == struct.pack("<9d", *[v for row in VAR_SLOPE for v in row])


def test_slope_scales_with_cell_m_roughness_does_not():
    slope_2 = derive(RAMP3, kind="slope", cell_m=2.0)
    slope_4 = derive(RAMP3, kind="slope", cell_m=4.0)
    assert _rows(slope_4) == [[0.0625, 0.125, 0.0625] for _ in range(3)]
    assert slope_2.values.tobytes() != slope_4.values.tobytes()
    rough_1 = derive(RAMP3, kind="roughness", cell_m=1.0)
    rough_2 = derive(RAMP3, kind="roughness", cell_m=2.0)
    assert rough_1.values.tobytes() == rough_2.values.tobytes()
    assert rough_1.to_json() != rough_2.to_json()


def test_same_array_is_byte_identical():
    a = derive(RAMP3, kind="slope", cell_m=2.0, provenance=dict(PROV))
    b = derive([row[:] for row in RAMP3], kind="slope", cell_m=2.0, provenance=dict(PROV))
    assert a.values.tobytes() == b.values.tobytes()
    assert a.to_json() == b.to_json()


def test_provenance_does_not_change_values():
    a = derive(VAR, kind="slope", cell_m=1.0, provenance={"seed": 1001, "epoch": None})
    b = derive(VAR, kind="slope", cell_m=1.0, provenance={"seed": 1003, "epoch": "b"})
    assert a.values.tobytes() == b.values.tobytes()
    assert a.to_json() != b.to_json()
    assert a.degenerate is False and b.degenerate is False


def test_same_seed_identical_layer():
    from sensegame.dem import generate

    prov = dict(PROV)
    a = derive(generate(1001), kind="slope", cell_m=1.0, provenance=prov)
    b = derive(generate(1001), kind="slope", cell_m=1.0, provenance=prov)
    assert a.values.shape == (257, 257)
    assert a.values.tobytes() == b.values.tobytes()
    assert a.to_json() == b.to_json()


def test_different_seed_or_epoch_changes_layer():
    from sensegame.dem import generate

    s1001 = derive(generate(1001), kind="slope", cell_m=1.0, provenance={"seed": 1001, "epoch": None})
    s1003 = derive(generate(1003), kind="slope", cell_m=1.0, provenance={"seed": 1003, "epoch": None})
    assert s1001.values.tobytes() != s1003.values.tobytes()
    a = derive(generate(1002, "a"), kind="roughness", cell_m=1.0, provenance={"seed": 1002, "epoch": "a"})
    b = derive(generate(1002, "b"), kind="roughness", cell_m=1.0, provenance={"seed": 1002, "epoch": "b"})
    assert a.values.tobytes() != b.values.tobytes()


def test_module_does_not_pull_in_the_scorer():
    import sys

    import sensegame.dem_layer as mod

    assert "sensegame.search_core" not in sys.modules
    assert not hasattr(mod, "CleanScorer")
    assert not hasattr(mod, "M1_W_KM")


@pytest.mark.parametrize("key", ["lat", "lon", "latitude", "longitude", "address", "Lat", "lng"])
def test_rejects_geographic_keys(key):
    with pytest.raises(LayerError):
        derive(RAMP3, kind="slope", cell_m=1.0, provenance={key: 1})


@pytest.mark.parametrize(
    "fixture",
    [
        "case/dem_synthetic_1001.tif",
        "fixtures/real.tif",
        "fixtures/../dem_synthetic_1001.tif",
        "/tmp/fixtures/dem_synthetic_1001.tif",
        "hfmr/dem_synthetic_1001.tif",
    ],
)
def test_rejects_bad_fixture_provenance(fixture):
    with pytest.raises(LayerError):
        derive(RAMP3, kind="slope", cell_m=1.0, provenance={"fixture": fixture})


@pytest.mark.parametrize(
    "kwargs",
    [
        {"kind": "aspect", "cell_m": 1.0},
        {"kind": "slope", "cell_m": 0.0},
        {"kind": "slope", "cell_m": -1.0},
        {"kind": "slope", "cell_m": float("nan")},
    ],
)
def test_rejects_bad_kind_or_cell(kwargs):
    with pytest.raises(LayerError):
        derive(RAMP3, **kwargs)


def test_rejects_small_nonfinite_and_nodata():
    with pytest.raises(LayerError):
        derive([[0.0, 0.0], [0.0, 0.0]], kind="slope", cell_m=1.0)
    with pytest.raises(LayerError):
        derive([[0.0, 0.0, float("nan")], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], kind="slope", cell_m=1.0)
    with pytest.raises(LayerError):
        derive([[0.0, 0.0, -9999.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], kind="slope", cell_m=1.0)
    with pytest.raises(LayerError):
        derive({"lat": 1.0, "values": RAMP3}, kind="slope", cell_m=1.0)
