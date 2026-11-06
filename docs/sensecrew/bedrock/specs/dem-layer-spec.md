# DEM-derived grid layer — 2380 (proposed, child of 2300 sensegame) (DESIGN DOC, 2026-11-05)

Owner: Bedrock pair (Bedrock-D / Bedrock-N). Status: **draft design**. No implementation in this PR. No `sensegame.tile`, no `run_one_tile`, no orchestrator, no edits to CleanScorer.

This is Bedrock's answer on [Discussion #44](https://github.com/midnghtsapphire/forensicfinders/discussions/44): Bedrock owns the synthetic DEM (2320) and the science-core API, and owns this DEM→layer step as a spec before any tile code. Fusion consumes the layer. POA changes only through `CleanScorer.update`. `M1_W_KM` stays `None`.

Licence: UNLICENSED (private repo; licence pending Audrey). Synthetic inputs only.

## 1. Registry

Proposed id **2380** `dem_layer`, parent **2300** `sensegame`. Not written into `sar/registry.json` (PR #39 shipped specs without a registry edit; this PR does the same).

| id | name | where it is claimed |
|---|---|---|
| 2300 | sensegame parent | PR #41 registry |
| 2310 | CleanScorer | PR #41 registry |
| 2320 | synthetic DEM | PR #41 registry; `docs/sensecrew/bedrock/specs/dem-fixture-spec.md` |
| 2330 | NEW-10 sweep-width table | GDD v0.4; PR #11. **Not free.** Unused in `sar/registry.json` on main and on PR #41 / #42, and still not available for this layer |
| 2331 | NEW-11 sweep adapter | GDD v0.4; PR #11 |
| 2340 | NEW-12 harness | GDD v0.4; PR #11 |
| 2350 | insect-trace-add-sim | PR #27 |
| 2360 | NEW-22 mineral-spectral-unmix | PR #33 / #34 |
| 2370 | NEW-13 fusion parent, provisional | PR #18; GDD v0.4 |
| 2371 | fusion combine, provisional | PR #42 `combine.py` |
| **2380** | **dem_layer (this spec)** | **unused** in `sar/registry.json` (main, PR #41 `dafed87`, PR #42 `ad83cba`) and not in the GDD v0.4 final list |

2380 is the next free decade after that list. Strata / Verity can renumber before code lands. Do not reuse 2330.

## 2. What this layer is

A pure function from one synthetic elevation grid to one hint grid of the same shape. Kinds in v0: `slope` and `roughness`. No aspect, no hillshade, no hydrology.

Inputs are an elevation array already produced by `dem.generate(seed, epoch)` (2320) or an array the caller built from a `fixtures/*synthetic*` file. `derive` does not open files, does not call the generator, and does not draw random numbers. The DEM seed is provenance only.

Cells are integer indices `(r, c)` with `r` down the array and `c` across it. Fusion's site id for that cell is `cell_<r>_<c>` (0-based), assigned by Fusion, not by this layer. Spacing is `cell_m` in fixture-local metres. 2320 fixtures use `cell_m = 1.0`. There is no geographic CRS on the layer.

## 3. API

Module, when code exists: `sar/sensegame/dem_layer.py`. This PR does not add that file.

```python
REGISTRY_ID = 2380

REJECTED_GEO_KEYS = frozenset({
    "lat", "lon", "lng", "long", "latitude", "longitude",
    "address", "addr", "geom", "geometry", "wkt", "coordinates",
})  # same set as Fusion combine.py GEO_KEYS, PR #42 @ ad83cba

class LayerError(ValueError): ...

@dataclass(frozen=True)
class Layer:
    kind: str                 # "slope" | "roughness"
    values: ndarray           # shape == dem.shape, dtype "<f8", C-contiguous, writeable False
    cell_m: float
    units: str                # "m/m" | "m"
    degenerate: bool
    excluded: bool            # v0: always equal to degenerate
    provenance: dict          # see §7; never affects values
    def to_json(self) -> str: ...   # §8, includes one trailing "\n"

def derive(dem, *, kind: str, cell_m: float, provenance: Mapping | None = None) -> Layer:
    ...
```

`dem` must be array-like, rank 2, both axes ≥ 3, every sample finite and not equal to the 2320 nodata sentinel `-9999.0`. Cast with `float()` through IEEE-754 binary64 before any arithmetic. `cell_m` must be finite and `> 0`. `kind` must be `"slope"` or `"roughness"`. Anything else raises `LayerError` before a layer is returned.

`provenance` is optional. `None` and `{}` are the same. Allowed keys only: `seed` (int, not bool, `≥ 0`), `epoch` (`None`, `"a"`, or `"b"`), `generator_version` (str, no whitespace), `fixture` (relative path). Any other key raises `LayerError`. A key whose lower-case form is in `REJECTED_GEO_KEYS` raises `LayerError` and names the geographic field. `derive` does not read `fixture`; the string is metadata. It must match `fixtures/<name>` where `<name>` matches `*synthetic*`, must not be absolute, must not contain `..`, and must not contain a path part `case`, `hfmr`, `evidence`, `realdata`, or `dossier`.

The returned array is little-endian float64 (`dtype.str == "<f8"`), C-contiguous, and not writeable.

## 4. Slope — Horn rise/run

**Unit: metre per metre (dimensionless rise/run), not degrees.**

Horn (1981, §IX) defines the gradient components `p` and `q` as first partial derivatives of elevation, estimated with a 3×3 weighted central difference, and §XVI defines slope along a step as change in elevation divided by the length of the step. The steepest-ascent slope is therefore `sqrt(p² + q²)`, in the same units as `p` and `q`. Degrees would be `atan` of that magnitude: a further nonlinear map, and a libm call this contract does not need. Rise/run is the quantity Fusion should see as `raw`. Positive scale does not change Fusion's robust z; a nonlinear degree map would.

Square cells: `Δx = Δy = cell_m`. At cell `(r, c)`, with out-of-range indices replaced by the nearest in-range index (edge replication):

```text
z_nw z_n  z_ne
z_w  z_c  z_e
z_sw z_s  z_se
```

`z_n` is the sample toward decreasing row index (the top of the array). That matches the 2320 GeoTIFF, whose origin is the top-left corner. Horn's `q` is positive when elevation increases toward that side (his south-to-north axis on a north-up map). v0 stores only the magnitude, so the sign of `q` is not a field. It is still pinned, because `p*p + q*q` is evaluated in a fixed order:

```text
east  = (z_ne + (2.0 * z_e)) + z_se
west  = (z_nw + (2.0 * z_w)) + z_sw
p     = (east - west) / (8.0 * cell_m)
north = (z_ne + (2.0 * z_n)) + z_nw
south = (z_se + (2.0 * z_s)) + z_sw
q     = (north - south) / (8.0 * cell_m)
slope = math.sqrt((p * p) + (q * q))
```

Parentheses are significant. Use `math.sqrt`, not a hypot helper and not `numpy.gradient`.

Horn's sample program in that paper writes a brightness grid one row and one column smaller than the elevation grid. v0 does not do that: Fusion's `values` must have the DEM's shape (§6). The one-pixel border uses the same weights on a neighbourhood completed by edge replication. Replication is a same-shape rule of this spec. On a constant grid it changes nothing (every slope is 0). On a plane it biases the border; the goldens below include that bias on purpose.

Worked slope, `cell_m = 2`, every row `[1000.0, 1000.5, 1001.0]` (a rise of 0.5 m per column, run 2 m, true gradient 0.25):

| cells | slope |
|---|---|
| both edge columns | 0.125 |
| centre column | 0.25 |

Centre check: `((1001+2·1001+1001) − (1000+2·1000+1000)) / 16 = 4/16 = 0.25`, `q = 0`. Edge check: the replicated side collapses one column, so the difference is `2/16 = 0.125`. These values are dyadic and exact in binary64.

A 3×4 grid of the same ramp is `[0.125, 0.25, 0.25, 0.125]` on every row. Doubling `cell_m` to 4 halves every slope (`0.0625` on the edges, `0.125` inside).

## 5. Roughness — local RMS height

**Unit: metres.** Population RMS of the same clamped 3×3 elevations about their mean. The window is the Horn neighbourhood, so the horizontal scale is `3 * cell_m` and is reported as `cell_m` rather than folded into the number. Shepard et al. (2001) show that topographic roughness parameters are scale-dependent; v0 therefore pins the window and records `cell_m` instead of emitting a scale-free index. The 3×3 population divisor is this contract, not a formula quoted from that paper.

Window order is row-major from the north row to the south row, west to east, clamp as in §4. Nine samples, duplicates allowed when the clamp repeats a pixel:

```text
m_sum = z0; then m_sum = m_sum + z1; … through z8
m     = m_sum / 9.0
acc   = 0.0; for each zi in that same order: d = zi - m; acc = acc + (d * d)
roughness = math.sqrt(acc / 9.0)
```

`cell_m` must still be valid, and it does not enter the arithmetic. Two calls that differ only in `cell_m` have identical roughness bytes and different JSON.

Worked roughness on the §4 ramp (`cell_m` irrelevant):

| cells | value | closed form |
|---|---|---|
| edge columns | 0.23570226039551584 | `sqrt(1/18)` |
| centre column | 0.408248290463863 | `sqrt(1/6)` |

Centre: three copies each of 1000, 1000.5, 1001; mean 1000.5; mean square deviation `1/6`. Edge column: six 1000 and three 1000.5; mean square deviation `1/18`. Both match binary64 `math.sqrt`.

## 6. MAD, flat terrain, and Fusion

Degeneracy uses the same MAD as Fusion `robust_z` in `sar/sensegame/fusion/combine.py` (PR #42 @ `ad83cba`). That function is the behaviour to match. This layer does not import it (PR #42 is unmerged; Bedrock does not take a Fusion dependency to compute a flag).

```text
xs  = finite samples in row-major order
if len(xs) < 2: degenerate
med = statistics.median(xs)          # even n: average of the two central values
mad = statistics.median([abs(x - med) for x in xs])
degenerate = (mad == 0.0)            # exact, no tolerance
excluded   = degenerate              # v0
```

`statistics.median` is the function `combine.py` imports. The comparison is `== 0.0`, as in `robust_z`. Do not add an epsilon.

Rousseeuw & Croux (1993) write `MAD_n = 1.4826 med |x_i − med x|` and cite Hampel (1974) for the influence function of this scale. Fusion multiplies by `MAD_K = 1.4826` when it builds a robust z. This layer does not. `1.4826 * 0 = 0`, so the constant cannot change the flag, and the layer does not emit a z-score.

**Flat terrain.** Every elevation equal → every Horn difference is 0 → slope grid is all 0 → roughness grid is all 0 → MAD is 0 → `degenerate` and `excluded` are true. The zeros are the computed rise/run and the computed RMS, not a fill that replaces some other grid. JSON keeps those zeros under `values`. It has no `normalised` array and no `contribution` array.

**Not only the all-zero grid.** MAD is also 0 when at least half the samples equal the median, even if other cells differ. Fusion's `mad == 0.0` branch then sets normalised values to `None`, sets `degenerate` and `excluded`, and **keeps raw**. It does not write a z of 0. The 3×3 ramp in §4 is that case:

- six cells at 0.125, three at 0.25
- median = 0.125 (5th of 9)
- absolute deviations: 0 (six times), 0.125 (three times)
- MAD = 0
- `degenerate` true, `excluded` true, values unchanged (they are not all 0)

The 3×4 ramp splits 6 and 6. `statistics.median` averages the two central values: `(0.125 + 0.25) / 2 = 0.1875`. Every absolute deviation is 0.0625, so MAD is 0.0625 and the layer is **not** degenerate. An implementation that flags "any repeated value", or that flags only the all-zero grid, fails these two goldens.

A varied 3×3, `cell_m = 1`, elevations `[[0, 0, 0], [0, 1, 0], [0, 0, 2]]`, slope grid:

```text
[[0.1767766952966369, 0.25,               0.1767766952966369],
 [0.25,               0.3535533905932738, 0.75              ],
 [0.1767766952966369, 0.75,               0.8838834764831844]]
```

Centre: `p = 0.25`, `q = -0.25`, `sqrt(0.125) = 0.3535533905932738`. Median of the nine slopes is 0.25. MAD is `abs(0.1767766952966369 - 0.25) = 0.0732233047033631` ≠ 0, so `degenerate` is false.

v0 has no nodata holes (2320 fixtures have none, and `-9999.0` is rejected), so every accepted grid has at least 9 finite samples. The `len(xs) < 2` branch is still required so the flag stays aligned with `robust_z` if a later revision allows holes.

What Fusion does with the flag, quoted from behaviour rather than restated loosely: `robust_z` returns `([None] * n, True)` when MAD is 0; `combine` sets `meta["layers"][name]["degenerate"]` and `["excluded"]` to that flag; raw is the original sample (`5.0` in `test_flat_layer_flagged_not_zeroed`); `normalised` is `None`; `contribution` is `None`. This layer's job is to set the same two flags and to leave `values` equal to the computed grid. Weight and `direction` (`higher` / `lower`) belong to the Fusion config. This spec does not choose them.

## 7. Provenance and determinism

`derive` is a pure function of `(dem, kind, cell_m)` plus a provenance dict that is stored and not read by the arithmetic. Same array, same kind, same `cell_m` → identical `<f8` bytes, whether or not the provenance dict differs. Same provenance as well → identical `to_json()` text.

The seed enters only as that dict, copied from the `dem.generate(seed, epoch)` call the caller already made. Same seed and epoch produce the same DEM under 2320, and therefore the same layer bytes. This module must not reseed and must not call `numpy.random`.

Byte contract: `np.ascontiguousarray(values, dtype="<f8").tobytes()` on the returned array (already that dtype and layout). JSON is a second, text contract (§8). Both are free of timestamps, host names, and process ids.

## 8. JSON

Same encoder as Fusion `run.py` `_fmt` (PR #42 @ `ad83cba`), local to this module, not an import of Fusion:

- objects: keys sorted, `json.dumps` on each key, no spaces
- arrays: order preserved
- Python `float`: `"%.17g" % float(x)` (cast numpy scalars with `float` first)
- bool and null: `json.dumps`
- int and str: `json.dumps`
- one trailing `\n`
- non-finite floats are a `LayerError` (they are already rejected on input)

`%.17g` matches Fusion's text. It is not required to round-trip through `json.loads` to the same binary64. The bit contract remains the little-endian grid. `1.0` is written as `1`, `2.0` as `2`, `0.0` as `0`.

Object fields: `cell_m`, `degenerate`, `excluded`, `kind`, `provenance`, `registry_id`, `shape` (`[rows, cols]`), `units`, `values` (row-major nested arrays). No `normalised`, no `contribution`, no geographic field.

Golden text for the §4 3×3 ramp, `kind="slope"`, `cell_m=2`, empty provenance (newline terminated):

```text
{"cell_m":2,"degenerate":true,"excluded":true,"kind":"slope","provenance":{},"registry_id":2380,"shape":[3,3],"units":"m/m","values":[[0.125,0.25,0.125],[0.125,0.25,0.125],[0.125,0.25,0.125]]}
```

Flat 4×4 elevation `1000.0`, `cell_m=1`, `kind="slope"`:

```text
{"cell_m":1,"degenerate":true,"excluded":true,"kind":"slope","provenance":{},"registry_id":2380,"shape":[4,4],"units":"m/m","values":[[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]}
```

## 9. Integration boundary

- Fusion may copy `values` into a combine layer and may trust `degenerate` / `excluded`. If it ignores the flags and runs `robust_z` itself, the MAD rule in §6 is the same rule, so a flat or half-constant grid is excluded there too.
- This layer is a hint. It does not read or write POA. It does not call `CleanScorer.update`, `pos`, `optimal`, or `pod`. It does not define `M1_W_KM`. Sweep width stays uncited. No numeric W is stated in this document.
- `sensegame.tile.run_one_tile` is out of scope. Discussion #44 Option A may call `derive` later, only after the gates on that thread (this spec signed, #41 and #42 decided, Verity's conditions). This PR does not add the tile module.
- Procedural Fusion scenes (`thermal`, `ndvi_change`, `sar_coherence` from `fusion/synth.py`) are not DEM layers and are not relabelled here.

## 10. Offline entry points (sketch only)

Not added to the Makefile, and no CLI module is added, in this PR.

```make
SEED ?= 1001
EPOCH ?=
KIND ?= slope
CELL_M ?= 1
dem-layer:
	python -m sensegame.dem_layer --seed $(SEED) $(if $(EPOCH),--epoch $(EPOCH)) \
	    --kind $(KIND) --cell-m $(CELL_M) \
	    --out out/dem-layer/$(KIND)_$(SEED)$(EPOCH).json
test-dem-layer:
	PYTHONPATH=sar python -m pytest docs/sensecrew/bedrock/specs/tests/test_dem_layer_golden.py
```

The CLI, when it exists, will call `dem.generate` and then `derive`, and write `to_json()` bytes. It rejects geographic keys and any path that is not `fixtures/*synthetic*`. It does not fetch a tile and does not read `data/dem/`.

Dependencies for a future implementation: Python ≥ 3.11 stdlib (`math`, `statistics`, `json`) and numpy (BSD-3) for the array container. No GDAL, no rasterio, no GPL library, no Ultralytics, no TerraTorch, no TerraMesh.

## 11. Tests

`docs/sensecrew/bedrock/specs/tests/test_dem_layer_golden.py` imports `sensegame.dem_layer` at collection time. Until that module exists the file fails with `ImportError`. That is the intended state of this PR. The assertions cover shape and dtype, slope units and the Horn goldens, roughness units and the RMS goldens, flat MAD with the flag set, the non-zero ramp whose MAD is still 0, the 3×4 even-median case whose MAD is 0.0625, the varied grid whose MAD is not 0, byte identity, same-seed identity through `dem.generate`, provenance not entering the arithmetic, and rejection of geographic keys.

Tolerances: the dyadic slope goldens and the two RMS closed forms are exact binary64 equalities. No new tolerance band is introduced. 2310's `1e-12` / `1e-9` bands are not used here.

## 12. Citations

Verified against Crossref on 2026-11-05.

| ref | id | use in this spec |
|---|---|---|
| Horn, B.K.P. (1981) Hill shading and the reflectance map. *Proceedings of the IEEE* 69(1):14–47 | doi:10.1109/PROC.1981.11918 | §IX `p`, `q` weights; §XVI slope as rise over run. VERIFIED |
| Hampel, F.R. (1974) The influence curve and its role in robust estimation. *JASA* 69(346):383–393 | doi:10.1080/01621459.1974.10482962 | robust scale whose MAD Fusion cites. VERIFIED |
| Rousseeuw, P.J. & Croux, C. (1993) Alternatives to the median absolute deviation. *JASA* 88(424):1273–1283 | doi:10.1080/01621459.1993.10476408 | MAD definition, including the 1.4826 factor Fusion applies and this layer does not. VERIFIED |
| Shepard, M.K., Campbell, B.A., Bulmer, M.H., Farr, T.G., Gaddis, L.R. & Plaut, J.J. (2001) The roughness of natural terrain: a planetary and remote sensing perspective. *JGR Planets* 106(E12):32777–32795 | doi:10.1029/2000JE001429 | roughness is scale-dependent, so the window and `cell_m` are pinned. VERIFIED. The 3×3 population RMS is not attributed to a page of this paper |
| Fournier, A., Fussell, D. & Carpenter, L. (1982) Computer rendering of stochastic models. *CACM* 25(6):371–384 | doi:10.1145/358523.358553 | upstream 2320 generator only, already verified in `dem-fixture-spec.md`. Not re-derived here |

## 13. Open points for Strata / Verity

- Confirm or replace registry **2380** before any implementation PR.
- Fusion still chooses layer `weight` and `direction`. This spec does not.
- Verity sign-off on this draft is still open. Tile code stays out until that sign-off and the other Discussion #44 gates.
