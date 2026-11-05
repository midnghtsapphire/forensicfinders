"""Pure-Python little-endian GeoTIFF writer for SenseCrew synthetic DEMs (2320).

No GDAL/rasterio on the write path. Layout is fixed so fixture bytes are
platform- and version-independent (stdlib struct + numpy float32 LE only).
"""
from __future__ import annotations

import struct
from pathlib import Path
from typing import Union

import numpy as np

# TIFF types
_BYTE, _ASCII, _SHORT, _LONG, _RATIONAL = 1, 2, 3, 4, 5
_FLOAT, _DOUBLE = 11, 12

_SIZE = 257
_NODATA_ASCII = b"-9999\0"
_CITATION = b"SenseCrew synthetic local frame v0; not georeferenced\0"

# GeoKeys (KeyID, TIFFTagLocation, Count, Value_Offset)
# TIFFTagLocation 0 => Value_Offset is the short value itself.
# 34737 => offset into GeoAsciiParams.
_GEOKEYS = (
    (1024, 0, 1, 1),       # GTModelTypeGeoKey = ModelTypeProjected
    (1025, 0, 1, 1),       # GTRasterTypeGeoKey = RasterPixelIsArea
    (1026, 34737, 54, 0),  # GTCitationGeoKey -> ascii (len includes NUL)
    (3072, 0, 1, 32767),   # ProjectedCSTypeGeoKey = user-defined
    (3076, 0, 1, 9001),    # ProjLinearUnitsGeoKey = metre
)


def _tag(tag: int, typ: int, count: int, value: int) -> bytes:
    return struct.pack("<HHII", tag, typ, count, value)


def write_geotiff(arr: np.ndarray, path: Union[str, Path]) -> None:
    """Write a 257×257 float32 DEM as a classic little-endian GeoTIFF.

    Tags (ascending): 256,257,258,259,262,273,277,278,279,284,339,
    33550,33922,34735,34737,42113. No 270/305/306. Padding bytes zero.
    """
    a = np.asarray(arr, dtype=np.dtype("<f4"))
    if a.shape != (_SIZE, _SIZE):
        raise ValueError(f"expected ({_SIZE}, {_SIZE}) float32, got {a.shape} {a.dtype}")
    pixel = a.tobytes(order="C")
    assert len(pixel) == _SIZE * _SIZE * 4

    n_tags = 16
    ifd_offset = 8
    ifd_size = 2 + n_tags * 12 + 4  # 198
    extras_offset = ifd_offset + ifd_size  # 206

    # Extra data layout (all immediately after IFD, then pixels last):
    #   ModelPixelScale (3 doubles)  — 24 B
    #   ModelTiepoint  (6 doubles)   — 48 B
    #   GeoKeyDirectory (shorts)     — 4 + 4*n_keys = 4+20 = 24 B
    #   GeoAsciiParams               — len(_CITATION)
    #   GDAL_NODATA                  — len(_NODATA_ASCII)
    scale_off = extras_offset
    tie_off = scale_off + 24
    gk_off = tie_off + 48
    n_keys = len(_GEOKEYS)
    gk_bytes = (4 + 4 * n_keys) * 2  # header 4 shorts + 4 shorts/key
    ascii_off = gk_off + gk_bytes
    nodata_off = ascii_off + len(_CITATION)
    pixel_off = nodata_off + len(_NODATA_ASCII)
    # Align pixel data to 4 bytes (already aligned if lengths cooperate)
    if pixel_off % 4:
        pixel_off += 4 - (pixel_off % 4)

    scale = struct.pack("<3d", 1.0, 1.0, 0.0)
    tie = struct.pack("<6d", 0.0, 0.0, 0.0, 0.0, float(_SIZE), 0.0)
    gk = struct.pack("<4H", 1, 1, 0, n_keys)  # version, rev, minor, nkeys
    for kid, loc, cnt, val in _GEOKEYS:
        gk += struct.pack("<4H", kid, loc, cnt, val)
    assert len(gk) == gk_bytes
    assert len(_CITATION) == 54

    # IFD entries (value-or-offset in last field). SHORT/LONG count=1 inline.
    entries = [
        _tag(256, _SHORT, 1, _SIZE),             # ImageWidth
        _tag(257, _SHORT, 1, _SIZE),             # ImageLength
        _tag(258, _SHORT, 1, 32),                # BitsPerSample
        _tag(259, _SHORT, 1, 1),                 # Compression=None
        _tag(262, _SHORT, 1, 1),                 # Photometric=BlackIsZero
        _tag(273, _LONG, 1, pixel_off),          # StripOffsets
        _tag(277, _SHORT, 1, 1),                 # SamplesPerPixel
        _tag(278, _SHORT, 1, _SIZE),             # RowsPerStrip
        _tag(279, _LONG, 1, len(pixel)),         # StripByteCounts
        _tag(284, _SHORT, 1, 1),                 # PlanarConfiguration=chunky
        _tag(339, _SHORT, 1, 3),                 # SampleFormat=IEEE float
        _tag(33550, _DOUBLE, 3, scale_off),      # ModelPixelScale
        _tag(33922, _DOUBLE, 6, tie_off),        # ModelTiepoint
        _tag(34735, _SHORT, 4 + 4 * n_keys, gk_off),  # GeoKeyDirectory
        _tag(34737, _ASCII, len(_CITATION), ascii_off),
        _tag(42113, _ASCII, len(_NODATA_ASCII), nodata_off),
    ]
    assert len(entries) == n_tags
    # Ascending tag order is required.
    tag_ids = [struct.unpack_from("<H", e, 0)[0] for e in entries]
    assert tag_ids == sorted(tag_ids)

    buf = bytearray()
    buf += b"II*\x00"                             # classic little-endian TIFF
    buf += struct.pack("<I", ifd_offset)          # IFD at 8
    assert len(buf) == 8
    buf += struct.pack("<H", n_tags)
    for e in entries:
        buf += e
    buf += struct.pack("<I", 0)                   # no next IFD
    assert len(buf) == extras_offset

    buf += scale
    buf += tie
    buf += gk
    buf += _CITATION
    buf += _NODATA_ASCII
    if len(buf) < pixel_off:
        buf += b"\x00" * (pixel_off - len(buf))
    assert len(buf) == pixel_off
    buf += pixel

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(buf))
