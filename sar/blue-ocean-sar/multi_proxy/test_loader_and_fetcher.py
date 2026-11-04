# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  Regression test for the 2026-11-04 change that finished loader.py and
#       data_fetcher.fetch_sentinel2. standards/GREEN_MAIN_STANDARD.md requires a
#       regression test with every fix, and the defects being fixed were two:
#       (1) load_geotiff_stub raised NotImplementedError on its only call path, and
#           fetch_sentinel2 returned None unconditionally, so neither could be used;
#       (2) nothing in this repository checked VISITING_AGENTS.md section 1 at all. The
#           Anti-Scaffolding Enforcer lives in revvel-standards and runs on PRs there;
#           forensicfinders inherits the standard by convention and enforced none of it,
#           which is why four flagged lines sat in this package untouched since 2026-10-24.
# What: NEW FILE, purely additive. Nothing else was changed by it. unittest.TestCase
#       subclasses, deliberately: component 100 in registry.json runs
#       `unittest discover`, which collects ONLY TestCase subclasses, so bare test_*
#       functions here would be collected zero times and report success.
# What Worked: every assertion below was run, not asserted. Measured on Python 3.14.3 with
#       rasterio 1.x installed: a 4x5 EPSG:4326 GeoTIFF round-trips through load_geotiff
#       exactly, and so does a 4x5 EPSG:3857 one; a registered hook fires and is named in
#       the receipt, which is the proof that delegating to read_cog_window really does put
#       this loader inside the decode seam rather than beside it.
# Notes: RVS-VERIFY-001 -- "a marker is a claim; if nothing checks the claim, the marker is
#       decoration" -- applied twice here. (1) The language scan self-tests: it asserts it
#       fires on a synthetic bad line before trusting that it found none in real files, so
#       a broken matcher fails instead of passing quietly. (2) It asserts it scanned a
#       non-zero number of files, so a glob that matches nothing cannot read green.
#       The scan skips two machine-delimited regions, and that is not an allowlist of
#       violations: a REVVEL-DISABLED block exists to hold the previous code verbatim
#       (RVS-AGENT-001 requires it), and a header box like this one exists to say what
#       changed and why (SELF_HEALING_STANDARDS.md section 2.2 requires it). Both have to
#       be able to name the thing that was removed. Live code outside them is scanned with
#       no exceptions, and there is nothing to except: the four flagged lines are gone.
#       SCOPE, stated because it is narrower than it could be: this scan covers
#       multi_proxy/ only. Measured on origin/main at aea7020, the same word list hits 22
#       more lines across 10 other files under sar/ -- opendata/ (11), realdata/ (2),
#       sar_person_finder_v3.py (2), sar_dual_comms_publisher.py (1), coldtrace (1) and
#       the opendata tests (5). Widening this scan today would make main red for defects
#       it was added to report rather than ones it introduced, which
#       GREEN_MAIN_STANDARD.md forbids. Those files are the next piece of work, and the
#       repository-wide gate comes after them, not before.
# ══════════════════════════════════════════════════════════════════════════════════════════
"""The loader and the Sentinel-2 fetcher must work, and this package must stay clean."""
import glob
import json
import os
import re
import sys
import tempfile
import unittest

from . import data_fetcher, loader

HERE = os.path.dirname(os.path.abspath(__file__))
_SAR_ROOT = os.path.dirname(os.path.dirname(HERE))
if _SAR_ROOT not in sys.path:
    sys.path.insert(0, _SAR_ROOT)


def _rasterio_or_skip(case):
    """Import rasterio, or skip -- but only for a genuinely absent rasterio.

    An ImportError naming anything else is a real breakage in this package's import graph
    and must fail. Skipping on any ImportError at all is how a suite reports success while
    testing nothing; the same discipline as test_package_imports.py.
    """
    try:
        import rasterio
        return rasterio
    except ImportError as exc:
        if getattr(exc, "name", None) != "rasterio":
            raise
        case.skipTest("rasterio is not installed; sar/Dockerfile.tests installs it")


def _write_tiff(path, values, crs="EPSG:4326", bounds=(-105.0, 40.0, -104.9, 40.1)):
    import rasterio
    from rasterio.transform import from_bounds
    rows, cols = values.shape
    profile = {
        "driver": "GTiff", "height": rows, "width": cols, "count": 1, "dtype": "float32",
        "transform": from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], cols, rows),
    }
    if crs is not None:
        profile["crs"] = crs
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(values.astype("float32"), 1)
    return path


class LoaderReadsRealPixels(unittest.TestCase):
    """load_geotiff must return the pixels that are in the file."""

    def setUp(self):
        import numpy as np
        self.np = np
        self.values = np.arange(20, dtype="float32").reshape(4, 5)
        self.dir = tempfile.mkdtemp()

    def test_load_geotiff_round_trips_a_lonlat_raster(self):
        _rasterio_or_skip(self)
        path = _write_tiff(os.path.join(self.dir, "t.tif"), self.values)
        band, meta = loader.load_geotiff(path)
        self.assertEqual(band.shape, (4, 5))
        self.assertEqual(str(band.dtype), "float64")
        self.np.testing.assert_array_equal(band, self.values.astype("float64"))
        self.assertEqual(meta["decoder"], "read_cog_window",
                         "the loader must go through the repository's raster ingress, not "
                         "open rasterio itself -- that is the whole reason it delegates")
        self.assertIn("4326", str(meta["crs"]))

    def test_load_geotiff_round_trips_a_projected_raster(self):
        """The documented bbox round trip must not mangle a non-lon/lat grid."""
        _rasterio_or_skip(self)
        path = _write_tiff(os.path.join(self.dir, "merc.tif"), self.values, crs="EPSG:3857",
                           bounds=(-11688546.0, 4865942.0, -11677416.0, 4880381.0))
        band, _ = loader.load_geotiff(path)
        self.assertEqual(band.shape, (4, 5))
        self.np.testing.assert_array_equal(band, self.values.astype("float64"))

    def test_registered_hook_fires_and_is_named_in_the_receipt(self):
        """Proof the loader is inside the decode seam, not merely near it."""
        _rasterio_or_skip(self)
        import decode_hooks
        fired = []

        def shift(payload, meta=None):
            fired.append(True)
            return payload + 100.0

        decode_hooks.register("test_loader_shift", shift, decoders=["read_cog_window"])
        self.addCleanup(decode_hooks.unregister, "test_loader_shift")
        path = _write_tiff(os.path.join(self.dir, "t.tif"), self.values)
        meta = {}
        band, meta = loader.load_geotiff(path, meta=meta)
        self.assertEqual(fired, [True], "a hook scoped to read_cog_window did not run")
        self.assertEqual(meta.get("decode_hooks_applied"), ["test_loader_shift"])
        self.assertEqual(band[0, 0], 100.0, "the hook ran but its result was discarded")

    def test_deprecated_alias_still_works(self):
        """load_geotiff_stub is kept because nothing here is deleted; it must not be dead."""
        _rasterio_or_skip(self)
        path = _write_tiff(os.path.join(self.dir, "t.tif"), self.values)
        band, _ = loader.load_geotiff_stub(path)
        self.np.testing.assert_array_equal(band, self.values.astype("float64"))

    def test_raster_without_crs_is_refused_by_name(self):
        """A documented limit nothing enforces is a comment, not a limit."""
        _rasterio_or_skip(self)
        path = _write_tiff(os.path.join(self.dir, "nocrs.tif"), self.values, crs=None)
        with self.assertRaises(ValueError) as caught:
            loader.load_geotiff(path)
        self.assertIn("no CRS", str(caught.exception))


class LoaderIsNoLongerUnwritten(unittest.TestCase):
    """The direct regression, and it runs whether or not rasterio is installed."""

    def test_load_geotiff_does_not_raise_not_implemented(self):
        missing = os.path.join(tempfile.mkdtemp(), "absent.tif")
        try:
            loader.load_geotiff(missing)
        except NotImplementedError as exc:
            self.fail(f"load_geotiff is still unwritten: {exc}")
        except Exception:
            pass  # any other failure is the file being absent, which is correct

    def test_alias_does_not_raise_not_implemented(self):
        missing = os.path.join(tempfile.mkdtemp(), "absent.tif")
        try:
            loader.load_geotiff_stub(missing)
        except NotImplementedError as exc:
            self.fail(f"the preserved alias is still unwritten: {exc}")
        except Exception:
            pass


class FetchSentinel2Searches(unittest.TestCase):
    """fetch_sentinel2 must search, and None must mean 'nothing matched'."""

    SCENES = [
        {"id": "S2A_1", "collection": "sentinel-2-l2a", "datetime": "2025-06-03T18:00:00Z",
         "cloud_cover": 4.1, "bbox": [-105.0, 40.0, -104.9, 40.1],
         "assets": {"red": "https://example.invalid/1/B04.tif",
                    "swir22": "https://example.invalid/1/B12.tif"}},
        {"id": "S2B_2", "collection": "sentinel-2-l2a", "datetime": "2025-06-18T18:00:00Z",
         "cloud_cover": 61.0, "bbox": [-105.0, 40.0, -104.9, 40.1],
         "assets": {"red": "https://example.invalid/2/B04.tif"}},
    ]
    BBOX = (-105.0, 40.0, -104.9, 40.1)
    DATES = ("2025-06-01", "2025-06-30")

    def setUp(self):
        from geo_connectors import stac
        self.stac = stac
        self.calls = []
        self.dir = tempfile.mkdtemp()
        self._real_search = stac.search
        self.addCleanup(setattr, stac, "search", self._real_search)

    def _fake_search(self, scenes):
        def search(bbox, datetime, collections, **kw):
            self.calls.append({"bbox": bbox, "datetime": datetime,
                               "collections": list(collections), "kw": kw})
            return list(scenes)
        return search

    def test_writes_a_manifest_holding_every_asset_href(self):
        self.stac.search = self._fake_search(self.SCENES)
        out = data_fetcher.fetch_sentinel2(self.BBOX, self.DATES, out_dir=self.dir)
        self.assertIsNotNone(out, "a search that matched two scenes must not return None")
        self.assertTrue(os.path.isfile(out))
        with open(out, encoding="utf-8") as fh:
            payload = json.load(fh)
        self.assertEqual(payload["scene_count"], 2)
        self.assertEqual(payload["collection"], "sentinel-2-l2a")
        hrefs = [h for s in payload["scenes"] for h in s["assets"].values()]
        self.assertIn("https://example.invalid/1/B12.tif", hrefs)
        self.assertEqual(len(hrefs), 3)

    def test_asks_the_open_endpoint_for_the_right_collection(self):
        self.stac.search = self._fake_search(self.SCENES)
        data_fetcher.fetch_sentinel2(self.BBOX, self.DATES, out_dir=self.dir)
        self.assertEqual(len(self.calls), 1)
        call = self.calls[0]
        self.assertEqual(call["collections"], ["sentinel-2-l2a"])
        self.assertEqual(call["datetime"], "2025-06-01/2025-06-30")
        self.assertEqual(call["kw"].get("endpoint"), self.stac.EARTH_SEARCH,
                         "Earth Search needs no account; a credentialed endpoint would "
                         "reintroduce the signup wall this change removed")

    def test_none_now_means_nothing_matched_and_writes_no_file(self):
        self.stac.search = self._fake_search([])
        out = data_fetcher.fetch_sentinel2(self.BBOX, self.DATES, out_dir=self.dir)
        self.assertIsNone(out)
        self.assertEqual(glob.glob(os.path.join(self.dir, "*.json")), [],
                         "an empty search must not leave an empty manifest behind")

    def test_find_sentinel2_returns_the_scenes_themselves(self):
        self.stac.search = self._fake_search(self.SCENES)
        scenes = data_fetcher.find_sentinel2(self.BBOX, self.DATES)
        self.assertEqual([s["id"] for s in scenes], ["S2A_1", "S2B_2"])
        self.assertEqual(scenes[1]["cloud_cover"], 61.0,
                         "no cloud threshold may be applied inside the fetcher")


# The enforcer's word list, assembled from fragments rather than written whole. Without
# that, this file would match itself and the scan below would have to exempt it -- and a
# guard that exempts itself teaches the next reader that exemptions are normal. Four extra
# characters of awkwardness buys a scan with no exclusions at all. Source of truth for the
# list is revvel-standards/.github/workflows/anti-scaffolding-enforcer.yml.
_WORDS = ("TO" + "DO", "FIX" + "ME", "scaff" + "old", "place" + "holder")
_PHRASES = ("phase " + "1", "phase " + "2", "mvp " + "first", "coming " + "soon",
            "not yet " + "implemented")
# The enforcer's own false-positive exclusions, mirrored PER WORD rather than as one blanket
# list, so this guard is neither stricter nor looser than the thing it stands in for. A
# blanket list would let any line mentioning a github URL escape the scan entirely.
_EXEMPT = {
    _WORDS[0]: (_WORDS[0] + ": See issue #",),
    _WORDS[2]: ("anti-" + "scaff" + "old", "scaff" + "olding tools like npm init",
                "anti_" + "scaff" + "old"),
    _WORDS[3]: ("place" + "holder=", "::" + "place" + "holder",
                "place" + "holder values", 'alt="' + "place" + 'holder"',
                "search projects"),
}
_RULE = re.compile(r"^\s*#\s*[═]{20,}")
_DISABLED_OPEN = "REVVEL-" + "DISABLED |"
_DISABLED_END = "REVVEL-" + "DISABLED-END"


def _hits(line):
    low = line.lower()
    found = []
    for word in _WORDS:
        if word.lower() not in low:
            continue
        if any(ex.lower() in low for ex in _EXEMPT.get(word, ())):
            continue
        found.append(word)
    found += [p for p in _PHRASES if p in low]
    return found


def _live_lines(text):
    """Lines outside both delimited documentation regions, as (lineno, text).

    Skipped: a header box between two full-width rules, and a REVVEL-DISABLED block. Both
    are required by the standards to quote what they replaced, so both have to be able to
    contain the words.
    """
    out, in_box, in_block = [], False, False
    for n, line in enumerate(text.splitlines(), 1):
        if _DISABLED_OPEN in line:
            in_block = True
            continue
        if _DISABLED_END in line:
            in_block = False
            continue
        if in_block:
            continue
        if _RULE.match(line):
            in_box = not in_box
            continue
        if in_box:
            continue
        out.append((n, line))
    return out


class MultiProxyLiveCodeIsFinished(unittest.TestCase):
    """No live line in this package may claim the code is unfinished."""

    def test_the_matcher_fires_on_a_known_bad_line(self):
        """Self-test first. A matcher that finds nothing proves nothing until this passes."""
        for word in _WORDS + _PHRASES:
            with self.subTest(word=word):
                self.assertTrue(_hits(f"    x = 1  # {word} something"),
                                f"the matcher missed {word!r}; every result below is void")
        self.assertEqual(_hits("    y = 2  # ordinary comment"), [])

    def test_the_region_skipper_keeps_live_code_and_drops_documentation(self):
        text = "\n".join([
            "# " + "═" * 40,
            "# Why: removed a " + _WORDS[3] + " here",
            "# " + "═" * 40,
            "live_one = 1",
            "# " + _DISABLED_OPEN + " AGENT: x",
            "# " + _WORDS[0] + ": the old line",
            "# " + _DISABLED_END,
            "live_two = 2",
        ])
        kept = [t for _, t in _live_lines(text)]
        self.assertEqual(kept, ["live_one = 1", "live_two = 2"])

    def test_no_live_line_in_multi_proxy_uses_the_words(self):
        files = sorted(glob.glob(os.path.join(HERE, "*.py")))
        self.assertGreater(
            len(files), 5,
            f"only {len(files)} python files found in {HERE} -- the glob is wrong, and this "
            f"guard proves nothing until that is explained")
        offences = []
        for path in files:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            for lineno, line in _live_lines(text):
                found = _hits(line)
                if found:
                    rel = os.path.basename(path)
                    offences.append(f"{rel}:{lineno} {sorted(set(found))}: {line.strip()}")
        self.assertEqual(
            offences, [],
            "these live lines say the code is unfinished, which VISITING_AGENTS.md section "
            "1 forbids -- finish the code or, if it genuinely cannot be finished, say so in "
            "the PR body rather than in the source:\n    " + "\n    ".join(offences))


if __name__ == "__main__":
    unittest.main()
