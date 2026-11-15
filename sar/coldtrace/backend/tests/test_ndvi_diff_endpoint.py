# ════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-14
# Why:  GET /data/ndvi-diff fetched both NDVI composites and discarded them both, answering
#       {date_start, date_end, status: "computed"} while its docstring said it returns the
#       difference. Nothing in the suite noticed, because nothing had ever called the
#       endpoint: test_no_data.py reaches fetch_sentinel_ndvi directly, and both sentinel
#       test files stop at the service layer. The router was untested end to end, which is
#       exactly how a handler that drops its own results stays green for months.
# What: NEW FILE, purely additive. It drives the endpoint through FastAPI's TestClient with
#       only the network stubbed, over real GeoTIFF bytes, and checks the anomaly it gets
#       back against the GeoTIFF's own affine transform -- so the difference is tested for
#       being CORRECT, not merely present.
# What Worked: all four tests run and pass; component 700 goes 24 -> 28 passed.
# Notes: NOTHING IS COPIED HERE THAT ALREADY EXISTS. VISITING_AGENTS.md section 2 says to
#       extend existing tooling rather than clone it under a new name, and the suite already
#       had two GeoTIFF builders and a stub transport by the time this was written:
#         - _synthetic_geotiff_bytes comes from test_sentinel_dataarray.py (PR #46/#60),
#         - _StubClient/_StubResponse come from test_sentinel_arrays.py (PR #54, mine).
#       Both are imported rather than reimplemented. Importing underscore-prefixed names
#       across sibling test modules is not lovely, and the honest end state is ONE shared
#       conftest.py owning a GeoTIFF fixture and a stub transport. That means editing two
#       files which three different pull requests touched in the last week, so it is
#       reported as a follow-up instead of done here -- see the PR body.
#       The fixtures pass nodata=None deliberately. A real Sentinel Hub response declares NO
#       nodata tag, which is the whole reason the service masks -9999 explicitly; a fixture
#       that declared one would let masked=True do the work and quietly stop exercising that
#       masking. test_sentinel_dataarray.py's own fixtures declare -9999 as the tag, so this
#       is the one place that covers the tag-absent shape at endpoint level.
#       The anti-decoration property, per RVS-VERIFY-001 section 5.3: test_identical_scenes_
#       report_no_anomalies pins the opposite direction from the other three. Without it, a
#       handler that fabricated anomalies -- or simply returned every pixel -- would satisfy
#       every "the difference is there" assertion. One test says the difference appears when
#       there is one; another says it does not appear when there is none.
# ════════════════════════════════════════════════════════════════════════════════════════
"""GET /data/ndvi-diff must return the difference, not merely claim to have computed it."""
from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from coldtrace.backend.errors import NoDataError
from coldtrace.backend.main import app
from coldtrace.backend.services import sentinel

# Reused, not reimplemented -- see the Notes box above.
from .test_sentinel_arrays import _StubClient
from .test_sentinel_dataarray import _synthetic_geotiff_bytes

ENDPOINT = "/data/ndvi-diff"
SIZE = 8
BASE_NDVI = 0.50
CHANGED_NDVI = 0.90
CHANGED_YX = (2, 5)
CLOUD_VALUE = -9999.0
CLOUD_YX = (0, 0)
QUERY = {
    "west": -105.05, "south": 39.97, "east": -104.97, "north": 40.05,
    "date_start": "2026-05-01", "date_end": "2026-09-01",
}


def _scene(changed: bool) -> bytes:
    """One synthetic NDVI scene, with no declared nodata tag (as the real API sends)."""
    values = np.full((SIZE, SIZE), BASE_NDVI, dtype="float32")
    values[CLOUD_YX] = CLOUD_VALUE
    if changed:
        values[CHANGED_YX] = CHANGED_NDVI
    return _synthetic_geotiff_bytes(values, nodata=None)


@pytest.fixture
def stubbed_sentinel(mocker):
    """Only the network is stubbed. The parse, the diff and the router all run for real."""

    def _install(before: bytes, after: bytes):
        mocker.patch.object(sentinel.settings, "sentinel_hub_client_id", "test-client-id")
        mocker.patch.object(sentinel.settings, "sentinel_hub_client_secret", "test-secret")

        async def _token():
            return "test-token"

        mocker.patch.object(sentinel, "_get_token", _token)
        mocker.patch.object(sentinel.httpx, "AsyncClient", _StubClient([before, after]))
        return TestClient(app)

    return _install


def test_the_difference_is_returned_and_is_correct(stubbed_sentinel):
    """The one changed pixel must come back, at the coordinates the GeoTIFF implies."""
    client = stubbed_sentinel(_scene(changed=False), _scene(changed=True))
    response = client.get(ENDPOINT, params=QUERY)
    assert response.status_code == 200, response.text
    payload = response.json()

    anomalies = payload.get("anomalies")
    assert anomalies is not None, (
        "the response has no 'anomalies' key. This endpoint fetched both NDVI composites "
        "and discarded them while reporting status 'computed'; if that has come back, it "
        "is answering 200 and silence to a question about where the ground changed."
    )
    assert len(anomalies) == 1, f"expected the single changed pixel, got {len(anomalies)}"

    found = anomalies[0]
    assert found["ndvi_before"] == pytest.approx(BASE_NDVI, abs=1e-6)
    assert found["ndvi_after"] == pytest.approx(CHANGED_NDVI, abs=1e-6)
    assert found["ndvi_delta"] == pytest.approx(CHANGED_NDVI - BASE_NDVI, abs=1e-6)
    assert found["sigma"] > 1.5, "an anomaly below the threshold should not be reported"

    # Coordinates checked against the fixture's own georeferencing, computed the way
    # temporal.py does, so a transposed or mislocated anomaly fails rather than passes.
    transform = sentinel.geotiff_bytes_to_ndvi_dataarray(_scene(changed=True)).rio.transform()
    y, x = CHANGED_YX
    assert found["lon"] == pytest.approx(transform.c + x * transform.a)
    assert found["lat"] == pytest.approx(transform.f + y * transform.e)


def test_identical_scenes_report_no_anomalies(stubbed_sentinel):
    """The other direction. Without this, fabricated anomalies would pass every test above.

    Two identical scenes differ by nothing, so the delta field is flat, its standard
    deviation is zero, and the honest answer is an empty list with a 200 -- not an error
    and not a list of every pixel.
    """
    client = stubbed_sentinel(_scene(changed=False), _scene(changed=False))
    response = client.get(ENDPOINT, params=QUERY)
    assert response.status_code == 200, response.text
    assert response.json()["anomalies"] == [], (
        "identical scenes produced anomalies. Either the diff is comparing something "
        "other than the two scenes, or anomalies are being invented."
    )


def test_the_existing_response_keys_are_untouched(stubbed_sentinel):
    """The fix is additive: any client already reading these three keys must still work."""
    client = stubbed_sentinel(_scene(changed=False), _scene(changed=True))
    payload = client.get(ENDPOINT, params=QUERY).json()
    assert payload["date_start"] == QUERY["date_start"]
    assert payload["date_end"] == QUERY["date_end"]
    assert payload["status"] == "computed", (
        "'computed' is now a claim the endpoint can actually back up; it should not have "
        "been renamed or dropped while making it true."
    )


def test_missing_credentials_still_answers_424(mocker):
    """The no-data contract is unchanged: this path returns before any difference exists."""
    mocker.patch.object(sentinel.settings, "sentinel_hub_client_id", "")
    response = TestClient(app, raise_server_exceptions=False).get(ENDPOINT, params=QUERY)
    assert response.status_code == 424, response.text
    assert response.json()["status"] == "no_data"
    assert NoDataError is not None  # the error type this path depends on still exists
