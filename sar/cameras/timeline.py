"""Frame-to-timeline merger: turns camera frame/event metadata (public_cams, ring_cam) and satellite scene
lists (geo_connectors.run_sectors output) into one sorted SAR timeline (JSON Lines).

Event schema: {t_utc, kind, source_id, label, lat?, lon?, media_path?, sha256?, ref}
  python3 -m cameras.timeline merge out/frames/*.json out/ring/*.json --sectors out/SYNTH-0001_sectors.json --out out/timeline.jsonl
"""
import argparse, datetime, glob, json, re, sys


def _t(v):
    if v is None:
        return None
    s = str(v).replace("Z", "+00:00")
    t = datetime.datetime.fromisoformat(s)
    if t.tzinfo is None:
        t = t.replace(tzinfo=datetime.timezone.utc)
    return t.astimezone(datetime.timezone.utc)


def from_camera_meta(m):
    return {"t_utc": m.get("t_utc"), "kind": m["kind"], "source_id": m.get("camera_id"),
            "label": m.get("camera_name") or m.get("camera_id"), "lat": m.get("lat"), "lon": m.get("lon"),
            "media_path": m.get("media_path"), "sha256": m.get("sha256"),
            "ref": m.get("event_id") or m.get("image_url")}


_S2 = re.compile(r"_(\d{8})_")
_S1 = re.compile(r"_(\d{8}T\d{6})_")


def scene_time(scene_id):
    m = _S1.search(scene_id)
    if m:
        return datetime.datetime.strptime(m.group(1), "%Y%m%dT%H%M%S").replace(tzinfo=datetime.timezone.utc).isoformat()
    m = _S2.search(scene_id)
    if m:
        return datetime.datetime.strptime(m.group(1), "%Y%m%d").replace(tzinfo=datetime.timezone.utc).isoformat()
    return None


def from_sectors(doc):
    out = []
    for s in doc.get("sectors", []):
        for which in ("scenes_before", "scenes_after"):
            for sid in s.get(which, []):
                out.append({"t_utc": scene_time(sid), "kind": "satellite_scene", "source_id": sid,
                            "label": f"{s['sector']} {which.split('_')[1]}", "lat": None, "lon": None,
                            "media_path": None, "sha256": None, "ref": sid})
    return out


def merge(*event_lists, dedupe=True):
    seen, out, undated = set(), [], []
    for ev in (e for lst in event_lists for e in lst):
        key = (ev["kind"], ev["source_id"], ev.get("t_utc"), ev.get("sha256"))
        if dedupe and key in seen:
            continue
        seen.add(key)
        (out if ev.get("t_utc") else undated).append(ev)
    out.sort(key=lambda e: (_t(e["t_utc"]), e["kind"], str(e["source_id"])))
    for e in out:
        e["t_utc"] = _t(e["t_utc"]).isoformat().replace("+00:00", "Z")
    return out + undated


def window(events, start, end):
    s, e = _t(start), _t(end)
    return [x for x in events if x.get("t_utc") and s <= _t(x["t_utc"]) <= e]


def main(argv=None):
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("merge"); p.add_argument("meta", nargs="*"); p.add_argument("--sectors", action="append", default=[])
    p.add_argument("--out", default="out/timeline.jsonl")
    a = ap.parse_args(argv)
    cams = [from_camera_meta(json.load(open(f))) for pat in a.meta for f in (glob.glob(pat) or [pat])]
    sats = [e for f in a.sectors for e in from_sectors(json.load(open(f)))]
    tl = merge(cams, sats)
    import os
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as f:
        for e in tl:
            f.write(json.dumps(e) + "\n")
    print(f"{a.out}: {len(tl)} events")
    return 0


if __name__ == "__main__":
    sys.exit(main())
