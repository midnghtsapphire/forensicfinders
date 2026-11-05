# splib07 PD endmember fixture (NEW-22 / registry 2360)

**Licence (our docs/code):** UNLICENSED (private repo; licence pending Audrey).
**Data:** USGS Spectral Library v7 — public domain. Cite https://doi.org/10.3133/ds1035 and https://www.usgs.gov/labs/spectroscopy-lab/science/spectral-library.

Shipped path: `sar/blue-ocean-sar/multi_proxy/fixtures/splib07_subset/` (real AVIRIS-2014-convolved AREF spectra; not placeholders; LUCAS not included).

Loader: `sar/blue-ocean-sar/multi_proxy/splib07_endmembers.py` → `load_endmembers(names=None) -> dict[str, np.ndarray]`.

Wavelengths: micrometres (µm) on the USGS AVIRIS-Classic 2014 grid; water windows 1.35–1.45 µm and 1.80–1.95 µm dropped (196 bands kept of 224). No runtime resampling.

Do **not** edit `registry.json` until Verity confirms id **2360**.

See fixture `README.md` for regeneration and full citation.
