# multi_proxy — next step for private forensic pipeline

<!--
Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
When: 2026-11-04
Why:  The Sentinel-2 section told the reader to register a Copernicus Data Space account and
      install cdse-client. After the 2026-11-04 change to data_fetcher.fetch_sentinel2 that
      is no longer what the code does, and a README describing a credential flow the module
      does not use is worse than no README.
What: Rewrote the "Spectral (Sentinel-2 L2A)" section only. Every other section is
      untouched, and the original spectral section is kept verbatim at the bottom of this
      comment.
Notes: Two things in this file are still wrong and are deliberately NOT fixed here, because
      fixing them means designing something rather than describing it. (1) The import paths
      `sar.blue_ocean_sar.multi_proxy...` cannot resolve: sar/ is the directory every
      registry component runs from, not an importable package, and the directory is
      blue-ocean-sar with hyphens. (2) `run_one_tile` does not exist anywhere in the
      repository. Writing it means choosing how a tile is orchestrated end to end, which is
      a judgement about the cases, not a transcription job.

ORIGINAL SPECTRAL SECTION, kept verbatim:

### Spectral (Sentinel-2 L2A)
Register free at https://dataspace.copernicus.eu/
```bash
pip install cdse-client
```
Then use the client to download SWIR bands for ash/mineral proxies.
-->

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

No account, and no download. `data_fetcher.find_sentinel2` searches Element84 Earth Search
through `sar/geo_connectors/stac.py`, which is open, and `fetch_sentinel2` writes the
matching scenes and all their asset hrefs to a manifest:

```python
from data_fetcher import fetch_sentinel2
from loader import load_geotiff

manifest = fetch_sentinel2((-105.0, 40.0, -104.9, 40.1), ("2025-06-01", "2025-06-30"))
# None means no scene intersects that box in that window -- nothing else.
```

The pixels stay where they are. `loader.load_geotiff` reads a window straight from an
`https://` asset href through GDAL's vsicurl, so pulling whole products to disk would cost
gigabytes to produce bytes nothing reads:

```python
import json
scenes = json.load(open(manifest))["scenes"]
band, meta = load_geotiff(scenes[0]["assets"]["swir22"],
                          bbox=(-105.0, 40.0, -104.9, 40.1))
```

Every scene in the manifest carries its own `cloud_cover`, and no threshold is applied for
you: filter on a number you chose. Which bands serve an ash or mineral proxy is likewise
your call — the manifest hands you all of them.

### SAR / InSAR (Sentinel-1)
Same CDSE account. Download GRD or SLC for coherence stacks.
Long-term (years) coherence loss or multi-era DEM differencing is the strongest free signal for persistent soil disturbance (concrete burial settlement, incineration ash footprint).

## Run the engines
```python
from sar.blue_ocean_sar.multi_proxy import run_one_tile
out = run_one_tile(dem_path="data/dem/tile.tif", spectral_path="data/s2/stack.tif", synthetic=False)
```

This is the step. Point it at a real tile.
