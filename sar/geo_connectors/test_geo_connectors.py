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
