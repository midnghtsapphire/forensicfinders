"""WR #62 (follow-up to PR #60): one Sentinel GeoTIFF parser, no dead code, pinned versions.

Synthetic data only: every GeoTIFF here is built in memory with rasterio. Nothing calls
the live Sentinel Hub API and nothing reads real imagery or PII.

What each test pins (Verity post-merge review of #60, issue #62):
  * test_no_unreachable_statements_in_sentinel  -> Sonar python:S1763 at the old L286
  * test_deprecated_alias_*                     -> one parser; old name kept as thin alias
  * test_both_names_agree_*                     -> same NaN mask + transform on the 3x3 fixture
  * test_pinned_test_requirements_*             -> CI installs exactly the requirements.txt pins
  * test_running_environment_matches_pins       -> only enforced in the pinned CI job
"""

from __future__ import annotations

import ast
import importlib.metadata as md
import io
import os
import re
import warnings
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from coldtrace.backend.services import sentinel

BACKEND = Path(__file__).resolve().parents[1]
SENTINEL_SRC = BACKEND / "services" / "sentinel.py"

# Same synthetic 3x3 grid as test_sentinel_dataarray.py; (1, 1) is the -9999 sentinel.
_GRID = np.array(
    [[0.10, 0.20, 0.30], [0.40, -9999.0, 0.50], [0.60, 0.70, 0.80]], dtype=np.float32
)


def _tiff(data: np.ndarray, *, nodata_tag: float | None, crs: str | None = "EPSG:4326") -> bytes:
    """Single-band FLOAT32 GeoTIFF in memory; nodata_tag=None mimics the real Hub body."""
    profile = {
        "driver": "GTiff", "height": data.shape[0], "width": data.shape[1], "count": 1,
        "dtype": "float32", "transform": from_origin(-105.05, 40.05, 0.01, 0.01),
    }
    if crs is not None:
        profile["crs"] = crs
    if nodata_tag is not None:
        profile["nodata"] = nodata_tag
    buf = io.BytesIO()
    with rasterio.open(buf, "w", **profile) as dst:
        dst.write(data, 1)
    return buf.getvalue()


def _call_alias(payload: bytes):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return sentinel._tiff_to_ndvi_array(payload)


# ── Sonar S1763: no statement may follow return/raise/continue/break in a block ─────────

def _unreachable_statements(tree: ast.AST) -> list[int]:
    dead: list[int] = []
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if not isinstance(block, list):
                continue
            for i, stmt in enumerate(block[:-1]):
                if isinstance(stmt, (ast.Return, ast.Raise, ast.Continue, ast.Break)):
                    dead.append(block[i + 1].lineno)
    return dead


def test_no_unreachable_statements_in_sentinel():
    tree = ast.parse(SENTINEL_SRC.read_text(encoding="utf-8"))
    assert _unreachable_statements(tree) == []


def test_unreachable_detector_catches_the_old_l286_shape():
    """Guard the guard: the detector must flag the exact pattern #60 shipped."""
    src = "def f():\n    return 1\n    return 2\n"
    assert _unreachable_statements(ast.parse(src)) == [3]


# ── one parser, old name kept as a deprecated alias ─────────────────────────────────────

def test_deprecated_alias_still_exists_and_warns():
    assert callable(sentinel._tiff_to_ndvi_array)
    with pytest.warns(DeprecationWarning, match="geotiff_bytes_to_ndvi_dataarray"):
        sentinel._tiff_to_ndvi_array(_tiff(_GRID, nodata_tag=None))


def test_deprecated_alias_delegates_to_the_shared_parser(monkeypatch):
    marker = object()
    seen = []

    def fake(payload):
        seen.append(payload)
        return marker

    monkeypatch.setattr(sentinel, "geotiff_bytes_to_ndvi_dataarray", fake)
    assert _call_alias(b"payload") is marker
    assert seen == [b"payload"]


@pytest.mark.parametrize("nodata_tag", [None, -9999.0], ids=["hub-style-no-tag", "tagged"])
def test_both_names_agree_on_nan_mask_and_transform(nodata_tag):
    payload = _tiff(_GRID, nodata_tag=nodata_tag)
    shared = sentinel.geotiff_bytes_to_ndvi_dataarray(payload)
    legacy = _call_alias(payload)
    assert shared.shape == legacy.shape == (3, 3)
    np.testing.assert_array_equal(np.isnan(shared.values), np.isnan(legacy.values))
    assert bool(np.isnan(shared.values[1, 1])) and int(np.isnan(shared.values).sum()) == 1
    np.testing.assert_array_equal(shared.values, legacy.values)
    assert shared.rio.transform() == legacy.rio.transform()
    assert shared.rio.crs == legacy.rio.crs


def test_hub_style_body_without_nodata_tag_maps_sentinel_to_nan():
    """The real Hub response declares no nodata tag, so masked=True alone cannot mask it."""
    da = sentinel.geotiff_bytes_to_ndvi_dataarray(_tiff(_GRID, nodata_tag=None))
    assert da.dims == ("y", "x")
    assert np.isnan(da.values[1, 1])
    assert not np.isnan(da.values[0, 0])


def test_valid_negative_ndvi_is_not_masked():
    grid = _GRID.copy()
    grid[0, 0] = -0.3  # water / bare rock: a valid observation, not missing data
    da = sentinel.geotiff_bytes_to_ndvi_dataarray(_tiff(grid, nodata_tag=None))
    assert da.values[0, 0] == pytest.approx(-0.3)


def test_alias_inherits_the_fail_loud_checks():
    """Before WR #62 the old parser silently accepted a body with no CRS."""
    with pytest.raises(ValueError, match="CRS"):
        _call_alias(_tiff(_GRID, nodata_tag=None, crs=None))


def test_parsed_array_is_fully_loaded_not_lazy():
    """The buffer is closed after parsing; a lazy array would read a dead file handle."""
    da = sentinel.geotiff_bytes_to_ndvi_dataarray(_tiff(_GRID, nodata_tag=None))
    assert da.variable._in_memory
    assert da.chunks is None


def test_fetch_docstring_no_longer_points_at_the_duplicate_parser_alone():
    doc = sentinel.fetch_sentinel_ndvi.__doc__ or ""
    assert "geotiff_bytes_to_ndvi_dataarray" in doc


# ── pinned versions: requirements.txt is the single source of truth ─────────────────────

_PIN_NAMES = ("rasterio", "rioxarray", "xarray")


def _pins(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*([A-Za-z0-9_.\-]+)(\[[^\]]*\])?==([^\s#;]+)", line)
        if m:
            out[m.group(1).lower().replace("_", "-")] = m.group(3)
    return out


def test_pinned_test_requirements_exist_and_match_requirements_txt():
    prod = _pins(BACKEND / "requirements.txt")
    test_pins = _pins(BACKEND / "requirements-test-pinned.txt")
    assert {n: test_pins.get(n) for n in _PIN_NAMES} == {
        "rasterio": "1.3.10", "rioxarray": "0.15.5", "xarray": "2024.5.0",
    }
    # Every ==pin in the test file must be byte-identical to requirements.txt.
    mismatched = {n: (v, prod.get(n)) for n, v in test_pins.items() if prod.get(n) != v}
    assert mismatched == {}


@pytest.mark.skipif(
    os.environ.get("COLDTRACE_PINNED_ENV") != "1",
    reason="enforced only in the pinned CI job (COLDTRACE_PINNED_ENV=1); other jobs run newer wheels on purpose",
)
def test_running_environment_matches_pins():
    prod = _pins(BACKEND / "requirements.txt")
    for name in _PIN_NAMES:
        assert md.version(name) == prod[name], name


# ── extra guards added with the consolidation ───────────────────────────────────────────

def test_cloud_sentinel_and_nodata_constants_are_the_same_value():
    assert sentinel._CLOUD_SENTINEL == sentinel._SENTINEL_NODATA == -9999.0


@pytest.mark.parametrize("shape", [(1, 4), (4, 1)], ids=["one-row", "one-column"])
def test_single_row_or_column_raster_keeps_y_and_x_axes(shape):
    """Squeezing every length-1 axis (the #60 version) would drop y or x here."""
    data = np.linspace(0.1, 0.4, shape[0] * shape[1], dtype=np.float32).reshape(shape)
    da = sentinel.geotiff_bytes_to_ndvi_dataarray(_tiff(data, nodata_tag=None))
    assert da.dims == ("y", "x")
    assert da.shape == shape
