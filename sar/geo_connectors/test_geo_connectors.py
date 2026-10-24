"""Offline tests replay responses recorded from the live endpoints on 2026-10-21 (neutral bbox in
the Nebraska Sandhills; no case areas). Live tests run only with SAR_LIVE_TESTS=1."""
import io, json, os, subprocess, sys, unittest, urllib.error
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from geo_connectors import arcgis, dep3, mcp_server, stac, wayback  # noqa: E402
from geo_connectors import netio as http  # noqa: E402

FX = HERE / "fixtures"
NEUTRAL = [-100.50, 41.00, -100.45, 41.05]
LIVE = os.environ.get("SAR_LIVE_TESTS") == "1"


class Replay:
    """Opener that serves recorded responses in order and checks the request URL matches."""
    def __init__(self, name):
        self.rows = json.loads((FX / name).read_text()); self.i = 0; self.seen = []
    def __call__(self, req, timeout=30):
        row = self.rows[self.i]; self.i += 1; self.seen.append(req.full_url)
        assert req.full_url.split("?")[0] == row["url"].split("?")[0], (req.full_url, row["url"])
        data = row["response"].encode()
        class R:
            def read(s, n=-1): return data
            def geturl(s): return req.full_url
            def __enter__(s): return s
            def __exit__(s, *a): return False
        return R()


class Http(unittest.TestCase):
    def test_retry_then_success_with_backoff(self):
        calls, sleeps = [], []
        def op(req, timeout=30):
            calls.append(1)
            if len(calls) < 3:
                raise urllib.error.HTTPError(req.full_url, 503, "busy", {}, io.BytesIO(b""))
            class R:
                def read(s, n=-1): return b'{"ok": 1}'
                def geturl(s): return req.full_url
                def __enter__(s): return s
                def __exit__(s, *a): return False
            return R()
        self.assertEqual(http.request_json(stac.EARTH_SEARCH + "/", opener=op, sleep=sleeps.append, backoff=1), {"ok": 1})
        self.assertEqual(len(calls), 3); self.assertTrue(1 <= sleeps[0] < 1.3 and 2 <= sleeps[1] < 2.3)
    def test_gives_up_and_does_not_retry_4xx(self):
        def op503(req, timeout=30): raise urllib.error.URLError("down")
        with self.assertRaises(http.ConnectorError): http.request(stac.EARTH_SEARCH, opener=op503, sleep=lambda s: None, retries=2)
        n = []
        def op400(req, timeout=30):
            n.append(1); raise urllib.error.HTTPError(req.full_url, 400, "bad", {}, io.BytesIO(b"bad datetime"))
        with self.assertRaises(http.ConnectorError): http.request(stac.EARTH_SEARCH, opener=op400, sleep=lambda s: None)
        self.assertEqual(len(n), 1)
    def test_allowlist_and_https(self):
        with self.assertRaises(http.ConnectorError): http.request("https://evil.example.org/x")
        with self.assertRaises(http.ConnectorError): http.request("http://earth-search.aws.element84.com/v1")


class Stac(unittest.TestCase):
    def test_datetime_fix(self):
        self.assertEqual(stac.normalize_datetime("2025-06-01/2025-06-30"), "2025-06-01T00:00:00Z/2025-06-30T23:59:59Z")
        self.assertEqual(stac.normalize_datetime("../2025-06-30"), "../2025-06-30T23:59:59Z")
    def test_bbox_validation(self):
        with self.assertRaises(ValueError): stac.validate_bbox([1, 2, 0, 3])
    def test_s2_search_paginates_from_fixture(self):
        op = Replay("earthsearch_s2.json")
        items = stac.search(NEUTRAL, "2025-06-01/2025-06-30", ["sentinel-2-l2a"], limit=2, max_items=3, opener=op)
        self.assertEqual(len(items), 3); self.assertEqual(op.i, 2)
        self.assertTrue(all(i["collection"] == "sentinel-2-l2a" and "red" in i["assets"] for i in items))
    def test_s1_and_hls(self):
        s1 = stac.search(NEUTRAL, "2025-06-01/2025-06-30", ["sentinel-1-grd"], limit=2, max_items=2, opener=Replay("earthsearch_s1.json"))
        self.assertTrue(s1[0]["id"].startswith("S1"))
        h = stac.search(NEUTRAL, "2025-06-01/2025-06-30", ["HLSS30_2.0"], endpoint=stac.CMR_LPCLOUD, limit=2, max_items=2, opener=Replay("cmr_hls.json"))
        self.assertTrue(h[0]["id"].startswith("HLS.S30"))
    def test_band_math(self):
        import numpy as np
        self.assertAlmostEqual(float(stac.ndvi([0.1], [0.5])[0]), 0.6667, places=3)
        self.assertTrue(np.isnan(stac.ndvi([0], [0])[0]))
        d = stac.delta_ndvi([[0.1] * 4] * 4, [[0.5] * 4] * 4, [[0.1] * 4] * 4, [[0.5] * 3 + [0.1]] + [[0.5] * 4] * 3)
        r, c, _ = stac.anomalies(d, sigma=2)
        self.assertEqual((r, c), ([0], [3]))
        self.assertAlmostEqual(float(stac.log_ratio_db([1.0], [10.0])[0]), 10.0, places=4)


class Dep3(unittest.TestCase):
    def test_export_metadata(self):
        m = dep3.export_dtm([-100.50, 41.00, -100.495, 41.005], size=(16, 16), opener=Replay("3dep_export.json"))
        self.assertEqual((m["width"], m["height"]), (16, 16)); self.assertTrue(m["href"].startswith("https://elevation.nationalmap.gov/"))
    def test_samples(self):
        s = dep3.sample_elevations([(-100.48, 41.02), (-100.46, 41.04)], opener=Replay("3dep_samples.json"))
        self.assertEqual(len(s), 2); self.assertTrue(all(700 < x["elevation_m"] < 1000 for x in s))
    def test_recorded_dtm_tiff_and_difference(self):
        try: import rasterio
        except ImportError: self.skipTest("rasterio not installed")
        with rasterio.open(FX / "3dep_dtm16.tif") as ds: a = ds.read(1)
        self.assertEqual(a.shape, (16, 16)); self.assertTrue(700 < float(a.mean()) < 1000)
        self.assertEqual(float(dep3.dtm_difference(a, a + 0.5).mean()), 0.5)
        with self.assertRaises(ValueError): dep3.dtm_difference(a, a[:2])


class Wayback(unittest.TestCase):
    def test_cdx_and_digest_diff(self):
        rows = wayback.query_cdx("example.com", 2006, 2008, limit=4, collapse=None, opener=Replay("wayback_cdx_example_com.json"))
        self.assertEqual(len(rows), 4)
        ch = wayback.digest_changes(rows)
        self.assertEqual(len(ch), 1)  # all four share one digest
        rows[2]["digest"] = "CHANGED"
        self.assertEqual([c["timestamp"] for c in wayback.digest_changes(rows)], ["20060101064348", "20060102100342", "20060102114708"])


class ArcGIS(unittest.TestCase):
    def test_paging(self):
        op = Replay("arcgis_pages.json")
        fc = arcgis.query_layer("https://sampleserver6.arcgisonline.com/arcgis/rest/services/USA/MapServer/0", where="st='NE'", page_size=2, max_features=4, opener=op)
        self.assertEqual(len(fc["features"]), 4); self.assertEqual(op.i, 2); self.assertIn("resultOffset=2", op.seen[1])


class Mcp(unittest.TestCase):
    def test_list_and_call_offline(self):
        r = mcp_server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual({t["name"] for t in r["result"]["tools"]}, set(mcp_server.TOOLS))
        r = mcp_server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "sample_usgs_elevation",
                               "arguments": {"points": [[-100.48, 41.02], [-100.46, 41.04]]}}}, opener=Replay("3dep_samples.json"))
        self.assertFalse(r["result"]["isError"]); self.assertEqual(len(json.loads(r["result"]["content"][0]["text"])), 2)
    def test_errors(self):
        self.assertIn("error", mcp_server.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "nope"}}))
        r = mcp_server.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "search_stac_satellite", "arguments": {"bbox": [1, 2, 0, 3], "datetime": "2025-01-01"}}})
        self.assertTrue(r["result"]["isError"])
        self.assertIsNone(mcp_server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))
    def test_stdio_subprocess(self):
        p = subprocess.run([sys.executable, "-m", "geo_connectors.mcp_server"], cwd=HERE.parent, capture_output=True, text=True, timeout=30,
                           input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n{"jsonrpc":"2.0","id":2,"method":"tools/list"}\n')
        lines = [json.loads(l) for l in p.stdout.splitlines()]
        self.assertEqual(lines[0]["result"]["serverInfo"]["name"], "forensicfinders-geo"); self.assertEqual(len(lines[1]["result"]["tools"]), 5)



class Ops(unittest.TestCase):
    def test_verify_connectors_writes_github_output(self):
        from geo_connectors import verify_connectors as vc
        import tempfile
        orig = dict(vc.CHECKS)
        try:
            vc.CHECKS.clear(); vc.CHECKS.update({"good": lambda: True, "bad": lambda: (_ for _ in ()).throw(http.ConnectorError("down"))})
            with tempfile.TemporaryDirectory() as d:
                gho = os.path.join(d, "gho"); os.environ["GITHUB_OUTPUT"] = gho
                rc = vc.main(["--out", os.path.join(d, "h.json")])
                self.assertEqual(rc, 1); self.assertEqual(open(gho).read(), "status=FAIL\n")
                vc.CHECKS.pop("bad"); open(gho, "w").close()
                self.assertEqual(vc.main(["--out", os.path.join(d, "h.json")]), 0); self.assertEqual(open(gho).read(), "status=PASS\n")
        finally:
            os.environ.pop("GITHUB_OUTPUT", None); vc.CHECKS.clear(); vc.CHECKS.update(orig)

    def test_run_sectors_from_fixtures(self):
        from geo_connectors import run_sectors as rs
        calls = []
        orig_search, orig_samples = rs.stac.search, rs.dep3.sample_elevations
        rs.stac.search = lambda *a, **k: (calls.append(k.get("query")) or orig_search(NEUTRAL, "2025-06-01/2025-06-30", ["sentinel-2-l2a"], limit=2, max_items=3, opener=Replay("earthsearch_s2.json")))
        rs.dep3.sample_elevations = lambda pts, **k: orig_samples([(-100.48, 41.02), (-100.46, 41.04)], opener=Replay("3dep_samples.json"))[:1]
        try:
            out = rs.run_sector({"id": "SECTOR-A", "bbox": NEUTRAL}, {"before": "2025-05-01/2025-05-31", "after": "2025-06-01/2025-06-30"}, 20, use_cog=False)
        finally:
            rs.stac.search, rs.dep3.sample_elevations = orig_search, orig_samples
        self.assertEqual(calls[0], {"eo:cloud_cover": {"lt": 20}})
        self.assertEqual(len(out["scenes_after"]), 3); self.assertEqual(out["ndvi"]["status"], "no_data")
        self.assertTrue(out["centre_elevation"][0]["elevation_m"] > 700)

    def test_example_case_config_is_synthetic(self):
        from geo_connectors import run_sectors as rs
        cfg = rs.load_config(str(HERE.parent / "case" / "example.config.yaml"))
        self.assertTrue(cfg["case_id"].startswith("SYNTH-"))
        for s in cfg["sectors"]:
            w, so, e, n = s["bbox"]; self.assertTrue(-101 < w < e < -100 and 40.9 < so < n < 41.1)

@unittest.skipUnless(LIVE, "set SAR_LIVE_TESTS=1 to hit the public endpoints")
class Live(unittest.TestCase):
    def test_earth_search(self): self.assertTrue(stac.search(NEUTRAL, "2025-06-01/2025-06-30", ["sentinel-2-l2a"], max_items=1))
    def test_cmr(self): self.assertTrue(stac.search(NEUTRAL, "2025-06-01/2025-06-30", ["HLSS30_2.0"], endpoint=stac.CMR_LPCLOUD, max_items=1))
    def test_3dep(self): self.assertTrue(dep3.sample_elevations([(-100.48, 41.02)])[0]["elevation_m"])
    def test_wayback(self): self.assertTrue(wayback.query_cdx("example.com", 2006, 2007, limit=3))
    def test_arcgis(self): self.assertTrue(arcgis.query_layer("https://sampleserver6.arcgisonline.com/arcgis/rest/services/USA/MapServer/0", max_features=1)["features"])
    def test_cog_ndvi(self):
        import numpy as np
        it = stac.search(NEUTRAL, "2025-06-01/2025-06-30", ["sentinel-2-l2a"], max_items=1, query={"eo:cloud_cover": {"lt": 20}})[0]
        b = [-100.48, 41.02, -100.475, 41.025]
        v = stac.ndvi(stac.read_cog_window(it["assets"]["red"], b), stac.read_cog_window(it["assets"]["nir"], b))
        self.assertTrue(-1 <= float(np.nanmean(v)) <= 1)


if __name__ == "__main__":
    unittest.main()


class DecodeSeam(unittest.TestCase):
    """read_cog_window must route its band through the decode seam (sar/decode_hooks.py).

    rasterio is an optional dependency, so rather than skip -- a skipped test proves
    nothing -- these stub the three rasterio names read_cog_window imports inside its own
    body. The assertions compare returned VALUES against what the hook produced, so if the
    seam were removed from read_cog_window the band would come back unmodified and these
    fail. That is the mutation test, built into the assertion.
    """
    def setUp(self):
        import decode_hooks
        decode_hooks.clear()
        self.hooks = decode_hooks
        self.saved = {k: sys.modules.get(k) for k in ("rasterio", "rasterio.warp", "rasterio.windows")}

    def tearDown(self):
        self.hooks.clear()
        for k, v in self.saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v

    def _stub(self, arr):
        import types
        ds = type("DS", (), {"crs": "EPSG:32614", "transform": (1, 0, 0, 0, -1, 0),
                             "read": lambda s, *a, **k: arr,
                             "__enter__": lambda s: s, "__exit__": lambda s, *a: False})()
        rio = types.ModuleType("rasterio"); rio.open = lambda href: ds
        warp = types.ModuleType("rasterio.warp"); warp.transform_bounds = lambda *a, **k: (0.0, 0.0, 1.0, 1.0)
        wins = types.ModuleType("rasterio.windows"); wins.from_bounds = lambda *a, **k: "WIN"
        rio.warp, rio.windows = warp, wins
        sys.modules.update({"rasterio": rio, "rasterio.warp": warp, "rasterio.windows": wins})

    def test_unhooked_band_is_unchanged(self):
        import numpy as np
        self._stub(np.array([[1.0, 2.0], [3.0, 4.0]]))
        out = stac.read_cog_window("https://example.org/b.tif", NEUTRAL)
        self.assertEqual(out.tolist(), [[1.0, 2.0], [3.0, 4.0]])

    def test_hook_reaches_read_cog_window(self):
        import numpy as np
        self._stub(np.array([[1.0, 2.0], [3.0, 4.0]]))
        self.hooks.register("plus100", lambda p, m: p + 100.0)
        out = stac.read_cog_window("https://example.org/b.tif", NEUTRAL)
        self.assertEqual(out.tolist(), [[101.0, 102.0], [103.0, 104.0]])

    def test_receipt_describes_the_decode(self):
        import numpy as np
        self._stub(np.array([[1.0]]))
        self.hooks.register("noop", lambda p, m: p)
        meta = {}
        stac.read_cog_window("https://example.org/b.tif", NEUTRAL, meta=meta)
        self.assertEqual(meta["decode_hooks_applied"], ["noop"])
        self.assertEqual(meta["decoder"], "read_cog_window")
        self.assertEqual(meta["href"], "https://example.org/b.tif")

    def test_one_registry_is_shared_with_instrument_input(self):
        """Both callers must import the SAME decode_hooks module object, or a hook
        registered once would apply to rasters but not to instrument files."""
        sys.path.insert(0, str(HERE.parent / "instrument_input"))
        import instrument_input as ii
        self.assertIs(ii.decode_hooks, self.hooks)


class Hyp3Pairs(unittest.TestCase):
    """Pair selection for ASF HyP3, replayed from a live jsonlite response recorded
    2026-10-24 over the neutral Nebraska Sandhills bbox (no case areas).

    The assertions are about behaviour that would be wrong in a way nothing else catches:
    pairing across tracks produces an interferogram of the sensor moving, not the ground.
    """
    def setUp(self):
        from geo_connectors import hyp3
        self.h = hyp3
        hyp3.allow_asf_hosts()
        self.raw = (FX / "asf_slc_search.json").read_bytes()

    def _opener(self):
        data = self.raw

        class R:
            def read(s, n=-1): return data
            def geturl(s): return "https://api.daac.asf.alaska.edu/services/search/param"
            def __enter__(s): return s
            def __exit__(s, *a): return False
        return lambda req, timeout=30: R()

    def _granules(self):
        return self.h.search_slc(NEUTRAL, "2024-06-01", "2024-07-15", opener=self._opener())

    def test_fixture_parses_into_granules(self):
        g = self._granules()
        self.assertEqual(len(g), 8)
        self.assertTrue(all(x["granule"] for x in g))
        self.assertTrue(all(isinstance(x["path"], int) for x in g))

    def test_field_rename_raises_instead_of_pairing_on_none(self):
        """If ASF drops granuleName, every record would otherwise compare equal on None."""
        with self.assertRaises(http.ConnectorError) as cm:
            self.h.normalise({"path": 85, "flightDirection": "DESCENDING", "startTime": "2024-07-14T12:53:09Z"})
        self.assertIn("granuleName", str(cm.exception))

    def test_never_pairs_across_path_or_direction(self):
        pairs = self.h.interferometric_pairs(self._granules(), min_days=0, max_days=10000)
        self.assertTrue(pairs, "fixture should contain at least one same-track pair")
        by_name = {g["granule"]: g for g in self._granules()}
        for p in pairs:
            a, b = by_name[p["reference"]], by_name[p["secondary"]]
            self.assertEqual(a["path"], b["path"])
            self.assertEqual(a["direction"], b["direction"])
            self.assertEqual(a["polarization"], b["polarization"])

    def test_fixture_really_does_contain_mixed_tracks(self):
        """Guards the guard: if the fixture had one track, the test above would pass empty."""
        tracks = {(g["path"], g["direction"]) for g in self._granules()}
        self.assertGreater(len(tracks), 1)

    def test_reference_is_the_earlier_acquisition(self):
        for p in self.h.interferometric_pairs(self._granules(), min_days=0, max_days=10000):
            self.assertLess(p["reference_time"], p["secondary_time"])
            self.assertGreater(p["days"], 0)

    def test_baseline_window_is_enforced(self):
        wide = self.h.interferometric_pairs(self._granules(), min_days=0, max_days=10000)
        none = self.h.interferometric_pairs(self._granules(), min_days=900, max_days=1000)
        self.assertEqual(none, [], "no pair should survive an impossible baseline window")
        self.assertTrue(wide)

    def test_can_insar_false_is_excluded(self):
        g = self._granules()
        for x in g:
            x["can_insar"] = False
        self.assertEqual(self.h.interferometric_pairs(g, min_days=0, max_days=10000), [])

    def test_summarise_tracks_counts_every_granule(self):
        g = self._granules()
        self.assertEqual(sum(self.h.summarise_tracks(g).values()), len(g))

    def test_submit_uses_the_burst_endpoint_only_when_asked(self):
        calls = []

        class FakeClient:
            def submit_insar_job(s, ref, sec, name):
                calls.append(("scene", ref, sec, name)); return object()

            def submit_insar_isce_burst_job(s, ref, sec, name):
                calls.append(("burst", ref, sec, name)); return object()

        pairs = [{"reference": "A", "secondary": "B"}, {"reference": "C", "secondary": "D"}]
        self.h.submit_insar(pairs, "run", FakeClient(), burst=False)
        self.h.submit_insar(pairs, "run", FakeClient(), burst=True, limit=1)
        self.assertEqual([c[0] for c in calls], ["scene", "scene", "burst"])
        self.assertEqual(calls[0][1:], ("A", "B", "run-001"))
        self.assertEqual(calls[2][1:], ("A", "B", "run-001"))

    def test_missing_credentials_say_what_to_do(self):
        import os
        saved = {k: os.environ.pop(k, None) for k in ("EARTHDATA_USERNAME", "EARTHDATA_PASSWORD")}
        try:
            with self.assertRaises(http.ConnectorError) as cm:
                self.h.earthdata_auth(netrc_path=str(FX / "does_not_exist_netrc"))
            self.assertIn("EARTHDATA_USERNAME", str(cm.exception))
            self.assertIn("urs.earthdata.nasa.gov", str(cm.exception))
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v

    def test_same_pass_slices_are_never_paired(self):
        """Regression: path 107 carries frames 128 and 132 taken 25 s apart on one pass.
        Keyed without frame they paired with each other, giving days = 0.0 -- a pair with
        no temporal baseline, over different ground. Asking for min_days=0 must not
        resurrect that."""
        pairs = self.h.interferometric_pairs(self._granules(), min_days=0, max_days=10000)
        self.assertTrue(pairs)
        for p in pairs:
            self.assertGreaterEqual(p["days"], self.h.MIN_SEPARATION_DAYS)

    def test_every_pair_shares_a_frame_and_repeats_on_the_cycle(self):
        """The fixture's four tracks each repeat at 12 days. Anything else is a mispair."""
        pairs = self.h.interferometric_pairs(self._granules(), min_days=0, max_days=10000)
        self.assertEqual(len(pairs), 4)
        self.assertTrue(all(abs(p["days"] - 12.0) < 0.01 for p in pairs), [p["days"] for p in pairs])
        self.assertTrue(all(p["frame"] is not None for p in pairs))
