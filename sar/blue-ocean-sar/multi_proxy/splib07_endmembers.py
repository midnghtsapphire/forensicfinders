# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Grok Bot as Sense-Quartz pair -- Quartz-N (Navigator) / Quartz-D (Driver),
#       for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  constrained_nnls_unmix / spectral_angle need real public-domain endmember spectra
#       on a shared wavelength grid. Task A golden tests used synthetic Gaussians; this
#       module loads a SHIPPED USGS Spectral Library v7 (splib07) subset so tests and
#       training never need the network or the multi-GB archive.
# What: Deterministic offline loader for reference_oracle/splib07_subset/. Returns reflectance
#       vectors (B,) on the shared AVIRIS-2014 micrometre grid (water windows dropped).
# Notes: Component NEW-22 / registry 2360 (pending Verity). Data is USGS PD
#       (doi:10.3133/ds1035); our code UNLICENSED (private repo; licence pending Audrey).
#       LUCAS is NOT included. No Ultralytics. No case/hfmr/evidence paths.
# ══════════════════════════════════════════════════════════════════════════════════════════
"""Offline loader for a small USGS Spectral Library v7 (splib07) endmember subset.

Wavelengths are in **micrometres (µm)** on the AVIRIS-Classic 2014 convolution grid
shipped under ``reference_oracle/splib07_subset/``. Default band selection drops the AVIRIS
water-vapor windows 1.35–1.45 µm and 1.80–1.95 µm (see ``manifest.json``). No
resampling is performed at load time — spectra were already convolved by USGS to that
sensor grid before we vendored the ASCII columns.

Reflectance is absolute reflectance (AREF), unitless, typically in ``[0, 1]``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

import numpy as np

_ORACLE_DIR = Path(__file__).resolve().parent / "reference_oracle" / "splib07_subset"
_NPZ_NAME = "endmembers_aviris2014.npz"
_MANIFEST_NAME = "manifest.json"
_CSV_NAME = "endmembers_reflectance.csv"

# USGS deleted-band sentinel (SPECPR). Present for documentation; the shipped AVIRIS
# subset has no deleted markers after water-window filtering.
DELETED_BAND_SENTINEL = -1.0e34


def reference_oracle_dir() -> Path:
    """Absolute path to the shipped splib07 subset reference-oracle directory.

    Real USGS PD spectra (not synthetic mixture fixtures). Path:
    ``reference_oracle/splib07_subset/``.
    """
    return _ORACLE_DIR


def fixture_dir() -> Path:
    """Deprecated alias for :func:`reference_oracle_dir` (kept for call-site compat)."""
    return reference_oracle_dir()


def load_manifest() -> dict:
    """Return the fixture manifest (citation, band selection, endmember catalogue)."""
    path = _ORACLE_DIR / _MANIFEST_NAME
    with path.open() as f:
        return json.load(f)


def list_endmember_names() -> list[str]:
    """Canonical short names available in the fixture (stable order from the NPZ)."""
    data = _load_npz()
    return [str(n) for n in data["names"].tolist()]


def wavelength_grid_um(*, full: bool = False) -> np.ndarray:
    """Shared wavelength grid in micrometres.

    Parameters
    ----------
    full :
        If False (default), return the kept grid used by ``load_endmembers``
        (water windows removed). If True, return the full 224-channel AVIRIS-2014 grid.
    """
    data = _load_npz()
    key = "full_wavelengths_um" if full else "wavelengths_um"
    return np.asarray(data[key], dtype=np.float64).copy()


def load_endmembers(
    names: Optional[Sequence[str]] = None,
    *,
    as_matrix: bool = False,
) -> Mapping[str, np.ndarray] | tuple[np.ndarray, np.ndarray, list[str]]:
    """Load reflectance endmembers on the shared wavelength grid.

    Parameters
    ----------
    names :
        Optional subset of canonical short names (e.g. ``["quartz", "kaolinite"]``).
        ``None`` loads every endmember in fixture order.
    as_matrix :
        If True, return ``(wavelengths_um, reflectance_BxK, names_list)`` instead of a dict.

    Returns
    -------
    dict[str, np.ndarray]
        Mapping short name → reflectance vector shape ``(B,)`` with ``B`` equal to
        ``wavelength_grid_um().shape[0]``. Values are absolute reflectance in ``[0, 1]``.

    Notes
    -----
    Fully offline: reads only committed fixture files under
    ``reference_oracle/splib07_subset/``. Prefer the compressed NPZ; fall back to the CSV if
    the NPZ is missing (regen path documented in the fixture README).
    """
    data = _load_npz()
    all_names = [str(n) for n in data["names"].tolist()]
    wavelengths = np.asarray(data["wavelengths_um"], dtype=np.float64)
    reflectance = np.asarray(data["reflectance"], dtype=np.float64)  # (B, K)

    if names is None:
        selected = all_names
    else:
        unknown = [n for n in names if n not in all_names]
        if unknown:
            raise KeyError(
                f"Unknown endmember name(s) {unknown!r}; available: {all_names}"
            )
        selected = list(names)

    index = {n: i for i, n in enumerate(all_names)}
    cols = [index[n] for n in selected]
    R = reflectance[:, cols]

    if as_matrix:
        return wavelengths.copy(), R.copy(), selected

    return {n: R[:, j].copy() for j, n in enumerate(selected)}


def _load_npz() -> dict:
    npz_path = _ORACLE_DIR / _NPZ_NAME
    if npz_path.is_file():
        with np.load(npz_path, allow_pickle=False) as z:
            return {k: z[k] for k in z.files}

    # CSV fallback (wavelength_um, name1, name2, ...)
    csv_path = _ORACLE_DIR / _CSV_NAME
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"Missing splib07 fixture at {npz_path} and {csv_path}"
        )
    with csv_path.open() as f:
        header = f.readline().strip().split(",")
    names = header[1:]
    table = np.loadtxt(csv_path, delimiter=",", skiprows=1)
    wavelengths = table[:, 0]
    reflectance = table[:, 1:]
    return {
        "wavelengths_um": wavelengths,
        "reflectance": reflectance,
        "names": np.array(names),
    }


__all__ = [
    "DELETED_BAND_SENTINEL",
    "reference_oracle_dir",
    "fixture_dir",
    "list_endmember_names",
    "load_endmembers",
    "load_manifest",
    "wavelength_grid_um",
]
