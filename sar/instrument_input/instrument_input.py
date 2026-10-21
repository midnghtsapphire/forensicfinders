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
import random


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


def read_points(path):
    return read_las(path) if path.lower().endswith((".las", ".laz")) else read_points_csv(path)


def read_gpr_csv(path):
    with open(path, newline="") as f:
        traces = [[float(c) for c in row] for row in csv.reader(f) if row and not row[0].startswith("#")]
    if traces and len({len(t) for t in traces}) != 1:
        raise ValueError("all GPR traces must have the same number of samples")
    return traces


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
