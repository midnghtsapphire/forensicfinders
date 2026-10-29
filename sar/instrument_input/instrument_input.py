"""
Instrument file input. This replaces layer-peel's animated SensorMock as the data source.

Reads real instrument exports instead of drawing fake scan lines:
  * LiDAR point clouds: .las/.laz through laspy (optional dependency), or
    x,y,z[,intensity] CSV in local metres.
  * GPR B-scans: CSV of traces, one row per trace and one column per time sample.
synthetic_lidar() and synthetic_gpr() generate deterministic samples in a LOCAL
metre frame (origin 0,0). They carry no geographic coordinates and no pins.
"""
import csv
import math
import os as _os
import random
import sys as _sys

# ----------------------------------------------------------------------------------------
# Decode seam import (sar/decode_hooks.py). This directory is not a package -- its tests run
# with the cwd set here (registry.json component 810) -- so the parent sar/ is put on
# sys.path explicitly and the module imported by plain name. Importing the same file under
# a different name would create a SECOND hook registry, and a hook registered once would
# then apply to the rasters but not to the instrument files. geo_connectors/stac.py does the
# identical thing for the same reason; keep the two in step.
# ----------------------------------------------------------------------------------------
_SAR_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _SAR_ROOT not in _sys.path:
    _sys.path.insert(0, _SAR_ROOT)
import decode_hooks


def read_points_csv(path):
    pts = []
    with open(path, newline="") as f:
        for row in csv.reader(f):
            if not row or row[0].strip().lower() in ("x", "#"):
                continue
            v = [float(c) for c in row[:4]]
            if len(v) < 3:
                raise ValueError(f"need x,y,z per row, got {row}")
            pts.append(tuple(v) if len(v) == 4 else (*v, 0.0))
    return pts


def read_las(path):
    try:
        import laspy
    except ImportError as e:
        raise RuntimeError("laspy not installed: pip install laspy (add lazrs for .laz)") from e
    las = laspy.read(path)
    return list(zip(las.x, las.y, las.z, getattr(las, "intensity", [0] * len(las.x))))


# REVVEL-DISABLED | AGENT: claude-code | MODEL: claude-opus-5 | WR: UNASSIGNED | DATE: 2026-10-24 | STATUS: REPLACED
# REASON: signature superseded below -- gained the optional `meta` out-parameter for the
#         decode receipt. Additive; read_points(path) still behaves exactly as before.
# PREVIOUS SIGNATURE, kept verbatim (this function had no docstring):
# def read_points(path):
# OWNER: @midnghtsapphire
# REVVEL-DISABLED-END
def read_points(path, meta=None):
    """Read a LiDAR point cloud (.las/.laz via laspy, else x,y,z[,intensity] CSV).

    This is the documented entry point for point data, so it is where conditioning is
    applied. read_points_csv() and read_las() below are deliberately NOT seamed: this
    function delegates to them, and seaming both levels would run every hook twice over
    the same points.

    Pass a dict as `meta` for a receipt naming the hooks that ran. With no hooks
    registered the seam is the identity function and the return value is unchanged.
    """
    # REVVEL-DISABLED | AGENT: claude-code | MODEL: claude-opus-5 | WR: UNASSIGNED | DATE: 2026-10-24 | STATUS: REPLACED
    # REASON: superseded by the lines below, which route decoded points through the decode
    #         seam (sar/decode_hooks.py) instead of returning the reader's output directly.
    # PREVIOUS BEHAVIOUR: returned the list of (x, y, z, intensity) tuples straight from
    #         read_las()/read_points_csv(), unconditioned, with no record of what had been
    #         applied. Identical values are still returned while no hook is registered.
    # WHY CHANGED: Audrey's design decision (2026-10-22/23) to inject at the decoding layer
    #         rather than higher up the stack, so corrections land once, at ingress.
    # OWNER: @midnghtsapphire
    # return read_las(path) if path.lower().endswith((".las", ".laz")) else read_points_csv(path)
    # REVVEL-DISABLED-END
    is_las = path.lower().endswith((".las", ".laz"))
    points = read_las(path) if is_las else read_points_csv(path)
    if meta is None:
        meta = {}
    meta.update({"decoder": "read_points", "path": path, "format": "las" if is_las else "csv",
                 "count": len(points)})
    return decode_hooks.apply(points, meta)


# REVVEL-DISABLED | AGENT: claude-code | MODEL: claude-opus-5 | WR: UNASSIGNED | DATE: 2026-10-24 | STATUS: REPLACED
# REASON: signature superseded below -- gained the optional `meta` out-parameter for the
#         decode receipt. Additive; read_gpr_csv(path) still behaves exactly as before.
# PREVIOUS SIGNATURE, kept verbatim (this function had no docstring):
# def read_gpr_csv(path):
# OWNER: @midnghtsapphire
# REVVEL-DISABLED-END
def read_gpr_csv(path, meta=None):
    """Read a GPR B-scan CSV: one row per trace, one column per time sample.

    Conditioned through the decode seam for the same reason as read_points() -- GPR
    corrections (time-zero, gain, dewow) belong to the instrument, not to whichever
    analysis happens to open the file. Pass a dict as `meta` for a receipt.
    """
    with open(path, newline="") as f:
        traces = [[float(c) for c in row] for row in csv.reader(f) if row and not row[0].startswith("#")]
    if traces and len({len(t) for t in traces}) != 1:
        raise ValueError("all GPR traces must have the same number of samples")
    # REVVEL-DISABLED | AGENT: claude-code | MODEL: claude-opus-5 | WR: UNASSIGNED | DATE: 2026-10-24 | STATUS: REPLACED
    # REASON: superseded by the lines below, which route the decoded traces through the seam.
    # PREVIOUS BEHAVIOUR: returned the parsed trace lists directly. The ragged-row check above
    #         is unchanged and still runs BEFORE any hook, so a malformed file is still
    #         rejected on its own terms rather than inside somebody's correction.
    # OWNER: @midnghtsapphire
    # return traces
    # REVVEL-DISABLED-END
    if meta is None:
        meta = {}
    meta.update({"decoder": "read_gpr_csv", "path": path, "traces": len(traces),
                 "samples": len(traces[0]) if traces else 0})
    return decode_hooks.apply(traces, meta)


def grid_min_z(points, cell_m=1.0):
    """Bare-earth style raster: min z per cell -> {(i, j): z}."""
    g = {}
    for x, y, z, *_ in points:
        k = (math.floor(x / cell_m), math.floor(y / cell_m))
        g[k] = min(z, g.get(k, z))
    return g


def synthetic_lidar(n=500, seed=0, size_m=20.0, pit=(10.0, 10.0, 1.5, 0.4)):
    """Flat ground with gentle slope plus one shallow depression (cx, cy, radius, depth). Local metres only."""
    r = random.Random(seed)
    cx, cy, rad, depth = pit
    out = []
    for _ in range(n):
        x, y = r.uniform(0, size_m), r.uniform(0, size_m)
        z = 0.02 * x + r.gauss(0, 0.01)
        d = math.hypot(x - cx, y - cy)
        if d < rad:
            z -= depth * (1 - d / rad)
        out.append((x, y, z, r.randint(0, 255)))
    return out


def synthetic_gpr(traces=40, samples=64, seed=0, target_trace=20, target_sample=30):
    """Hyperbola from one point reflector, plus noise."""
    r = random.Random(seed)
    out = []
    for t in range(traces):
        tt = round(math.hypot(t - target_trace, target_sample))
        out.append([(1.0 if s == tt else 0.0) + r.gauss(0, 0.02) for s in range(samples)])
    return out
