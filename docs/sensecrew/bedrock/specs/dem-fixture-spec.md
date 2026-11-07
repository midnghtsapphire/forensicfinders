# Synthetic DEM fixture spec — 2320 (NEW-03, child of 2300 sensegame) (DESIGN DOC, 2026-11-04)
Owner: Bedrock pair. Status: **draft, not approved**. No code or commits. Procedural only; no real DEM, no case data, no PII.

## 1. Fixtures
Names follow Loam's GDD (v0.1 §4 M1–M3; v0.2/v0.3 §3 "1a's DEM pairs are `dem_synthetic_<seed>{a,b}.tif`"; `make dem` line). Lead ruling 2026-11-04: seed-only names, no mission token.
| key | file | mission | seed | epoch | use (Loam GDD) |
|---|---|---|---|---|---|
| `1001` | `fixtures/dem_synthetic_1001.tif` | M1 water-filling | 1001 | — | terrain for 4 segments + ROW |
| `1002a` | `fixtures/dem_synthetic_1002a.tif` | M2 pit or mound | 1002 | a (earlier) | baseline epoch: terrain only |
| `1002b` | `fixtures/dem_synthetic_1002b.tif` | M2 pit or mound | 1002 | b (later) | same terrain + seeded pits/mounds |
| `1003` | `fixtures/dem_synthetic_1003.tif` | M3 screen-survey-confirm | 1003 | — | terrain + procedural segment polygons |
All match `fixtures/*synthetic*` (rule 7).
**M2 epoch semantics (GDD node 1a "DEM difference > level of detection → pit/fill"; F1 ≥ 0.8 on seeded pits/mounds):** `a` is the earlier survey, `b` the later one; the player differences `b − a`. A pit is `b − a < 0`, a mound (fill) is `b − a > 0`. Both epochs share one terrain draw from seed 1002; `b` adds the features. Ground truth: `fixtures/dem_synthetic_1002_truth.json`. In v0, `b − a` is exactly 0 outside features. Inter-epoch survey noise / level of detection is physics owned by Waveform (L1) and stays PLACEHOLDER (no value invented here).

## 2. Raster contract
- Size 257 × 257 (2⁸+1, diamond-square native), pixel 1.0 m, extent 257 m × 257 m.
- dtype float32, little-endian; heights in metres, quantised to integer millimetres; range [1000.000, 1100.000] m.
- nodata −9999.0 declared (GDAL_NODATA tag) but no nodata pixels in v0.
- CRS: **synthetic local engineering frame** — GeoKeys: GTModelType=1 (projected), GTRasterType=1 (PixelIsArea), ProjectedCSType=32767 (user-defined), ProjLinearUnits=9001 (metre), GTCitation="SenseCrew synthetic local frame v0; not georeferenced". Origin (0, 257) top-left; ModelPixelScale (1,1,0); ModelTiepoint (0,0,0, 0,257,0). Never place on a real-world CRS.

## 3. Generator (pure integer, platform-independent)
1. `bg = numpy.random.PCG64(seed)`; draw only `bg.random_raw()` (uint64). We do **not** use `Generator.normal/uniform` (NumPy does not guarantee distribution streams across versions; the PCG64 bit stream is fixed by the algorithm). Offset uniform: `u = (raw >> 11) - 2**52` → integer in [−2⁵², 2⁵²).
2. Diamond-square (Fournier, Fussell & Carpenter 1982) on an int64 grid in mm: corners = 1_050_000 mm; amplitude a₀ = 20_000 mm; at step k amplitude `a_k = a₀ >> round(k·H)` with roughness H = 1 (integer shifts, halving per level). Displacement = `(u * a_k) >> 52` (int arithmetic; floor division defined). Diamond then square passes in row-major order; edge square points average 3 neighbours with `//` (floor).
3. Mission features (deterministic integer ops, positions drawn from the same stream after terrain):
   - Mission is fixed by seed in v0 (1001→M1, 1002→M2, 1003→M3); other seeds produce terrain only (used by the different-seed test).
   - 1001: none. 1003: one gentle ridge (linear ramp, ±5 m).
   - 1002: epoch a = terrain; epoch b = the same terrain + 3 pits (−0.5 m) and 3 mounds (+0.5 m), radius 3–6 px, integer cone profile. Feature draws come after the terrain draws, so epoch a never consumes them. Ground truth in `dem_synthetic_1002_truth.json` (sorted keys): `{"generator_version": "0", "mounds": [{"col", "depth_mm": 500, "radius_px", "row"}×3], "pits": [{… "depth_mm": -500 …}×3]}`; features do not overlap. The ±0.5 m depths are synthetic game parameters, not physics claims.
   - API: `generate(seed: int, epoch: str | None = None)`; `epoch` must be `"a"`/`"b"` for 1002 and `None` otherwise (`ValueError`). `FIXTURES: dict[str, str]` maps the keys above to paths.
4. Clip to [1_000_000, 1_100_000] mm; convert `(mm / 1000).astype(float32)`.
Order of RNG draws is part of the spec; any change bumps `generator_version` and all goldens.

## 4. Byte-identical GeoTIFF writer
**Ruling:** pure-Python stdlib writer (`struct`), ~150 lines, in `sensegame/tiffw.py` — **no GDAL/rasterio in the write path** (removes version drift). Layout: classic TIFF "II*\0", IFD at offset 8, tags in ascending order: 256,257 (W,H), 258=32, 259=1 (no compression), 262=1, 273 strip offset, 277=1, 278=257 (one strip), 279, 284=1, 339=3 (IEEE float), 33550, 33922, 34735 (GeoKeyDirectory), 34737 (GeoAscii), 42113 GDAL_NODATA "-9999". **No** 305 Software, 306 DateTime, 270 Description; no XMP; padding bytes zero. Pixel data written via `arr.astype('<f4').tobytes()`.
rasterio (BSD-3) and GDAL (MIT) are optional read-back cross-checks in tests only; if used, pin `rasterio==1.5.2` in `requirements-dev.txt`. Present on box: numpy 2.5.4, rasterio 1.5.2, tifffile 2026.10.15 (BSD-3, read-check alternative).

## 5. SHA-256 golden check
- `specs/tests/dem_golden_sha256.json` (sorted keys, LF): `{ "dem_synthetic_1001.tif": "<hex>", "dem_synthetic_1002a.tif": "<hex>", "dem_synthetic_1002b.tif": "<hex>", "dem_synthetic_1003.tif": "<hex>", "generator_version": "0" }`. Fixtures are **SHA-256 exact**: no float tolerance applies to fixture bytes.
- First values are recorded by Bedrock-D on the reviewed implementation, re-generated independently by Bedrock-N on a second machine/container, hashes must match, then LEDGER entry + "Bedrock-N APPROVE". Until then the file does not exist and `test_golden_sha256` fails (intended).
- `make fixtures-verify` regenerates to a temp dir and runs `sha256sum -c fixtures/SHA256SUMS`.
- Tests (`specs/tests/test_dem_fixture_golden.py`, failing now with ImportError): naming, M2 epoch pair (same terrain, b − a only at features), same-seed byte identity, different-seed difference, array contract, header (no DateTime/software strings, nodata present), golden hash, optional rasterio read-back.

## 6. CLI (rule 4: offline, no agents, no network)
```make
SEED ?= 1001
EPOCH ?=
dem:               ## make dem SEED=1001 | make dem SEED=1002 EPOCH=a   (GDD: make dem SEED=1001)
	python -m sensegame.dem --seed $(SEED) $(if $(EPOCH),--epoch $(EPOCH)) --out fixtures/dem_synthetic_$(SEED)$(EPOCH).tif
fixtures-all:
	python -m sensegame.dem --seed 1001 --out fixtures/dem_synthetic_1001.tif
	python -m sensegame.dem --seed 1002 --epoch a --out fixtures/dem_synthetic_1002a.tif
	python -m sensegame.dem --seed 1002 --epoch b --out fixtures/dem_synthetic_1002b.tif
	python -m sensegame.dem --seed 1003 --out fixtures/dem_synthetic_1003.tif
fixtures-verify:
	python -m sensegame.dem --verify fixtures/SHA256SUMS
test-dem:
	python -m pytest specs/tests/test_dem_fixture_golden.py
```
Ruling (lead, 2026-11-04): the pure-Python stdlib writer is authoritative for fixture bytes; rasterio/GDAL are read-back cross-checks only. GDD v0.2/v0.3 `make dem` comment "(rasterio/GDAL only)" is superseded by this ruling; Loam to update the GDD wording.
Dependencies: Python ≥3.11 stdlib + numpy (BSD-3). Nothing GPL, no Ultralytics.

## 7. Citations / licences
| ref | id | status |
|---|---|---|
| Fournier, A., Fussell, D., Carpenter, L. (1982) Computer rendering of stochastic models. *CACM* 25(6):371–384 | doi:10.1145/358523.358553 | VERIFIED (Crossref, 2026-11-04) |
| O'Neill, M.E. (2014) PCG: A family of simple fast space-efficient statistically good algorithms for random number generation. Harvey Mudd College tech. report HMC-CS-2014-0905 (5 Sep 2014) | no DOI; https://www.cs.hmc.edu/tr/hmc-cs-2014-0905.pdf | VERIFIED (HMC PDF title page, 2026-11-04) |
| NumPy (BSD-3), TIFF 6.0 spec (Adobe, 1992), OGC GeoTIFF 1.1 (OGC 19-008r4) | — | specs not re-checked this turn; licence of NumPy BSD-3 known |
