"""python -m sensegame.fusion --seed N --config fixtures/...synthetic.json --out DIR [--replay]"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from .run import run


# Fields written only on the ledger record. run() never produces them.
_RECORD_ONLY = frozenset({"drift_from"})
_REPLAY_KEY_CAP = 10


def _canon(rec: dict) -> str:
    return json.dumps(rec, sort_keys=True)


def _outputs(rec: dict) -> dict:
    """Output fields only. Strips ledger metadata such as drift_from."""
    return {k: v for k, v in rec.items() if k not in _RECORD_ONLY}


def _record_hash(rec: dict) -> str:
    return hashlib.sha256(_canon(rec).encode()).hexdigest()


def _output_digest(rec: dict) -> str:
    return hashlib.sha256(_canon(_outputs(rec)).encode()).hexdigest()


def _replay_mismatch(expected: dict, got: dict) -> str:
    """Short mismatch line: key names and digests, never field values."""
    exp, act = _outputs(expected), _outputs(got)
    differ = sorted(k for k in set(exp) | set(act) if exp.get(k) != act.get(k))
    shown = differ[:_REPLAY_KEY_CAP]
    names = ",".join(shown)
    if len(differ) > _REPLAY_KEY_CAP:
        names = f"{names} (+{len(differ) - _REPLAY_KEY_CAP} more)"
    return (
        f"REPLAY_MISMATCH keys={names} "
        f"expected_sha256={_output_digest(expected)} got_sha256={_output_digest(got)}"
    )


def record_run(ledger: Path, got: dict, accept_drift: bool = False) -> int:
    """Append-only seeds.jsonl update.

    A repeat of the same output hashes for this seed writes nothing.
    A different hash for the same seed is drift: exit 1 and append nothing,
    unless accept_drift is set, in which case a new line is appended with
    drift_from set to the sha256 of the previous record.
    """
    existing = ledger.read_text().splitlines() if ledger.exists() else []
    records = [json.loads(line) for line in existing if line.strip()]
    same = [r for r in records if r.get("seed") == got.get("seed")]
    fresh = _outputs(got)
    if any(_outputs(r) == fresh for r in same):
        return 0
    if same:
        old_hash = _record_hash(same[-1])
        if not accept_drift:
            print(
                f"DRIFT seed={got.get('seed')}: output differs from seeds.jsonl "
                f"record {old_hash}; refusing to append",
                file=sys.stderr,
            )
            return 1
        recorded = dict(got)
        recorded["drift_from"] = old_hash
        line = _canon(recorded)
    else:
        line = _canon(got)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a") as fh:
        fh.write(line + "\n")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sensegame.fusion")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--replay", action="store_true", help="re-run and compare hashes against seeds.jsonl")
    ap.add_argument(
        "--accept-drift",
        action="store_true",
        help="when this seed's hashes differ, append a record with drift_from set to the previous hash",
    )
    a = ap.parse_args(argv)
    ledger = a.out.parent / "seeds.jsonl"
    if a.replay:
        rec = None
        if ledger.exists():
            for line in ledger.read_text().splitlines():
                r = json.loads(line)
                if r["seed"] == a.seed:
                    rec = r
        if rec is None:
            print(f"no seeds.jsonl entry for seed {a.seed}; run `make fusion` first", file=sys.stderr)
            return 2
        with tempfile.TemporaryDirectory() as td:
            got = run(a.seed, a.config, td)
        if _outputs(got) != _outputs(rec):
            print(_replay_mismatch(rec, got), file=sys.stderr)
            return 1
        print(f"replay OK seed={a.seed}")
        return 0
    got = run(a.seed, a.config, a.out)
    rc = record_run(ledger, got, a.accept_drift)
    if rc == 0:
        print(_canon(got))
    return rc


if __name__ == "__main__":
    sys.exit(main())
