"""Raspberry Pi field logger stub: GPS JSONL + synthetic/radar burst files.

Registry ID: 811. See docs/research/phone-gpr-addon.md (Pi section).
Does not talk to real hardware in tests; hardware hooks are optional callables.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional


@dataclass
class GpsFix:
    t_utc: str
    lat: float
    lon: float
    alt_m: float
    hdop: float
    fix_quality: int


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def capture_dir(root: Path, when: Optional[datetime] = None) -> Path:
    when = when or datetime.now(timezone.utc)
    name = "capture_" + when.strftime("%Y%m%d_%H%M%SZ")
    path = Path(root) / name
    (path / "radar").mkdir(parents=True, exist_ok=False)
    (path / "preview").mkdir(exist_ok=True)
    return path


def write_meta(path: Path, kit_model: str, host: str, authority: str = "") -> Path:
    meta = {
        "kit_model": kit_model,
        "host": host,
        "authority": authority,
        "started_utc": utc_now_iso(),
        "registry_id": "811",
    }
    out = path / "meta.json"
    out.write_text(json.dumps(meta, indent=2) + "\n")
    return out


def append_gps(path: Path, fixes: Iterable[GpsFix]) -> Path:
    out = path / "gps.jsonl"
    with out.open("a") as f:
        for fix in fixes:
            f.write(json.dumps(asdict(fix)) + "\n")
    return out


def write_synthetic_burst(path: Path, n_bins: int = 64, seed: int = 0) -> Path:
    """Write a deterministic range-profile .npy (or JSON fallback)."""
    try:
        import numpy as np

        rng = np.random.default_rng(seed)
        profile = rng.normal(0, 1, size=n_bins).astype("float32")
        profile[n_bins // 3] += 5.0
        out = path / "radar" / "burst_000.npy"
        np.save(out, profile)
        return out
    except ImportError:
        out = path / "radar" / "burst_000.json"
        out.write_text(json.dumps({"bins": [0.0] * n_bins}) + "\n")
        return out


def write_preview_summary(path: Path, peak_bin: int, peak_value: float) -> Path:
    out = path / "preview" / "last.json"
    out.write_text(
        json.dumps(
            {"t_utc": utc_now_iso(), "peak_bin": peak_bin, "peak_value": peak_value},
            indent=2,
        )
        + "\n"
    )
    return out


def run_synthetic_session(
    root: Path,
    kit_model: str = "SYNTHETIC",
    host: str = "pi5-stub",
    gps_reader: Optional[Callable[[], GpsFix]] = None,
) -> Path:
    """One offline session for tests / dry-run on the Pi before USB radar is attached."""
    path = capture_dir(root)
    write_meta(path, kit_model=kit_model, host=host)
    if gps_reader is None:
        fix = GpsFix(utc_now_iso(), 39.7392, -104.9903, 1600.0, 1.2, 3)
    else:
        fix = gps_reader()
    append_gps(path, [fix])
    burst = write_synthetic_burst(path)
    peak_bin, peak_value = 0, 0.0
    if burst.suffix == ".npy":
        import numpy as np

        arr = np.load(burst)
        peak_bin = int(arr.argmax())
        peak_value = float(arr[peak_bin])
    write_preview_summary(path, peak_bin, peak_value)
    return path
