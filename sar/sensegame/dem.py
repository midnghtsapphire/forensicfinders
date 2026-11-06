"""Synthetic DEM generator (registry 2320 / NEW-03) — integer diamond-square + PCG64.

Pure procedural terrain for SenseCrew missions M1–M3. No real DEM, no case data.
Spec: docs/sensecrew/bedrock/specs/dem-fixture-spec.md
"""
from __future__ import annotations

import argparse
import math
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from sensegame.tiffw import write_geotiff

GENERATOR_VERSION = "0"
SIZE = 257  # 2**8 + 1
CORNER_MM = 1_050_000
AMP0_MM = 20_000
H_ROUGHNESS = 1
CLIP_LO_MM = 1_000_000
CLIP_HI_MM = 1_100_000
RIDGE_AMP_MM = 5_000  # ±5 m for seed 1003
FEATURE_DEPTH_MM = 500  # ±0.5 m pits/mounds
RADIUS_MIN, RADIUS_MAX = 3, 6  # inclusive
N_PITS = N_MOUNDS = 3

FIXTURES: dict[str, str] = {
    "1001": "fixtures/dem_synthetic_1001.tif",
    "1002a": "fixtures/dem_synthetic_1002a.tif",
    "1002b": "fixtures/dem_synthetic_1002b.tif",
    "1003": "fixtures/dem_synthetic_1003.tif",
}

__all__ = [
    "FIXTURES",
    "GENERATOR_VERSION",
    "generate",
    "write_geotiff",
    "write_truth",
    "main",
]


def _disp(bg: np.random.PCG64, amp: int) -> int:
    """Signed displacement: u in [-2^52, 2^52), then (u * amp) >> 52."""
    u = int(bg.random_raw() >> 11) - (1 << 52)
    return (u * amp) >> 52


def _terrain_mm(seed: int) -> tuple[np.ndarray, np.random.PCG64]:
    """Diamond-square on int64 mm grid. Returns (grid, bg positioned after terrain draws)."""
    n = SIZE
    g = np.zeros((n, n), dtype=np.int64)
    g[0, 0] = g[0, -1] = g[-1, 0] = g[-1, -1] = CORNER_MM
    bg = np.random.PCG64(seed)

    step = n - 1  # 256
    k = 0
    while step > 1:
        half = step // 2
        amp = AMP0_MM >> int(round(k * H_ROUGHNESS))
        # Diamond pass, row-major over block origins.
        for y in range(0, n - 1, step):
            for x in range(0, n - 1, step):
                avg = (
                    int(g[y, x])
                    + int(g[y, x + step])
                    + int(g[y + step, x])
                    + int(g[y + step, x + step])
                ) // 4
                g[y + half, x + half] = avg + _disp(bg, amp)
        # Square pass, row-major (classic half/step traversal).
        for y in range(0, n, half):
            for x in range((y + half) % step, n, step):
                vals: list[int] = []
                if y - half >= 0:
                    vals.append(int(g[y - half, x]))
                if y + half < n:
                    vals.append(int(g[y + half, x]))
                if x - half >= 0:
                    vals.append(int(g[y, x - half]))
                if x + half < n:
                    vals.append(int(g[y, x + half]))
                avg = sum(vals) // len(vals)
                g[y, x] = avg + _disp(bg, amp)
        step //= 2
        k += 1
    return g, bg


def _draw_u(bg: np.random.PCG64, modulus: int) -> int:
    """Uniform integer in [0, modulus) from the raw PCG64 stream."""
    if modulus <= 0:
        raise ValueError("modulus must be positive")
    return int(bg.random_raw() % modulus)


def _disks_overlap(a: dict[str, int], b: dict[str, int]) -> bool:
    dy = a["row"] - b["row"]
    dx = a["col"] - b["col"]
    r = a["radius_px"] + b["radius_px"]
    return dy * dy + dx * dx <= r * r


def _draw_features(bg: np.random.PCG64) -> dict[str, Any]:
    """3 pits then 3 mounds; rejection sample until disks do not overlap."""
    margin = RADIUS_MAX
    span = SIZE - 2 * margin
    placed: list[dict[str, int]] = []
    pits: list[dict[str, int]] = []
    mounds: list[dict[str, int]] = []

    def one(depth_mm: int) -> dict[str, int]:
        for _ in range(10_000):
            radius = RADIUS_MIN + _draw_u(bg, RADIUS_MAX - RADIUS_MIN + 1)
            row = margin + _draw_u(bg, span)
            col = margin + _draw_u(bg, span)
            feat = {
                "col": col,
                "depth_mm": depth_mm,
                "radius_px": radius,
                "row": row,
            }
            if any(_disks_overlap(feat, p) for p in placed):
                continue
            placed.append(feat)
            return feat
        raise RuntimeError("could not place non-overlapping DEM feature")

    for _ in range(N_PITS):
        pits.append(one(-FEATURE_DEPTH_MM))
    for _ in range(N_MOUNDS):
        mounds.append(one(FEATURE_DEPTH_MM))

    return {
        "generator_version": GENERATOR_VERSION,
        "mounds": mounds,
        "pits": pits,
    }


def _apply_cone(grid: np.ndarray, feat: dict[str, int]) -> None:
    """Integer cone: peak depth_mm at centre, 0 at radius edge (disk <= r^2)."""
    r = feat["radius_px"]
    depth = feat["depth_mm"]
    cy, cx = feat["row"], feat["col"]
    y0, y1 = max(0, cy - r), min(SIZE, cy + r + 1)
    x0, x1 = max(0, cx - r), min(SIZE, cx + r + 1)
    for y in range(y0, y1):
        for x in range(x0, x1):
            dist_sq = (y - cy) * (y - cy) + (x - cx) * (x - cx)
            if dist_sq > r * r:
                continue
            dist = math.isqrt(dist_sq)
            if dist > r:
                continue
            grid[y, x] += depth * (r - dist) // r


def _apply_ridge(grid: np.ndarray) -> None:
    """Gentle east-west linear ramp ±5 m (deterministic; no extra RNG)."""
    for c in range(SIZE):
        delta = -RIDGE_AMP_MM + (2 * RIDGE_AMP_MM * c) // (SIZE - 1)
        grid[:, c] += delta


def generate(seed: int, epoch: str | None = None) -> np.ndarray:
    """Return a 257×257 float32 DEM (metres, integer-mm quantised).

    epoch must be \"a\"/\"b\" for seed 1002 and None otherwise.
    """
    if seed == 1002:
        if epoch not in ("a", "b"):
            raise ValueError("seed 1002 requires epoch 'a' or 'b'")
    else:
        if epoch is not None:
            raise ValueError(f"seed {seed} does not take an epoch")

    grid, bg = _terrain_mm(seed)

    if seed == 1003:
        _apply_ridge(grid)
    elif seed == 1002 and epoch == "b":
        truth = _draw_features(bg)
        for f in truth["pits"] + truth["mounds"]:
            _apply_cone(grid, f)
    # seed 1002 epoch a: terrain only (feature draws never consumed)
    # seed 1001: terrain only

    np.clip(grid, CLIP_LO_MM, CLIP_HI_MM, out=grid)
    return (grid.astype(np.float64) / 1000.0).astype(np.float32)


def write_truth(path: str | Path, seed: int = 1002) -> dict[str, Any]:
    """Generate and write dem_synthetic_1002_truth.json (sorted keys)."""
    if seed != 1002:
        raise ValueError("truth JSON is only defined for seed 1002")
    _, bg = _terrain_mm(seed)
    truth = _draw_features(bg)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(truth, sort_keys=True, separators=(",", ":")) + "\n")
    return truth


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cli_verify(sums_path: Path) -> int:
    """Regenerate fixtures named in SHA256SUMS into a temp dir and check digests."""
    import tempfile

    lines = [
        ln.strip()
        for ln in sums_path.read_text().splitlines()
        if ln.strip() and not ln.startswith("#")
    ]
    ok = True
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        for ln in lines:
            digest, name = ln.split()
            name = name.lstrip("*")
            # dem_synthetic_1001.tif / 1002a / 1002b / 1003
            stem = Path(name).stem  # dem_synthetic_1001
            key = stem.replace("dem_synthetic_", "")
            if key == "1001":
                seed, epoch = 1001, None
            elif key == "1002a":
                seed, epoch = 1002, "a"
            elif key == "1002b":
                seed, epoch = 1002, "b"
            elif key == "1003":
                seed, epoch = 1003, None
            else:
                print(f"UNKNOWN {name}", file=sys.stderr)
                ok = False
                continue
            out = td_path / Path(name).name
            write_geotiff(generate(seed, epoch), out)
            got = _sha256(out)
            if got == digest:
                print(f"OK {name}")
            else:
                print(f"FAIL {name}: expected {digest}, got {got}", file=sys.stderr)
                ok = False
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sensegame.dem", description="Synthetic DEM fixtures (2320)")
    p.add_argument("--seed", type=int, help="terrain seed (1001/1002/1003)")
    p.add_argument("--epoch", default=None, help="a|b for seed 1002")
    p.add_argument("--out", type=Path, help="output GeoTIFF path")
    p.add_argument("--verify", type=Path, help="SHA256SUMS path to verify against")
    p.add_argument("--write-truth", type=Path, help="write 1002 truth JSON to this path")
    args = p.parse_args(argv)

    if args.verify is not None:
        return _cli_verify(args.verify)
    if args.write_truth is not None:
        write_truth(args.write_truth)
        return 0
    if args.seed is None or args.out is None:
        p.error("--seed and --out are required unless --verify / --write-truth")
    epoch = args.epoch
    write_geotiff(generate(args.seed, epoch), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
