# ════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-06
# Why:  fetch_sentinel_ndvi returned the two raw GeoTIFF response bodies as bytes while its
#       signature, its docstring and its only real consumer all said xarray DataArrays.
#       Nothing in the suite noticed, because no test ever got as far as the response: the
#       one existing sentinel test asserts the NoDataError raised when credentials are
#       absent, which returns before any HTTP call. This file is the regression test
#       GREEN_MAIN_STANDARD.md asks for alongside the fix.
# What: NEW FILE, purely additive. It drives fetch_sentinel_ndvi over a real FLOAT32
#       GeoTIFF built here with rasterio -- not a mock of the parse step -- and asserts the
#       three properties _compute_ndvi_sync in services/temporal.py actually consumes:
#       a 2-D .values, a working .rio.transform(), and NaN rather than -9999 where the
#       scene classification masked the pixel.
# What Worked: all six tests run and pass. The end-to-end test feeds the result of
#       fetch_sentinel_ndvi straight into compute_ndvi_diff and checks the anomaly's
#       coordinates against the transform by hand, so the two halves of the contract are
#       proven to fit rather than asserted separately and assumed to meet.
# Notes: anti-decoration properties, per RVS-VERIFY-001 section 5.3 -- "a marker is a claim;
#       if nothing checks the claim, the marker is decoration":
#       (1) test_bytes_cannot_satisfy_the_consumer pins the OLD behaviour as a failure. It
#           feeds bytes to _compute_ndvi_sync and requires AttributeError. If someone
#           reverts the fix, that test is what explains why the others broke; and if it ever
#           stops raising, these tests have stopped testing the thing they were written for.
#       (2) The GeoTIFF fixtures declare NO nodata tag, exactly as the Sentinel Hub
#           response does. A fixture that declared one would let masked=True do the masking
#           by itself and the -9999 handling in _tiff_to_ndvi_array would go unexercised
#           while still appearing to be covered.
#       (3) The band-dimension test is separate from the shape test, because squeezing and
#           masking fail in different ways and a single combined assertion would not say
#           which one regressed.
#       (4) CLOUD_VALUE is a literal here and is NOT read from sentinel._CLOUD_SENTINEL,
#           and test_cloud_sentinel_matches_the_evalscript pins that constant to the
#           evalscript literal instead. A fixture built from the constant follows it.
#       (5) One fixture pixel holds a valid NEGATIVE NDVI, and
#           test_valid_negative_ndvi_is_not_masked requires it to survive.
#       THE FIRST VERSION OF THIS FILE HAD NEITHER (4) NOR (5), and mutation testing is
#       what found that out -- not review and not reasoning. Two mutations passed all six
#       original tests: changing _CLOUD_SENTINEL to -999.0, which the fixture silently
#       followed because it read the constant; and widening the mask to `array > 0.0`,
#       which masked the identical set because every pixel in the fixture was positive.
#       Both are failures a reader would call obvious once stated, and neither was caught
#       by six tests that all passed. A third mutation -- moving .load() outside the
#       context managers in _tiff_to_ndvi_array -- is still uncaught, and that one is
#       recorded in the helper's own docstring rather than papered over here, because the
#       behaviour turned out not to be observable on this rasterio version at all.
#       NOT covered here: the live Sentinel Hub API. There are no credentials in CI and the
#       tier is metered, so the transport is stubbed. What is NOT stubbed is the part that
#       was broken -- the bytes-to-DataArray parse runs for real on real GeoTIFF bytes.
#       ALSO NOT COVERED: the production dependency versions. These tests passed against
#       rasterio 1.5.2 and numpy 2.5.0, while requirements.txt pins rasterio==1.3.10 and
#       numpy==1.26.4. Neither pinned version publishes a distribution for Python 3.14, so
#       they could not be installed here to check -- requirements.txt as a whole cannot be
#       installed on this interpreter, which is a pre-existing problem for the backend and
#       not one this file created. rasterio and numpy are therefore left UNPINNED in
#       requirements-test.txt on purpose: pinning them to the production versions, as a
#       review bot suggested, would make the test requirements uninstallable on the only
#       interpreter available, which trades a stated risk for a certain breakage. Which
#       Python versions this backend supports is Audrey's call, not a detail to settle
#       inside a test file.
# ════════════════════════════════════════════════════════════════════════════════════════
"""fetch_sentinel_ndvi must return what compute_ndvi_diff can actually consume."""
import io

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_bounds

from coldtrace.backend.services import sentinel, temporal

BBOX = (-122.50, 37.70, -122.40, 37.80)
SIZE = 16
# The pixel that changes between the two dates, and by how much. One clean outlier in an
# otherwise flat delta field, so exactly one anomaly is expected and its position is known.
CHANGED_YX = (4, 11)
BASE_NDVI = 0.50
CHANGED_NDVI = 0.90
# Pixels the evalscript would mark cloud. Masked in BOTH dates, so the delta there is NaN
# and no anomaly may be reported for them however large -9999 - -9999 would look.
CLOUD_YX = ((0, 0), (9, 3))
# Written as a literal on purpose, NOT read from sentinel._CLOUD_SENTINEL. This is the
# value the evalscript emits, and a test that built its fixture from the module constant
# would follow that constant if it ever drifted -- it would keep passing while the module
# masked a value the API never sends. Mutation testing caught exactly that: changing the
# constant to -999.0 left the whole file green. test_cloud_sentinel_matches_the_evalscript
# below pins the two together.
CLOUD_VALUE = -9999.0
# A legitimately NEGATIVE NDVI pixel: open water, bare rock and wet soil all read below
# zero, and they are valid observations rather than missing data. It is here because
# mutation testing found the masking could be widened to `array > 0.0` without any test
# objecting -- every other pixel in this fixture is positive, so that mutation masked the
# same set. Masking valid water as missing is a real failure mode for a tool asked where
# the ground changed, so one pixel now has to survive the conversion intact.
WATER_YX = (7, 7)
WATER_NDVI = -0.30


def _geotiff(values):
    """A single-band FLOAT32 GeoTIFF in EPSG:4326 with no declared nodata tag.

    No nodata tag is the point: that is what the Sentinel Hub response looks like, and it
    is why _tiff_to_ndvi_array has to convert -9999 itself instead of relying on
    masked=True to do it.
    """
    buf = io.BytesIO()
    with rasterio.open(
        buf, "w", driver="GTiff", height=SIZE, width=SIZE, count=1,
        dtype="float32", crs="EPSG:4326",
        transform=from_bounds(BBOX[0], BBOX[1], BBOX[2], BBOX[3], SIZE, SIZE),
    ) as dst:
        dst.write(values.astype("float32"), 1)
    return buf.getvalue()


def _scene(changed=False):
    values = np.full((SIZE, SIZE), BASE_NDVI, dtype="float32")
    if changed:
        values[CHANGED_YX] = CHANGED_NDVI
    values[WATER_YX] = WATER_NDVI
    for yx in CLOUD_YX:
        values[yx] = CLOUD_VALUE
    return _geotiff(values)


class _StubResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        return None


class _StubClient:
    """Hands back the queued GeoTIFF bodies in the order fetch_sentinel_ndvi asks."""

    def __init__(self, queue):
        self._queue = list(queue)
        self.calls = []

    def __call__(self, *args, **kwargs):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _StubResponse(self._queue.pop(0))


@pytest.fixture
def fetched(mocker):
    """(ndvi_before, ndvi_after) from the real code path, with only the network stubbed."""
    mocker.patch.object(sentinel.settings, "sentinel_hub_client_id", "test-client-id")
    mocker.patch.object(sentinel.settings, "sentinel_hub_client_secret", "test-secret")

    async def _token():
        return "test-token"

    mocker.patch.object(sentinel, "_get_token", _token)
    client = _StubClient([_scene(changed=False), _scene(changed=True)])
    mocker.patch.object(sentinel.httpx, "AsyncClient", client)
    return client


@pytest.mark.asyncio
async def test_returns_dataarrays_not_bytes(fetched):
    before, after = await sentinel.fetch_sentinel_ndvi(BBOX, "2026-05-01", "2026-09-01")
    for name, array in (("before", before), ("after", after)):
        assert not isinstance(array, (bytes, bytearray)), (
            f"{name} is still the raw response body. fetch_sentinel_ndvi documents "
            f"xarray DataArrays and temporal.py reads .values off them; bytes has no "
            f".values, so this is an AttributeError on the production path."
        )
        assert hasattr(array, "values") and hasattr(array, "rio")


@pytest.mark.asyncio
async def test_values_are_two_dimensional(fetched):
    """_compute_ndvi_sync unpacks exactly two indices and then indexes delta[y, x]."""
    before, after = await sentinel.fetch_sentinel_ndvi(BBOX, "2026-05-01", "2026-09-01")
    for array in (before, after):
        assert array.values.ndim == 2, (
            f"got {array.values.ndim} dimensions, dims={array.dims}. A leading band axis "
            f"breaks `ys, xs = np.where(mask)` in temporal.py, which unpacks two."
        )
        assert array.values.shape == (SIZE, SIZE)
        assert "band" not in array.dims


@pytest.mark.asyncio
async def test_transform_survives_the_conversion(fetched):
    """temporal.py turns pixel indices back into coordinates with .rio.transform()."""
    before, after = await sentinel.fetch_sentinel_ndvi(BBOX, "2026-05-01", "2026-09-01")
    for array in (before, after):
        transform = array.rio.transform()
        assert transform.c == pytest.approx(BBOX[0]), "west edge lost in conversion"
        assert transform.f == pytest.approx(BBOX[3]), "north edge lost in conversion"
        assert transform.a > 0 and transform.e < 0


@pytest.mark.asyncio
async def test_cloud_sentinel_becomes_nan(fetched):
    """-9999 left in the band would wreck np.nanmean and np.nanstd in temporal.py."""
    before, after = await sentinel.fetch_sentinel_ndvi(BBOX, "2026-05-01", "2026-09-01")
    for array in (before, after):
        values = array.values
        assert not (values == CLOUD_VALUE).any(), (
            "the evalscript's cloud sentinel is still in the band data. Left there it "
            "drags np.nanmean down and inflates np.nanstd, so genuine vegetation change "
            "stops clearing the sigma threshold."
        )
        for yx in CLOUD_YX:
            assert np.isnan(values[yx]), f"masked pixel {yx} is not NaN"
        assert np.isnan(values).sum() == len(CLOUD_YX), (
            "exactly the masked pixels should be NaN; anything else means the mask is "
            "wider than the scene classification asked for."
        )


@pytest.mark.asyncio
async def test_valid_negative_ndvi_is_not_masked(fetched):
    """Water and bare rock read below zero. They are observations, not missing data."""
    before, after = await sentinel.fetch_sentinel_ndvi(BBOX, "2026-05-01", "2026-09-01")
    for array in (before, after):
        value = float(array.values[WATER_YX])
        assert not np.isnan(value), (
            "a valid negative NDVI pixel was masked. The conversion must drop the "
            "evalscript's sentinel value only, not everything below zero: water, bare "
            "rock and wet soil are real readings, and masking them tells the search "
            "there is no data where there is simply no vegetation."
        )
        assert value == pytest.approx(WATER_NDVI, abs=1e-6)


def test_cloud_sentinel_matches_the_evalscript():
    """The constant is only right if it equals the literal the evalscript writes.

    These two live about sixty lines apart in the same file and nothing but this test
    couples them. Changing one without the other leaves the module masking a value the
    API never sends, while the sentinel it does send flows into np.nanmean as if it were
    an NDVI reading of -9999.
    """
    import inspect

    assert sentinel._CLOUD_SENTINEL == CLOUD_VALUE
    source = inspect.getsource(sentinel)
    assert "return [-9999]" in source, (
        "the evalscript no longer emits -9999 for masked pixels. Update "
        "_CLOUD_SENTINEL to match it, and this test with it."
    )


@pytest.mark.asyncio
async def test_result_flows_through_compute_ndvi_diff(fetched):
    """The end-to-end path analysis.py takes: fetch, then diff, then an anomaly."""
    before, after = await sentinel.fetch_sentinel_ndvi(BBOX, "2026-05-01", "2026-09-01")
    anomalies = await temporal.compute_ndvi_diff(before, after, sigma_threshold=1.5)

    assert len(anomalies) == 1, (
        f"expected the one changed pixel to be the only anomaly, got {len(anomalies)}"
    )
    found = anomalies[0]
    assert found.ndvi_before == pytest.approx(BASE_NDVI, abs=1e-6)
    assert found.ndvi_after == pytest.approx(CHANGED_NDVI, abs=1e-6)
    assert found.ndvi_delta == pytest.approx(CHANGED_NDVI - BASE_NDVI, abs=1e-6)

    # The coordinates must be the changed pixel's, computed the same way temporal.py does.
    transform = after.rio.transform()
    y, x = CHANGED_YX
    assert found.lon == pytest.approx(transform.c + x * transform.a)
    assert found.lat == pytest.approx(transform.f + y * transform.e)


def test_bytes_cannot_satisfy_the_consumer():
    """The old return value, pinned as a failure.

    This is what made the defect invisible: nothing in the suite ever handed the consumer
    what the function actually returned. If this stops raising, the tests above have
    stopped proving anything about why the conversion is needed.
    """
    with pytest.raises(AttributeError):
        temporal._compute_ndvi_sync(b"GeoTIFF bytes", b"GeoTIFF bytes", 1.5)
