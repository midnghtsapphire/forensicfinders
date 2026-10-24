# multi_proxy — next step for private forensic pipeline

## Get data (free)

### DEM (USGS 3DEP)
```bash
pip install seamless-3dep
python -c "
from sar.blue_ocean_sar.multi_proxy.data_fetcher import fetch_dem_3dep
path = fetch_dem_3dep((-105.0, 40.0, -104.9, 40.1))
print(path)
"
```
Or manual: https://apps.nationalmap.gov/downloader/ → Elevation Products (3DEP).

### Spectral (Sentinel-2 L2A)
Register free at https://dataspace.copernicus.eu/
```bash
pip install cdse-client
```
Then use the client to download SWIR bands for ash/mineral proxies.

### SAR / InSAR (Sentinel-1)
Same CDSE account. Download GRD or SLC for coherence stacks.
Long-term (years) coherence loss or multi-era DEM differencing is the strongest free signal for persistent soil disturbance (concrete burial settlement, incineration ash footprint).

## Run the engines
```python
from sar.blue_ocean_sar.multi_proxy import run_one_tile
out = run_one_tile(dem_path="data/dem/tile.tif", spectral_path="data/s2/stack.tif", synthetic=False)
```

This is the step. Point it at a real tile.
