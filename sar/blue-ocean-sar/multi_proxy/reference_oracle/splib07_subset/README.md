# USGS Spectral Library v7 (splib07) — reference-oracle PD endmember subset

<!--
Who:  Sense-Quartz (Quartz-N / Quartz-D, Grok Bot) for Audrey Evans
When: 2026-11-04 (America/Denver)
Why:  Offline reference-oracle endmembers for constrained_nnls_unmix / spectral_angle (registry 2360).
Licence (our code/docs): UNLICENSED (private repo; licence pending Audrey)
Licence (this data): USGS Spectral Library v7 is public domain (US federal government work).
-->

## Status

**Real USGS public-domain spectra** (reference oracle, not a seed fixture), not placeholders and not case data.

- Library: USGS Spectral Library Version 7 (`splib07`)
- Report DOI: https://doi.org/10.3133/ds1035
- Data DOI: https://doi.org/10.5066/F7RR1WDJ
- Lab page: https://www.usgs.gov/labs/spectroscopy-lab/science/spectral-library
- ScienceBase ASCII item: https://www.sciencebase.gov/catalog/item/586e8c88e4b0f5ce109fccae
- Source package used here: `ASCIIdata_splib07b_cvAVIRISc2014.zip` (spectra convolved to AVIRIS-Classic 2014; 224 channels)

**LUCAS is NOT included.** This directory contains only a tiny USGS PD mineral / dry-grass subset for training and golden tests. Do not confuse with `*synthetic*` mixture cubes (those stay under `fixtures/*synthetic*` only).

## Wavelengths and reflectance

| Item | Value |
|------|--------|
| Units | micrometres (µm) |
| Sensor grid | AVIRIS-Classic 2014 (USGS convolution; no further resampling by us) |
| Full channels | 224 |
| Kept channels | 196 (water-vapor windows 1.35–1.45 µm and 1.80–1.95 µm dropped) |
| Reflectance | absolute reflectance (AREF), unitless, typically `[0, 1]` |
| Deleted-band sentinel | `-1.23e+34` (SPECPR); none present in this AVIRIS subset after filtering |

## Endmembers (9)

| Short name | USGS ASCII file | Chapter |
|------------|-----------------|---------|
| `quartz` | `s07_AV14_Quartz_GDS74_Sand_Ottawa_BECKc_AREF.txt` | Minerals |
| `kaolinite` | `s07_AV14_Kaolinite_KGa-1_(wxl)_BECKb_AREF.txt` | Minerals |
| `montmorillonite` | `s07_AV14_Montmorillonite_SWy-1_BECKb_AREF.txt` | Minerals |
| `calcite` | `s07_AV14_Calcite_HS48.3B_BECKa_AREF.txt` | Minerals |
| `goethite` | `s07_AV14_Goethite_WS222_Medium_Gr._BECKa_AREF.txt` | Minerals |
| `hematite` | `s07_AV14_Hematite_GDS27_BECKa_AREF.txt` | Minerals |
| `gypsum` | `s07_AV14_Gypsum_SU2202_BECKa_AREF.txt` | Minerals |
| `illite` | `s07_AV14_Illite_GDS4_Marblehead_BECKb_AREF.txt` | Minerals |
| `dry_grass` | `s07_AV14_Grass_Golden_Dry_GDS480_ASDFRa_AREF.txt` | Vegetation |

Chosen for disturbed-soil / mineral-mapping training relevance (silicates, clays, carbonate, Fe-oxides, evaporite, NPV vegetation).

## File list

| Path | Role |
|------|------|
| `ascii_src/` | Verbatim USGS single-column ASCII (title line + 224 floats) + wavelength/FWHM files |
| `wavelengths_um.csv` | Full 224-band grid with `kept` flag |
| `endmembers_reflectance.csv` | Kept-grid table: `wavelength_um,<names…>` |
| `endmembers_aviris2014.npz` | Compressed arrays for the deterministic loader |
| `manifest.json` | Citation, band selection, catalogue |
| `README.md` | This file |

## How to regenerate

Offline after download (network only for the one USGS zip; tests never need the network):

```bash
# ~4.3 MiB — do NOT vendor the multi-GB SPECPR archive
curl -L -o ASCIIdata_splib07b_cvAVIRISc2014.zip \
  'https://www.sciencebase.gov/catalog/file/get/586e8c88e4b0f5ce109fccae?name=ASCIIdata_splib07b_cvAVIRISc2014.zip'
unzip ASCIIdata_splib07b_cvAVIRISc2014.zip
# Copy the nine AREF columns + wavelength/FWHM files into ascii_src/, then rebuild
# CSV/NPZ/manifest with the same band mask documented above (see Sense-Quartz task B notes).
```

Loader API (package-relative):

```python
from multi_proxy.splib07_endmembers import load_endmembers, wavelength_grid_um
em = load_endmembers(["kaolinite", "hematite"])  # dict[str, (B,)]
wl = wavelength_grid_um()  # (B,) micrometres
```

## Component / registry

- Registry id: **2360** (Verity: NEW-22 → 2360)
- Registry id: **2360** (pending Verity collision check — do not edit `registry.json` until Verity confirms)

## Citation

Kokaly, R.F., Clark, R.N., Swayze, G.A., Livo, K.E., Hoefen, T.M., Pearson, N.C., Wise, R.A., Benzel, W.M., Lowers, H.A., Driscoll, R.L., and Klein, A.J., 2017, USGS Spectral Library Version 7: U.S. Geological Survey Data Series 1035, 61 p., https://doi.org/10.3133/ds1035.

Kokaly, R.F., Clark, R.N., Swayze, G.A., Livo, K.E., Hoefen, T.M., Pearson, N.C., Wise, R.A., Benzel, W.M., Lowers, H.A., Driscoll, R.L., and Klein, A.J., 2017, USGS Spectral Library Version 7 Data: U.S. Geological Survey data release, https://doi.org/10.5066/F7RR1WDJ.
