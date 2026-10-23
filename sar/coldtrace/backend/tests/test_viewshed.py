import pytest
from pathlib import Path
from coldtrace.backend.services import viewshed


@pytest.mark.asyncio
async def test_compute_viewshed_production_path(mocker):
    mock_run = mocker.patch("coldtrace.backend.services.viewshed._run_whitebox_viewshed")
    mock_run.return_value = {"type": "FeatureCollection", "features": []}
    result = await viewshed.compute_viewshed(dem_path="fake/path", observer_lon=1.0, observer_lat=2.0,
                                             observer_height=2.0, max_distance=100.0)
    assert result == {"type": "FeatureCollection", "features": []}
    mock_run.assert_called_once_with(dem_path=Path("fake/path"), observer_lon=1.0, observer_lat=2.0,
                                     observer_height=2.0, max_distance=100.0)


@pytest.mark.asyncio
async def test_no_demo_fallback_when_production_fails(mocker):
    mocker.patch("coldtrace.backend.services.viewshed._run_whitebox_viewshed", side_effect=RuntimeError("no whitebox"))
    with pytest.raises(RuntimeError):
        await viewshed.compute_viewshed(dem_path="fake", observer_lon=0, observer_lat=0)
    assert not hasattr(viewshed, "_demo_viewshed")
