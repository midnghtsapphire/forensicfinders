"""Procedural synthetic scene generator (Rule 3/7: seeded, no real data). Writes fixtures/*synthetic*.json."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROWS = COLS = 20
LAYERS = (("thermal", 1.0), ("ndvi_change", 1.0), ("sar_coherence", -1.0))


def scene(seed: int) -> dict:
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed)))
    labels = (rng.random((ROWS, COLS)) < 0.08).astype(int)
    rr, cc = np.mgrid[0:ROWS, 0:COLS]
    out = {"seed": seed, "grid": {"rows": ROWS, "cols": COLS, "cell_m": 30.0}, "layers": {}, "labels": labels.tolist()}
    for k, (name, sign) in enumerate(LAYERS):
        trend = 0.3 * np.sin((rr + k) / 5.0) + 0.3 * np.cos((cc - k) / 7.0)
        hit = labels * (rng.random((ROWS, COLS)) < 0.85)
        v = trend + rng.standard_normal((ROWS, COLS)) + sign * 3.0 * hit
        v = np.round(v, 6).tolist()
        if name == "ndvi_change":
            miss = rng.random((ROWS, COLS)) < 0.03
            v = [[None if miss[i][j] else v[i][j] for j in range(COLS)] for i in range(ROWS)]
        out["layers"][name] = v
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", required=True)
    ap.add_argument("--prefix", default="fusion_sensors_synthetic")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    for s in a.seeds:
        (a.out / f"{a.prefix}_{s}.json").write_text(json.dumps(scene(s), sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
