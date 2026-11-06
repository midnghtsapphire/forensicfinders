"""Sourced constants loader. Each entry needs a non-empty source. user_required entries have no value
until the caller supplies one (with its own source) through overrides."""
import json
from pathlib import Path

PATH = Path(__file__).with_name("constants.json")


class MissingConstant(ValueError):
    pass


def load(path=PATH, overrides=None):
    data = json.loads(Path(path).read_text())["constants"]
    for k, v in data.items():
        if not str(v.get("source", "")).strip():
            raise ValueError(f"constant {k} has no source")
    for k, ov in (overrides or {}).items():
        if not str(ov.get("source", "")).strip():
            raise ValueError(f"override for {k} must include a source")
        data[k] = {**data.get(k, {}), **ov, "status": "user_supplied"}
    return data


def value(consts, key):
    c = consts[key]
    if c.get("value") is None:
        raise MissingConstant(f"{key}: no published value. Supply it with a source (overrides={{'{key}': {{'value': ..., 'source': '...'}}}}). Note: {c['source']}")
    return c["value"]
