"""Ring connector for Audrey's own account, via the open-source `ring_doorbell` library (pip install ring_doorbell).

Optional secrets (env vars, never hard-coded, never printed):
  RING_USERNAME, RING_PASSWORD   first login only
  RING_OTP                       2FA code when Ring asks for it (first login only)
  RING_TOKEN_CACHE               token file path (default ~/.config/forensicfinders/ring_token.json, mode 600)
After the first login only the refreshed token cache is used.

  python3 -m cameras.ring_cam devices
  python3 -m cameras.ring_cam history "Front Door" --limit 20
  python3 -m cameras.ring_cam download "Front Door" EVENT_ID --out-dir out/ring
  python3 -m cameras.ring_cam snapshot "Front Door" --out-dir out/ring
"""
import argparse, asyncio, datetime, hashlib, json, os, sys
from pathlib import Path

USER_AGENT = "forensicfinders-sar/1.0"
DEFAULT_CACHE = Path.home() / ".config" / "forensicfinders" / "ring_token.json"


def cache_path():
    return Path(os.environ.get("RING_TOKEN_CACHE") or DEFAULT_CACHE)


def _save_token(token, path=None):
    p = Path(path or cache_path())
    p.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(token, f)


async def connect(lib=None, env=os.environ):
    """Return an updated ring_doorbell.Ring. Uses the token cache, or env credentials on first run."""
    if lib is None:
        import ring_doorbell as lib
    p = cache_path()
    if p.exists():
        auth = lib.Auth(USER_AGENT, json.loads(p.read_text()), _save_token)
    else:
        user, pw = env.get("RING_USERNAME"), env.get("RING_PASSWORD")
        if not (user and pw):
            raise RuntimeError("No Ring token cache and RING_USERNAME/RING_PASSWORD are not set")
        auth = lib.Auth(USER_AGENT, None, _save_token)
        try:
            await auth.async_fetch_token(user, pw)
        except lib.Requires2FAError:
            otp = env.get("RING_OTP")
            if not otp:
                raise RuntimeError("Ring sent a 2FA code: re-run with RING_OTP=<code>")
            await auth.async_fetch_token(user, pw, otp)
    ring = lib.Ring(auth)
    await ring.async_update_data()
    return ring


def _devices(ring):
    return list(ring.video_devices())


def device_info(d):
    return {"id": d.id, "name": d.name, "family": getattr(d, "family", None), "kind": getattr(d, "kind", None)}


def _find(ring, name_or_id):
    for d in _devices(ring):
        if d.name == name_or_id or str(d.id) == str(name_or_id):
            return d
    raise KeyError(f"no Ring video device {name_or_id!r}; have {[d.name for d in _devices(ring)]}")


def _iso(v):
    if isinstance(v, datetime.datetime):
        if v.tzinfo is None:
            v = v.replace(tzinfo=datetime.timezone.utc)
        return v.astimezone(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    return v


async def list_devices(ring):
    return [device_info(d) for d in _devices(ring)]


async def history(ring, device, limit=30, kind=None):
    d = _find(ring, device)
    ev = await d.async_history(limit=limit, kind=kind)
    return [{"kind": "ring_event", "t_utc": _iso(e.get("created_at")), "event_id": e.get("id"), "event_kind": e.get("kind"),
             "answered": e.get("answered"), "duration_s": e.get("duration"), "camera_id": f"ring-{d.id}", "camera_name": d.name}
            for e in ev]


async def download(ring, device, event_id, out_dir, event_time=None):
    d = _find(ring, device)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"ring-{d.id}_{event_id}.mp4")
    data = await d.async_recording_download(int(event_id), filename=path, override=True)
    blob = data if isinstance(data, (bytes, bytearray)) else Path(path).read_bytes()
    if data is not None and not Path(path).exists():
        Path(path).write_bytes(blob)
    meta = {"kind": "ring_recording", "t_utc": _iso(event_time), "event_id": event_id, "camera_id": f"ring-{d.id}",
            "camera_name": d.name, "media_path": path, "sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob)}
    json.dump(meta, open(path[:-4] + ".json", "w"), indent=2)
    return meta


async def snapshot(ring, device, out_dir, clock=None):
    d = _find(ring, device)
    t = (clock or (lambda: datetime.datetime.now(datetime.timezone.utc)))()
    data = await d.async_get_snapshot()
    if not data:
        raise RuntimeError(f"{d.name}: Ring returned no snapshot (battery devices may not support on-demand snapshots)")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"ring-{d.id}_{t.strftime('%Y%m%dT%H%M%SZ')}.jpg")
    Path(path).write_bytes(data)
    meta = {"kind": "ring_snapshot", "t_utc": _iso(t), "camera_id": f"ring-{d.id}", "camera_name": d.name,
            "media_path": path, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    json.dump(meta, open(path[:-4] + ".json", "w"), indent=2)
    return meta


async def _amain(a):
    ring = await connect()
    try:
        if a.cmd == "devices":
            return await list_devices(ring)
        if a.cmd == "history":
            return await history(ring, a.device, a.limit)
        if a.cmd == "download":
            return await download(ring, a.device, a.event_id, a.out_dir)
        return await snapshot(ring, a.device, a.out_dir)
    finally:
        try:
            await ring.auth.async_close()
        except Exception:
            pass


def main(argv=None):
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("devices")
    p = sp.add_parser("history"); p.add_argument("device"); p.add_argument("--limit", type=int, default=30)
    p = sp.add_parser("download"); p.add_argument("device"); p.add_argument("event_id"); p.add_argument("--out-dir", default="out/ring")
    p = sp.add_parser("snapshot"); p.add_argument("device"); p.add_argument("--out-dir", default="out/ring")
    print(json.dumps(asyncio.run(_amain(ap.parse_args(argv))), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
