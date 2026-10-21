"""Bare-earth DTM from a raw point cloud (registry 925). PROTOTYPE.

Fills the 1410 gap: fetch_lidar_dtm_3dep only kept points already classified as ground and had no noise
step, no hole filling and no output check. This module:

  1. removes outliers (statistical k-nearest-neighbour test, plus a robust low/high z cut),
  2. classifies ground with PDAL SMRF when the `pdal` Python bindings are importable (engine="pdal"),
     otherwise with a NumPy/SciPy progressive morphological filter (Zhang et al. 2003; the same idea as
     SMRF, Pingel et al. 2013) written here from the published description (no third-party code copied),
  3. grids ground points to a DTM with IDW or TIN (scipy Delaunay linear) and fills holes
     (nearest-neighbour by default),
  4. writes a GeoTIFF with rasterio and validates it: the file exists, has the expected shape and is not
     all nodata.

All heavy dependencies are optional. numpy and scipy are required for the fallback; rasterio only for
GeoTIFF output; laspy only for reading LAS/LAZ (read_las). Missing ones raise MissingDependency, which
callers and tests use to skip cleanly.

Nothing here is field-validated. The tests use a synthetic cloud with a known surface.
"""
import json
import os

import numpy as np


class MissingDependency(RuntimeError):
    pass


class EmptyRaster(RuntimeError):
    pass


def _scipy():
    try:
        from scipy import ndimage, spatial
        return ndimage, spatial
    except ImportError as e:  # pragma: no cover
        raise MissingDependency("scipy is required for lidar_dtm") from e


def have_pdal():
    try:
        import pdal  # noqa: F401
        return True
    except ImportError:
        return False


def read_las(path):
    """(N,3) xyz array from LAS/LAZ via laspy (optional dependency)."""
    try:
        import laspy
    except ImportError as e:
        raise MissingDependency("laspy not installed: pip install laspy") from e
    las = laspy.read(path)
    return np.column_stack([las.x, las.y, las.z]).astype(float)


# ---------------------------------------------------------------- 1. outliers
def remove_outliers(xyz, k=8, multiplier=2.5, z_mad=6.0):
    """Boolean keep-mask. Drops points whose mean distance to k neighbours is above
    mean + multiplier*std (statistical outlier removal), and points more than z_mad robust
    standard deviations from the median height of their neighbourhood (catches isolated low
    'multipath' points and birds)."""
    _, spatial = _scipy()
    xyz = np.asarray(xyz, float)
    n = len(xyz)
    if n <= k:
        return np.ones(n, bool)
    tree = spatial.cKDTree(xyz)
    d, idx = tree.query(xyz, k=k + 1)
    md = d[:, 1:].mean(axis=1)
    keep = md <= md.mean() + multiplier * md.std()
    tree2 = spatial.cKDTree(xyz[:, :2])
    _, idx2 = tree2.query(xyz[:, :2], k=min(4 * k + 1, n))
    zn = xyz[idx2, 2]
    med = np.median(zn, axis=1)
    mad = np.median(np.abs(zn - med[:, None]), axis=1) * 1.4826 + 1e-6
    keep &= np.abs(xyz[:, 2] - med) <= z_mad * np.maximum(mad, 0.5)
    return keep


# ------------------------------------------------------- 2. ground classification
def _grid_spec(xy, cell):
    x0, y0 = np.floor(xy.min(axis=0) / cell) * cell
    x1, y1 = np.ceil(xy.max(axis=0) / cell) * cell
    nx = max(1, int(round((x1 - x0) / cell)))
    ny = max(1, int(round((y1 - y0) / cell)))
    return x0, y0, nx, ny


def _min_surface(xyz, cell, spec):
    ndimage, _ = _scipy()
    x0, y0, nx, ny = spec
    ix = np.clip(((xyz[:, 0] - x0) / cell).astype(int), 0, nx - 1)
    iy = np.clip(((xyz[:, 1] - y0) / cell).astype(int), 0, ny - 1)
    zmin = np.full((ny, nx), np.inf)
    np.minimum.at(zmin, (iy, ix), xyz[:, 2])
    empty = ~np.isfinite(zmin)
    if empty.any():  # fill empty cells from nearest non-empty cell
        _, (ry, rx) = ndimage.distance_transform_edt(empty, return_indices=True)
        zmin = zmin[ry, rx]
    return zmin, ix, iy


def classify_ground_pmf(xyz, cell=1.0, max_window=20.0, slope=0.15, initial_threshold=0.3,
                        max_threshold=3.0, final_threshold=0.5):
    """Progressive morphological filter. Returns a boolean ground mask.

    Builds a minimum-elevation grid, opens it with square windows that grow (1, 3, 5, ... cells up to
    max_window metres) and, at each step, flags cells whose height drops by more than a slope-dependent
    threshold as non-ground. Points within final_threshold of the resulting surface are ground."""
    ndimage, _ = _scipy()
    xyz = np.asarray(xyz, float)
    spec = _grid_spec(xyz[:, :2], cell)
    surf, ix, iy = _min_surface(xyz, cell, spec)
    w, w_prev, prev = 1, 0, surf.copy()
    nonground = np.zeros_like(surf, bool)
    while w * cell <= max_window:
        opened = ndimage.grey_opening(prev, size=(w, w))
        # Zhang et al. 2003: dh_k = dh0 for the first window, then slope * (w_k - w_{k-1}) * cell + dh0
        thr = initial_threshold if w_prev == 0 else min(max_threshold, initial_threshold + slope * (w - w_prev) * cell)
        nonground |= (prev - opened) > thr
        prev, w_prev, w = opened, w, 2 * w + 1
    ground_surface = np.where(nonground, prev, surf)
    ground_surface = ndimage.grey_opening(ground_surface, size=(3, 3))
    return np.abs(xyz[:, 2] - ground_surface[iy, ix]) <= final_threshold


def classify_ground_pdal(xyz, slope=0.15, window=18.0, threshold=0.45, scalar=1.2, cell=1.0):
    """PDAL filters.smrf via the python-pdal bindings. Returns a ground mask."""
    try:
        import pdal
    except ImportError as e:
        raise MissingDependency("python-pdal not installed") from e
    arr = np.zeros(len(xyz), dtype=[("X", "f8"), ("Y", "f8"), ("Z", "f8"), ("Classification", "u1"),
                                    ("ReturnNumber", "u1"), ("NumberOfReturns", "u1")])
    arr["X"], arr["Y"], arr["Z"] = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    arr["ReturnNumber"] = arr["NumberOfReturns"] = 1
    spec = [{"type": "filters.smrf", "slope": slope, "window": window, "threshold": threshold,
             "scalar": scalar, "cell": cell}]
    p = pdal.Pipeline(json.dumps(spec), arrays=[arr])
    p.execute()
    return p.arrays[0]["Classification"] == 2


def classify_ground(xyz, engine="auto", **kw):
    """engine: 'auto' (PDAL if importable, else PMF), 'pdal' or 'pmf'. Returns (mask, engine_used)."""
    if engine == "pdal" or (engine == "auto" and have_pdal()):
        return classify_ground_pdal(xyz, **{k: v for k, v in kw.items() if k in ("slope", "cell")}), "pdal-smrf"
    return classify_ground_pmf(xyz, **kw), "numpy-pmf"


# ----------------------------------------------------------------- 3. gridding
def grid_dtm(ground_xyz, cell=1.0, method="idw", bounds=None, power=2.0, k=8, radius=None, fill="nearest"):
    """Grid ground points. method 'idw' or 'tin'. Returns (dtm 2-D array, transform tuple
    (x0, cell, y_top), filled-cell mask). Rows run north to south (GeoTIFF order)."""
    ndimage, spatial = _scipy()
    g = np.asarray(ground_xyz, float)
    if len(g) < 3:
        raise EmptyRaster("fewer than 3 ground points")
    if bounds is None:
        x0, y0, nx, ny = _grid_spec(g[:, :2], cell)
    else:
        x0, y0, x1, y1 = bounds
        nx, ny = int(round((x1 - x0) / cell)), int(round((y1 - y0) / cell))
    xs = x0 + (np.arange(nx) + 0.5) * cell
    ys = y0 + (np.arange(ny) + 0.5) * cell
    gx, gy = np.meshgrid(xs, ys[::-1])
    q = np.column_stack([gx.ravel(), gy.ravel()])
    radius = radius or 3.0 * cell
    if method == "tin":
        from scipy.interpolate import LinearNDInterpolator
        z = LinearNDInterpolator(g[:, :2], g[:, 2])(q)
        d, _ = spatial.cKDTree(g[:, :2]).query(q, k=1)
        z[d > radius * 2] = np.nan
    elif method == "idw":
        d, i = spatial.cKDTree(g[:, :2]).query(q, k=min(k, len(g)), distance_upper_bound=radius)
        d = np.atleast_2d(d.T).T if d.ndim == 1 else d
        i = np.atleast_2d(i.T).T if i.ndim == 1 else i
        ok = np.isfinite(d)
        wts = np.where(ok, 1.0 / np.maximum(d, 1e-6) ** power, 0.0)
        zz = np.where(ok, g[np.minimum(i, len(g) - 1), 2], 0.0)
        sw = wts.sum(axis=1)
        z = np.where(sw > 0, (wts * zz).sum(axis=1) / np.where(sw > 0, sw, 1), np.nan)
    else:
        raise ValueError("method must be 'idw' or 'tin'")
    dtm = z.reshape(ny, nx)
    holes = ~np.isfinite(dtm)
    if holes.all():
        raise EmptyRaster("no cell received a value")
    if holes.any() and fill == "nearest":
        _, (ry, rx) = ndimage.distance_transform_edt(holes, return_indices=True)
        dtm = dtm[ry, rx]
    return dtm, (x0, cell, y0 + ny * cell), holes


# ---------------------------------------------------------- 4. write + validate
def write_geotiff(dtm, transform, out_path, crs=None, nodata=-9999.0):
    try:
        import rasterio
        from rasterio.transform import from_origin
    except ImportError as e:
        raise MissingDependency("rasterio not installed") from e
    x0, cell, ytop = transform
    arr = np.where(np.isfinite(dtm), dtm, nodata).astype("float32")
    with rasterio.open(out_path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
                       dtype="float32", crs=crs, transform=from_origin(x0, ytop, cell, cell), nodata=nodata) as ds:
        ds.write(arr, 1)
    return out_path


def validate_raster(path, expect_shape=None, min_valid_frac=0.5):
    """Raise EmptyRaster unless the GeoTIFF exists, matches expect_shape and has enough valid cells.
    Returns a small stats dict."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        raise EmptyRaster(f"{path} was not produced")
    import rasterio
    with rasterio.open(path) as ds:
        a = ds.read(1, masked=True)
        shape = (ds.height, ds.width)
    if expect_shape and tuple(expect_shape) != shape:
        raise EmptyRaster(f"shape {shape} != expected {expect_shape}")
    valid = float((~np.ma.getmaskarray(a)).mean())
    if valid < min_valid_frac or a.count() == 0:
        raise EmptyRaster(f"only {valid:.0%} of cells are valid")
    return {"shape": shape, "valid_frac": valid, "min": float(a.min()), "max": float(a.max())}


def build_dtm(xyz, out_path=None, cell=1.0, method="idw", engine="auto", crs=None, bounds=None, **gkw):
    """Full pipeline. Returns dict with dtm, transform, masks and (if out_path) raster stats."""
    xyz = np.asarray(xyz, float)
    keep = remove_outliers(xyz)
    clean = xyz[keep]
    ground, used = classify_ground(clean, engine=engine, cell=cell, **gkw)
    dtm, tr, holes = grid_dtm(clean[ground], cell=cell, method=method, bounds=bounds)
    out = {"dtm": dtm, "transform": tr, "holes_filled": int(holes.sum()), "engine": used,
           "n_in": len(xyz), "n_outliers": int((~keep).sum()), "n_ground": int(ground.sum())}
    if out_path:
        write_geotiff(dtm, tr, out_path, crs=crs)
        out["raster"] = validate_raster(out_path, expect_shape=dtm.shape)
    return out


def synthetic_cloud(seed=0, size=60.0, density=6.0, n_trees=25, n_buildings=3, noise_frac=0.01):
    """Known terrain + vegetation + buildings + noise. Returns (xyz, truth_fn, labels) where labels is
    0 ground, 1 vegetation, 2 building, 7 noise (LAS-style codes)."""
    rng = np.random.default_rng(seed)

    def terrain(x, y):
        return 100 + 0.08 * x + 0.03 * y + 1.5 * np.sin(x / 9.0) * np.cos(y / 11.0)

    n = int(size * size * density)
    x, y = rng.uniform(0, size, n), rng.uniform(0, size, n)
    pts, lab = [np.column_stack([x, y, terrain(x, y) + rng.normal(0, 0.03, n)])], [np.zeros(n, int)]
    for _ in range(n_trees):  # crowns: points 2-15 m above ground within a radius
        cx, cy, r, h = rng.uniform(5, size - 5), rng.uniform(5, size - 5), rng.uniform(1.5, 3.5), rng.uniform(5, 15)
        m = int(np.pi * r * r * density * 2)
        a, rr = rng.uniform(0, 2 * np.pi, m), r * np.sqrt(rng.uniform(0, 1, m))
        tx, ty = cx + rr * np.cos(a), cy + rr * np.sin(a)
        pts.append(np.column_stack([tx, ty, terrain(tx, ty) + rng.uniform(2, h, m)])); lab.append(np.ones(m, int))
    for _ in range(n_buildings):  # flat roofs 4-8 m up, 6-12 m wide
        bx, by, w, d, h = rng.uniform(5, size - 15), rng.uniform(5, size - 15), rng.uniform(6, 12), rng.uniform(6, 12), rng.uniform(4, 8)
        m = int(w * d * density)
        tx, ty = bx + rng.uniform(0, w, m), by + rng.uniform(0, d, m)
        roof = terrain(bx + w / 2, by + d / 2) + h
        pts.append(np.column_stack([tx, ty, np.full(m, roof) + rng.normal(0, 0.03, m)])); lab.append(np.full(m, 2))
    k = int(n * noise_frac)
    nx_, ny_ = rng.uniform(0, size, k), rng.uniform(0, size, k)
    nz = terrain(nx_, ny_) + np.where(rng.uniform(size=k) < 0.5, -rng.uniform(5, 20, k), rng.uniform(30, 60, k))
    pts.append(np.column_stack([nx_, ny_, nz])); lab.append(np.full(k, 7))
    return np.vstack(pts), terrain, np.concatenate(lab)


def rmse_vs_truth(dtm, transform, truth_fn, margin_cells=2):
    x0, cell, ytop = transform
    ny, nx = dtm.shape
    xs = x0 + (np.arange(nx) + 0.5) * cell
    ys = ytop - (np.arange(ny) + 0.5) * cell
    gx, gy = np.meshgrid(xs, ys)
    err = (dtm - truth_fn(gx, gy))[margin_cells:ny - margin_cells, margin_cells:nx - margin_cells]
    return float(np.sqrt(np.nanmean(err ** 2))), float(np.nanmax(np.abs(err)))


if __name__ == "__main__":  # demo: python3 -m geo_connectors.lidar_dtm [out.tif]
    import sys, tempfile
    xyz, truth, _ = synthetic_cloud()
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "synthetic_dtm.tif")
    for method in ("idw", "tin"):
        r = build_dtm(xyz, out_path=out, method=method)
        print(method, r["engine"], "RMSE/max m:", rmse_vs_truth(r["dtm"], r["transform"], truth), r["raster"])
