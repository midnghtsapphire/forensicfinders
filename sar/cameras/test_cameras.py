"""Offline tests: recorded Caltrans fixture, mocked HTTP and a fake ring_doorbell module. SAR_LIVE_TESTS=1 adds a live public snapshot."""
import asyncio, datetime, json, os, stat, sys, tempfile, types, unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from cameras import public_cams as pc, ring_cam as rc, timeline as tl  # noqa: E402

FX = json.loads((HERE / "fixtures/caltrans_d03_cctv_trimmed.json").read_text())
JPEG = b"\xff\xd8\xff\xe0synthetic-jpeg\xff\xd9"
T0 = datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=datetime.timezone.utc)


def op_for(payload):
    def op(req, timeout=30):
        class R:
            def read(s, n=-1): return payload
            def geturl(s): return req.full_url
            def __enter__(s): return s
            def __exit__(s, *a): return False
        return R()
    return op


class Public(unittest.TestCase):
    def test_registry_is_data_driven(self):
        for k, v in pc.SOURCES.items():
            self.assertIn(v["type"], ("caltrans_cctv", "static_list"), k)
    def test_parse_and_near(self):
        cams = pc.list_cameras("caltrans-d03", opener=op_for(json.dumps(FX).encode()))
        self.assertEqual(len(cams), 2); c = cams[0]
        self.assertTrue(c["image_url"].startswith("https://cwwp2.dot.ca.gov/")); self.assertIsInstance(c["lat"], float)
        self.assertEqual(len(pc.near(cams, c["lat"], c["lon"], 0.01)), 1)
    def test_snapshot_writes_frame_and_metadata(self):
        cam = pc.parse_caltrans(FX)[0]; cam["source"] = "caltrans-d03"
        with tempfile.TemporaryDirectory() as d:
            m = pc.snapshot(cam, d, clock=lambda: T0, opener=op_for(JPEG))
            self.assertEqual(Path(m["media_path"]).read_bytes(), JPEG)
            self.assertEqual(m["t_utc"], "2026-01-02T03:04:05Z")
            self.assertEqual(json.loads(Path(m["media_path"][:-4] + ".json").read_text())["sha256"], m["sha256"])
    def test_stream_only_camera(self):
        with self.assertRaises(Exception): pc.snapshot({"id": "x", "image_url": None}, "/tmp")

    @unittest.skipUnless(os.environ.get("SAR_LIVE_TESTS") == "1", "live")
    def test_live_caltrans_snapshot(self):
        cams = [c for c in pc.list_cameras("caltrans-d03") if c["in_service"] and c["image_url"]]
        with tempfile.TemporaryDirectory() as d:
            m = pc.snapshot(cams[0], d)
            self.assertTrue(Path(m["media_path"]).read_bytes()[:2] == b"\xff\xd8")


class FakeDev:
    def __init__(s, i, name): s.id, s.name, s.family, s.kind = i, name, "doorbots", "lpd_v2"
    async def async_history(s, limit=30, kind=None):
        return [{"id": 111, "kind": "motion", "created_at": T0, "answered": False, "duration": 30},
                {"id": 112, "kind": "ding", "created_at": T0 + datetime.timedelta(minutes=5), "answered": True, "duration": 12}][:limit]
    async def async_recording_download(s, rid, filename=None, override=False):
        Path(filename).write_bytes(b"mp4-" + str(rid).encode()); return None
    async def async_get_snapshot(s): return JPEG


def fake_lib(require_2fa=False):
    calls = {}
    class Requires2FAError(Exception): pass
    class Auth:
        def __init__(s, ua, token, updater): s.token, s.updater = token, updater; calls["token"] = token
        async def async_fetch_token(s, u, p, otp=None):
            calls.setdefault("fetch", []).append(otp)
            if require_2fa and otp is None: raise Requires2FAError()
            s.updater({"access_token": "SYNTHETIC"}); return {}
        async def async_close(s): pass
    class Ring:
        def __init__(s, auth): s.auth = auth
        async def async_update_data(s): calls["updated"] = True
        def video_devices(s): return [FakeDev(1, "Front Door"), FakeDev(2, "Yard")]
    return types.SimpleNamespace(Auth=Auth, Ring=Ring, Requires2FAError=Requires2FAError), calls


class RingTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); os.environ["RING_TOKEN_CACHE"] = os.path.join(self.d.name, "tok.json")
    def tearDown(self):
        os.environ.pop("RING_TOKEN_CACHE", None); self.d.cleanup()
    def test_first_login_with_2fa_writes_private_cache_then_reuses(self):
        lib, calls = fake_lib(require_2fa=True)
        env = {"RING_USERNAME": "user@example.com", "RING_PASSWORD": "pw", "RING_OTP": "123456"}
        asyncio.run(rc.connect(lib, env))
        p = Path(os.environ["RING_TOKEN_CACHE"])
        self.assertEqual(calls["fetch"], [None, "123456"]); self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o600)
        lib2, calls2 = fake_lib(); asyncio.run(rc.connect(lib2, {}))
        self.assertEqual(calls2["token"], {"access_token": "SYNTHETIC"}); self.assertNotIn("fetch", calls2)
    def test_missing_credentials(self):
        lib, _ = fake_lib()
        with self.assertRaises(RuntimeError): asyncio.run(rc.connect(lib, {}))
        lib, _ = fake_lib(require_2fa=True)
        with self.assertRaises(RuntimeError) as e: asyncio.run(rc.connect(lib, {"RING_USERNAME": "u", "RING_PASSWORD": "secretpw"}))
        self.assertNotIn("secretpw", str(e.exception))
    def test_devices_history_download_snapshot(self):
        lib, _ = fake_lib(); ring = lib.Ring(lib.Auth("ua", {}, None))
        self.assertEqual([d["name"] for d in asyncio.run(rc.list_devices(ring))], ["Front Door", "Yard"])
        h = asyncio.run(rc.history(ring, "Front Door", limit=2))
        self.assertEqual(h[0]["t_utc"], "2026-01-02T03:04:05Z"); self.assertEqual(h[1]["event_kind"], "ding")
        m = asyncio.run(rc.download(ring, "1", 111, self.d.name, event_time=T0))
        self.assertEqual(Path(m["media_path"]).read_bytes(), b"mp4-111"); self.assertEqual(len(m["sha256"]), 64)
        s = asyncio.run(rc.snapshot(ring, "Yard", self.d.name, clock=lambda: T0))
        self.assertEqual(Path(s["media_path"]).read_bytes(), JPEG)
        with self.assertRaises(KeyError): asyncio.run(rc.history(ring, "Garage"))
    def test_no_credentials_in_source(self):
        src = (HERE / "ring_cam.py").read_text()
        self.assertNotRegex(src, r"(?i)password\s*=\s*['\"]\w")


class Timeline(unittest.TestCase):
    def test_merge_sorted_dedupe_and_satellite(self):
        cam = [tl.from_camera_meta({"kind": "public_cam_frame", "t_utc": "2025-06-28T18:00:00Z", "camera_id": "caltrans-3-1", "sha256": "a"})] * 2
        ring = [tl.from_camera_meta(e) for e in [{"kind": "ring_event", "t_utc": "2025-06-01T12:00:00+00:00", "camera_id": "ring-1", "event_id": 5}]]
        sat = tl.from_sectors({"sectors": [{"sector": "SECTOR-A", "scenes_before": ["S2C_14TLL_20250504_0_L2A"],
                                            "scenes_after": ["S1A_IW_GRDH_1SDV_20250627T125302_20250627T125327_059832_076E5F"]}]})
        out = tl.merge(cam, ring, sat)
        self.assertEqual([e["kind"] for e in out], ["satellite_scene", "ring_event", "satellite_scene", "public_cam_frame"])
        self.assertEqual(out[2]["t_utc"], "2025-06-27T12:53:02Z"); self.assertEqual(len(out), 4)
        self.assertEqual(len(tl.window(out, "2025-06-01T00:00:00Z", "2025-06-30T00:00:00Z")), 3)
    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "f.json"); json.dump({"kind": "ring_snapshot", "t_utc": "2025-01-01T00:00:00Z", "camera_id": "ring-1"}, open(p, "w"))
            out = os.path.join(d, "t.jsonl"); self.assertEqual(tl.main(["merge", p, "--out", out]), 0)
            self.assertEqual(len(Path(out).read_text().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
