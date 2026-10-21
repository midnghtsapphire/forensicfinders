"""Public webcam / traffic-cam connector: list cameras from a data-driven source registry
(sources.json) and capture timestamped snapshot frames with metadata + SHA-256.

  python3 -m cameras.public_cams list caltrans-d03 [--near LAT LON KM]
  python3 -m cameras.public_cams snap caltrans-d03 CAMERA_ID [CAMERA_ID ...] --out-dir out/frames [--repeat N --interval S]
"""
import argparse, datetime, hashlib, json, math, os, sys, time
from pathlib import Path
from urllib.parse import urlparse
from geo_connectors import netio

SOURCES = json.loads(Path(__file__).with_name("sources.json").read_text())["sources"]


def _allow(url):
    netio.allow_host(urlparse(url).hostname)


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_caltrans(doc):
    out = []
    for row in doc.get("data", []):
        c = row.get("cctv", row)
        loc, img = c.get("location", {}), c.get("imageData", {})
        st = img.get("static", {})
        out.append({"id": f"caltrans-{loc.get('district')}-{c.get('index')}", "name": loc.get("locationName"),
                    "route": loc.get("route"), "direction": loc.get("direction"), "county": loc.get("county"),
                    "lat": _f(loc.get("latitude")), "lon": _f(loc.get("longitude")),
                    "in_service": str(c.get("inService")).lower() == "true",
                    "image_url": st.get("currentImageURL") or None, "stream_url": img.get("streamingVideoURL") or None,
                    "update_minutes": _f(st.get("currentImageUpdateFrequency"))})
    return out


def list_cameras(source_id, sources=SOURCES, **kw):
    s = sources[source_id]
    if s["type"] == "static_list":
        return [dict(c, source=source_id) for c in s["cameras"]]
    if s["type"] == "caltrans_cctv":
        _allow(s["url"])
        cams = parse_caltrans(netio.request_json(s["url"], **kw))
        return [dict(c, source=source_id) for c in cams]
    raise ValueError(f"unsupported source type {s['type']!r}")


def near(cams, lat, lon, km):
    def d(c):
        p1, p2 = math.radians(lat), math.radians(c["lat"])
        a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(c["lon"] - lon) / 2) ** 2
        return 2 * 6371 * math.asin(math.sqrt(a))
    out = [dict(c, distance_km=round(d(c), 3)) for c in cams if c.get("lat") is not None and c.get("lon") is not None]
    return sorted([c for c in out if c["distance_km"] <= km], key=lambda c: c["distance_km"])


def snapshot(cam, out_dir, clock=None, **kw):
    if not cam.get("image_url"):
        raise netio.ConnectorError(f"{cam['id']}: no still-image URL (stream only)")
    _allow(cam["image_url"])
    t = (clock or (lambda: datetime.datetime.now(datetime.timezone.utc)))()
    data = netio.request(cam["image_url"], **kw)
    sha = hashlib.sha256(data).hexdigest()
    stamp = t.strftime("%Y%m%dT%H%M%SZ")
    os.makedirs(out_dir, exist_ok=True)
    img = os.path.join(out_dir, f"{cam['id']}_{stamp}.jpg")
    open(img, "wb").write(data)
    meta = {"kind": "public_cam_frame", "t_utc": t.isoformat().replace("+00:00", "Z"), "camera_id": cam["id"],
            "camera_name": cam.get("name"), "source": cam.get("source"), "lat": cam.get("lat"), "lon": cam.get("lon"),
            "image_url": cam["image_url"], "media_path": img, "sha256": sha, "bytes": len(data),
            "time_basis": "capture time (UTC) of fetch; publisher refresh interval min: %s" % cam.get("update_minutes")}
    json.dump(meta, open(img[:-4] + ".json", "w"), indent=2)
    return meta


def main(argv=None):
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("list"); p.add_argument("source"); p.add_argument("--near", nargs=3, type=float, metavar=("LAT", "LON", "KM"))
    p = sp.add_parser("snap"); p.add_argument("source"); p.add_argument("ids", nargs="+"); p.add_argument("--out-dir", default="out/frames")
    p.add_argument("--repeat", type=int, default=1); p.add_argument("--interval", type=float, default=60)
    sp.add_parser("sources")
    a = ap.parse_args(argv)
    if a.cmd == "sources":
        print(json.dumps({k: v.get("publisher") for k, v in SOURCES.items()}, indent=2)); return 0
    cams = list_cameras(a.source)
    if a.cmd == "list":
        if a.near:
            cams = near(cams, *a.near)
        print(json.dumps(cams, indent=2)); return 0
    by = {c["id"]: c for c in cams}
    for i in range(a.repeat):
        for cid in a.ids:
            print(json.dumps(snapshot(by[cid], a.out_dir)))
        if i < a.repeat - 1:
            time.sleep(a.interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
