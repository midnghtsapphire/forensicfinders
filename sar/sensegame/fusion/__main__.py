"""python -m sensegame.fusion --seed N --config fixtures/...synthetic.json --out DIR [--replay]"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from .run import run


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sensegame.fusion")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--replay", action="store_true", help="re-run and compare hashes against seeds.jsonl")
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
        if got != rec:
            print(f"REPLAY MISMATCH\nexpected {rec}\ngot      {got}", file=sys.stderr)
            return 1
        print(f"replay OK seed={a.seed}")
        return 0
    got = run(a.seed, a.config, a.out)
    line = json.dumps(got, sort_keys=True)
    existing = ledger.read_text().splitlines() if ledger.exists() else []
    if line not in existing:  # append-only
        with ledger.open("a") as f:
            f.write(line + "\n")
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
