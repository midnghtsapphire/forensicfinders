import pytest
from fastapi.testclient import TestClient
from coldtrace.backend.errors import NoDataError
from coldtrace.backend.main import app
from coldtrace.backend.services import heatmap, opentopo, sentinel, temporal, viewshed


def test_no_demo_functions_anywhere():
    for m in (heatmap, opentopo, sentinel, temporal, viewshed):
        assert not [n for n in dir(m) if n.startswith("_demo")], m.__name__


@pytest.mark.asyncio
async def test_missing_opentopo_key_is_no_data(mocker):
    mocker.patch.object(opentopo.settings, "opentopography_api_key", "")
    with pytest.raises(NoDataError):
        await opentopo.fetch_dem((0.0, 0.0, 0.01, 0.01))


@pytest.mark.asyncio
async def test_missing_sentinel_creds_is_no_data(mocker):
    mocker.patch.object(sentinel.settings, "sentinel_hub_client_id", "")
    with pytest.raises(NoDataError):
        await sentinel.fetch_sentinel_ndvi((0.0, 0.0, 0.01, 0.01), "2020-01-01", "2020-02-01")


@pytest.mark.asyncio
async def test_heatmap_with_no_inputs_is_empty_not_synthetic():
    r = await heatmap.synthesize_heatmap(None, [], [], (0.0, 0.0))
    assert r == {"type": "FeatureCollection", "features": []}


def test_no_data_handler_returns_424():
    @app.get("/__nodata_probe")
    async def probe():
        raise NoDataError("nothing here")
    r = TestClient(app).get("/__nodata_probe")
    assert r.status_code == 424 and r.json() == {"status": "no_data", "reason": "nothing here"}
