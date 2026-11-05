# Deepscan module specs v0

**Status:** proposal only (doc-only). No code, commits, or GitHub changes in this task.  
**Repo (read-only clone):** `midnghtsapphire/forensicfinders` `sar/` at `/workspace/audit/forensicfinders`, HEAD `a2630989`.  
**Style template:** existing `sar/gpr-wave-model/` — stdlib-first CLI module, JSON payload out, `test_*.py` unittest golden tests, `registry.json` component entry with `test_cwd` + `unittest discover -p test_*.py`.  
**Seeding / Makefile contract (Deepscan hard rules):** every sim is seeded; same seed → byte-identical output; runnable via `make sim SEED=...` and `python -m ...`. Pattern for RNG: `numpy.random.default_rng(seed)` as in `sensor-fusion-grid` / `sar-change-detection`, or `random.Random(seed)` as in `instrument_input` synthetic helpers. Emit `"seed"` in the JSON `parameters` block.  
**Data rule:** synthetic / procedural scenes only; only `fixtures/*synthetic*` paths are valid seed inputs. Never reference or open `case/`, `hfmr/`, `evidence/`, `lpb/`, `search_theory`, `optimal_search`, or public-records code. gprMax is offline-only (separate CLI; never link or ship). Ultralytics / AGPL is forbidden.

Proposed free registry IDs after `500 gpr-wave-model` and before `600`: **510**, **520**, **530** (IDs are stable; Strata confirms numbering before merge).

Common layout for each new module (mirror `gpr-wave-model/`):

```text
sar/<module>/
  README.md
  Makefile                 # sim, test, clean
  <module_snake>.py        # or package with __main__.py
  test_<module_snake>.py
  fixtures/
    *synthetic*            # only synthetic fixtures allowed
```

Common Makefile skeleton:

```makefile
SEED ?= 42
.PHONY: sim test clean
sim:
	python3 -m <module_import> --seed $(SEED) --out results_seed$(SEED).json --no-table
test:
	python3 -m unittest discover -p 'test_*.py' -v
clean:
	rm -f results_seed*.json
```

Common CLI flags (align with `gpr_wave_model.main` argparse style + seed peers): `--seed`, `--out`, `--no-table`, plus physics-specific options. Prefer `python3 -m <pkg>` entry; also allow `python3 <script>.py` like the template.

Common JSON envelope (match gpr-wave-model keys where sensible):

```json
{
  "model": "...",
  "assumptions": ["..."],
  "constants": {},
  "parameters": { "seed": 42 },
  "results": {}
}
```

Byte-identical contract: serialize with `json.dumps(..., indent=2, allow_nan=False, sort_keys=True)` of a rounded canonical payload (or write float arrays as fixed-decimal lists). Two runs with the same seed and args must produce identical file bytes. Tests assert `a == b` on the serialized string (and/or `filecmp`).

---

## 1. `ert-model` (proposed registry id `510`)

### Purpose

Analytic / semi-analytic **DC resistivity forward model** for training-game ground detection: apparent resistivity for Wenner and dipole–dipole arrays over (a) a 1-D layered half-space and (b) a buried resistive/conductive sphere or air void. Stdlib-first core (like `gpr-wave-model`); optional offline comparison against a permissive library is documented below, not required to ship.

### Inputs / outputs (SI units)

| Name | Role | Unit | Notes |
|---|---|---|---|
| `array` | geometry kind | — | `"wenner"` \| `"dipole-dipole"` |
| `a_m` | electrode spacing (Wenner *a*; dipole *a*) | m | > 0 |
| `n` | dipole–dipole level | — | integer ≥ 1 (ignored for Wenner) |
| `rho_layers_ohm_m` | layer resistivities | Ω·m | length *N* |
| `thickness_m` | layer thicknesses (top *N−1*) | m | half-space below is infinite |
| `sphere_center_m` | (x, y, z) of sphere centre | m | z > 0 depth positive down |
| `sphere_radius_m` | sphere radius | m | > 0; must not breach surface |
| `sphere_rho_ohm_m` | sphere resistivity | Ω·m | air void ≈ ∞ (use large sentinel, e.g. 1e6) |
| `host_rho_ohm_m` | host half-space resistivity (sphere case) | Ω·m | |
| `profile_x_m` | midpoints along a line | m | list |
| `seed` | RNG seed for optional noise | — | int; noise off if `noise_pct=0` |
| `noise_pct` | Gaussian relative noise on ρₐ | % | default 0 |

**Outputs (JSON):**

| Name | Unit | Notes |
|---|---|---|
| `apparent_resistivity_ohm_m` | Ω·m | one value per midpoint / spacing |
| `geometric_factor_m` | m | array geometric factor *K* |
| `potential_diff_V` | V | optional; for unit current *I* = 1 A |
| `parameters.seed` | — | echoed |

### Physics equations (cite)

Ohm’s law / steady current: **∇ · (σ ∇V) = 0** with σ = 1/ρ (Telford, Geldart & Sheriff, *Applied Geophysics*, 2nd ed., Cambridge University Press, 1990, ch. 8 Electrical properties / Resistivity methods; ISBN 0-521-33938-3).

**Wenner** (electrodes A–M–N–B, spacing *a*):

\[
K_\mathrm{W} = 2\pi a, \qquad
\rho_a = K_\mathrm{W}\,\frac{\Delta V}{I}.
\]

**Dipole–dipole** (dipole length *a*, separation *n a*):

\[
K_\mathrm{DD} = \pi n (n+1)(n+2)\, a, \qquad
\rho_a = K_\mathrm{DD}\,\frac{\Delta V}{I}.
\]

(Geometric factors as in Telford et al. 1990, Resistivity chapter.)

**Layered half-space (1-D):** use the kernel / image or linear-filter Hankel transform of the resistivity transform *T(λ)* for *N* layers (Telford et al. 1990; classic filter: Guptasarma–Singh style is acceptable if cited in the implementation README). Golden tests below lock a **two-layer** closed check: homogeneous half-space → ρₐ = ρ₁ for all *a*; thick resistive basement asymptote.

**Buried sphere in uniform host (semi-analytic):** potential perturbation of a sphere of radius *R*, resistivity ρₛ in host ρₕ in a uniform primary field (or point-current expansion). Leading dipole term for conductivity contrast (Telford et al. 1990, resistivity anomalies of simple shapes; see also Wait-type sphere solutions in the applied-geophysics literature). For an **air void**, take ρₛ → ∞ (contrast factor → +1/2 in the insulating-sphere limit of the classic formula). Spec requires the implementation to document the exact formula used in `README.md` with equation numbers.

### Seeding / determinism contract

- Default: pure analytic, `noise_pct=0` → fully deterministic without RNG; still accept `--seed` and echo it.
- If `noise_pct > 0`: `rng = numpy.random.default_rng(seed)` (or stdlib `random.Random(seed)` if staying numpy-free); multiply ρₐ by `(1 + 0.01*noise_pct*rng.standard_normal(...))`.
- Same `(seed, args)` → **byte-identical** JSON on disk (`sort_keys=True`, fixed rounding, e.g. 6 decimal places on ρₐ).
- No wall-clock, hostname, or unordered dict iteration in the payload.

### Makefile / CLI

```bash
make -C sar/ert-model sim SEED=42
python3 -m ert_model --array wenner --a 2 --rho-layers 100 500 --thickness 5 \
  --profile 0 2 4 6 8 --seed 42 --out results.json
python3 -m ert_model --array dipole-dipole --a 1 --n 2 --sphere-center 0 0 3 \
  --sphere-radius 1 --sphere-rho 1e6 --host-rho 100 --seed 7 --no-table --out void.json
python3 -m unittest discover -s sar/ert-model -p 'test_*.py' -v
```

### Synthetic fixtures (`fixtures/*synthetic*` only)

| Fixture | Content |
|---|---|
| `fixtures/synthetic_two_layer_wenner.json` | ρ=[100,500] Ω·m, h=[5] m, *a* grid, expected ρₐ table (analytic) |
| `fixtures/synthetic_homogeneous_dipole.json` | single half-space ρ=100, dipole–dipole *n*=1..4 |
| `fixtures/synthetic_air_sphere_void.json` | host 100 Ω·m, sphere R=1 m at z=3 m, ρₛ=1e6 |
| `fixtures/synthetic_noisy_seed42.json` | same as homogeneous + `noise_pct=5`, `seed=42` canonical bytes |

### FAILING golden tests to write first (`test_ert_model.py`)

Write these **before** implementation (Deepscan-N style). Expected values below are analytic targets; tolerances are absolute unless noted.

1. **`test_wenner_homogeneous_equals_host`** — ρₕ=100 Ω·m, *a*∈{1,2,5,10} m → ρₐ = 100 ± 1e-9 Ω·m.  
2. **`test_wenner_geometric_factor`** — *a*=2 m → *K*=2π*a* ≈ 12.566371 Ω factor in metres ± 1e-9.  
3. **`test_dipole_dipole_geometric_factor`** — *a*=1 m, *n*=2 → *K*=π·2·3·4·1 = 24π ≈ 75.398224 ± 1e-9.  
4. **`test_two_layer_large_a_approaches_basement`** — ρ=[100,500], h=5 m; at *a* ≫ h, ρₐ within 5% of 500 (document filter truncation).  
5. **`test_insulating_sphere_peak_positive_anomaly`** — air sphere: max(ρₐ)/ρₕ > 1 along surface profile over centre.  
6. **`test_seed_byte_identical`** — `noise_pct=5`, `seed=42` twice → identical JSON bytes.  
7. **`test_cli_writes_valid_json`** — mirror `gpr-wave-model` CLI tempfile test.

### Proposed `registry.json` entry

```json
"510": {
  "name": "ert-model",
  "path": "ert-model",
  "what": "Analytic/semi-analytic DC resistivity forward model (Wenner/dipole-dipole; layered half-space; buried sphere/void)",
  "test_cwd": "ert-model",
  "test": ["python3", "-m", "unittest", "discover", "-p", "test_*.py"],
  "source": "deepscan specs v0 — synthetic only"
}
```

### Licences

| Component | Licence | Role |
|---|---|---|
| Module code (proposed) | match repo (document in README) | ship |
| Python stdlib / numpy (if used) | PSF / BSD-3 | OK |
| **pyGIMLi** (optional offline cross-check) | **Apache-2.0** | optional; do not require at runtime for golden tests |
| **SimPEG** (optional offline cross-check) | **MIT** | optional |
| Ultralytics | AGPL — **FORBIDDEN** | — |

### Open questions

- Stdlib-only vs numpy dependency (gpr-wave-model is stdlib-only; layered Hankel filters are easier with numpy).
- Exact two-layer filter coefficients and citation (Guptasarma & Singh vs Anderson) for the golden asymptotic test.
- Whether sphere solution is uniform-field dipole only or full point-current series (scope vs accuracy).
- Sentinel resistivity for “infinite” air void (1e6 vs 1e9) and float32/64 canonicalization.

---

## 2. `magnetometry-model` (proposed registry id `520`)

### Purpose

Analytic **total-field magnetic anomaly** forward model for a buried dipole / magnetized sphere and a thin dyke, with a **seeded noise model**, for training-game sensor fusion and mag-grid playtests.

### Inputs / outputs (SI)

| Name | Role | Unit | Notes |
|---|---|---|---|
| `model_kind` | `"sphere"` \| `"dipole"` \| `"thin_dyke"` | — | |
| `B0_nT` | inducing / regional total field | nT | e.g. 50000 |
| `inc_deg`, `dec_deg` | ambient field inclination / declination | deg | |
| `susceptibility` | κ (SI) for induced sphere/dyke | — | or remanent moment |
| `m_A_m2` | dipole moment vector (dipole mode) | A·m² | |
| `center_m` / `depth_m` | source centre | m | depth > 0 down |
| `radius_m` | sphere radius | m | sphere mode |
| `dyke_strike_deg`, `dip_deg`, `thickness_m` | thin-dyke geometry | deg, m | |
| `profile_x_m` or `grid_x_m`,`grid_y_m` | observation locations | m | z=0 surface |
| `noise_nT` | Gaussian σ on ΔT | nT | 0 = off |
| `seed` | RNG seed | — | |

**Outputs:**

| Name | Unit |
|---|---|
| `delta_T_nT` | nT (total-field anomaly) |
| `Bx_nT`, `By_nT`, `Bz_nT` | nT (optional vector) |
| `parameters.seed` | — |

### Physics equations (cite)

Potential-field magnetics as in Blakely, R.J., *Potential Theory in Gravity and Magnetic Applications*, Cambridge University Press, 1995, DOI [10.1017/CBO9780511549816](https://doi.org/10.1017/CBO9780511549816).

**Dipole** (moment **m**, observation vector **r** from source):

\[
\mathbf{B}(\mathbf{r}) = \frac{\mu_0}{4\pi}\left(
\frac{3(\mathbf{m}\cdot\hat{\mathbf{r}})\hat{\mathbf{r}} - \mathbf{m}}{r^3}
\right).
\]

**Sphere** (uniform susceptibility κ in ambient **B₀**): equivalent dipole
\(\mathbf{m} = \frac{4\pi R^3}{\mu_0}\,\frac{\kappa}{3+\kappa}\,\mathbf{B}_0\)
(induced, SI; document demagnetization factor used — Blakely 1995, magnetic ideal bodies / spheres).

**Total-field anomaly** (first-order):

\[
\Delta T \approx \hat{\mathbf{B}}_0 \cdot \mathbf{B}_\mathrm{anom}.
\]

**Thin dyke:** use the classic 2-D thin-dyke total-field expression (Blakely 1995; textbook form in terms of depth, dip, strike, and effective magnetization). Implementation README must quote the exact expression and angle conventions (profile perpendicular to strike).

**Noise:** `delta_T_noisy = delta_T + noise_nT * rng.standard_normal(shape)` with `rng = np.random.default_rng(seed)`.

### Seeding / determinism contract

Same as §1: echo `seed`; `noise_nT=0` is RNG-free; non-zero noise must be byte-identical across runs; canonical JSON rounding (e.g. 0.001 nT).

### Makefile / CLI

```bash
make -C sar/magnetometry-model sim SEED=42
python3 -m magnetometry_model --kind sphere --depth 5 --radius 1 --kappa 0.1 \
  --B0 50000 --inc 65 --dec 10 --profile -20:20:0.5 --seed 42 --out mag.json
python3 -m magnetometry_model --kind thin_dyke --depth 10 --dip 90 --thickness 2 \
  --noise-nT 1 --seed 7 --no-table --out dyke.json
python3 -m unittest discover -s sar/magnetometry-model -p 'test_*.py' -v
```

### Synthetic fixtures

| Fixture | Content |
|---|---|
| `fixtures/synthetic_vertical_dipole_profile.json` | m vertical, profile across peak |
| `fixtures/synthetic_sphere_induced.json` | κ, R, depth, ambient field |
| `fixtures/synthetic_thin_dyke_vertical.json` | vertical dyke, E–W strike, N–S profile |
| `fixtures/synthetic_noise_seed42.json` | σ=1 nT, seed=42 canonical bytes |

### FAILING golden tests to write first (`test_magnetometry_model.py`)

1. **`test_dipole_axial_field`** — vertical **m** = (0,0,m), observe on axis at distance *z*:  
   \(B_z = (\mu_0/(4\pi))\,2m/z^3\). Example: *m*=1 A·m², *z*=10 m → *B_z* ≈ 2e-9 T = 2.0 nT ± 1e-6 nT.  
2. **`test_total_field_reduces_to_Bz_when_vertical_B0`** — *inc*=90° → ΔT ≈ Bz_anom within 1e-6 relative.  
3. **`test_sphere_moment_scales_R3`** — double *R* → |m| × 8 (κ fixed, induced).  
4. **`test_thin_dyke_antisymmetric_or_symmetric_by_dip`** — vertical dyke + vertical magnetization → symmetric ΔT about the epicentre (assert even function within tol).  
5. **`test_seed_byte_identical`** — `noise_nT=1`, `seed=42` twice → identical bytes.  
6. **`test_cli_writes_valid_json`** — tempfile CLI like gpr-wave-model.

### Proposed `registry.json` entry

```json
"520": {
  "name": "magnetometry-model",
  "path": "magnetometry-model",
  "what": "Analytic total-field magnetometry forward model (buried dipole/sphere, thin dyke) with seeded noise",
  "test_cwd": "magnetometry-model",
  "test": ["python3", "-m", "unittest", "discover", "-p", "test_*.py"],
  "source": "deepscan specs v0 — synthetic only"
}
```

### Licences

| Component | Licence | Role |
|---|---|---|
| Module code | match repo | ship |
| numpy (likely) | BSD-3 | OK |
| Optional Magento / custom code | verify before add | — |
| Ultralytics | AGPL — **FORBIDDEN** | — |

No GPL runtime link. Pure analytic; no gprMax.

### Open questions

- Induced-only vs remanence vector API.
- 2-D thin-dyke infinite-strike assumption vs finite strike length.
- IGRF / local declination: fixed CLI params vs bundled synthetic ambient tables (`fixtures/*synthetic*` only).
- nT vs T internal SI and conversion single-source.

---

## 3. `gpr-void-detector` (proposed registry id `530`)

### Purpose

**Deterministic** detector of air- or water-filled voids in **synthetic B-scans** produced by / compatible with `gpr-wave-model` (and, offline-only, gprMax-generated synthetic libraries). Uses **hyperbola fitting** plus **polarity / permittivity-contrast** criteria. No neural nets; **Ultralytics/AGPL forbidden**.

### Inputs / outputs

| Name | Role | Unit | Notes |
|---|---|---|---|
| `bscan` | amplitude grid | — | shape `[n_traces, n_samples]` float |
| `dx_m` | trace spacing | m | |
| `dt_ns` | sample interval | ns | |
| `soil_er` | host relative permittivity | — | from scene / gpr-wave-model |
| `freq_mhz` | centre frequency (metadata) | MHz | optional |
| `seed` | reserved / tie-break RNG | — | detector itself must be deterministic even if unused |
| `fixtures/...synthetic...` | only allowed file inputs | — | |

**Outputs:**

| Name | Unit | Notes |
|---|---|---|
| `detections[]` | — | list of void candidates |
| `detections[].x0_m` | m | apex horizontal |
| `detections[].z0_m` | m | apex depth from TWT and *v* |
| `detections[].v_m_per_ns` | m/ns | fitted wave speed |
| `detections[].polarity` | — | `"air_like"` \| `"water_like"` \| `"unknown"` |
| `detections[].score` | — | dimensionless fit quality |
| `parameters.seed` | — | |

Depth from two-way time (same physics family as `gpr-wave-model`):

\[
v = \frac{c}{\sqrt{\varepsilon_r}}, \quad
z = \frac{v\, t_\mathrm{apex}}{2}, \quad
c = 0.299792458\ \mathrm{m/ns}.
\]

### Physics / algorithm (cite)

**Hyperbola geometry** for a point-like scatterer at (*x₀*, *z₀*):

\[
t(x) = \frac{2}{v}\sqrt{(x-x_0)^2 + z_0^2}.
\]

Fit (*x₀*, *z₀*, *v*) by deterministic least squares / RANSAC-free grid search over a fixed seed-independent grid (document grid in README). Prefer closed-form linearization in *x²* when *v* is fixed from `soil_er`.

**Polarity / contrast** (Fresnel, normal incidence — same as `gpr_wave_model.fresnel_r`):

\[
R = \frac{\sqrt{\varepsilon_{r,1}} - \sqrt{\varepsilon_{r,2}}}{\sqrt{\varepsilon_{r,1}} + \sqrt{\varepsilon_{r,2}}}.
\]

- Soil → **air** (ε_r≈1): *R* > 0 for typical soil ε_r>1 → label `"air_like"` when first-break polarity matches the soil→low-ε convention used in `gpr-wave-model` (`polarity: "same"` when *R*>0 in that module’s sign convention — **align explicitly** with `fresnel_r` / `polarity` fields).  
- Soil → **water** (ε_r≈80): *R* < 0 → `"water_like"`.

Reference family: Daniels, D.J. (ed.), *Ground Penetrating Radar*, 2nd ed., IET, 2004 (DOI [10.1049/SBRA051E](https://doi.org/10.1049/SBRA051E)); Annan workshop notes / Sensors & Software GPR literature for hyperbola interpretation; Telford et al. 1990 for EM wave speed in dielectrics. Cross-check travel times against `gpr-wave-model.velocity` / `twt_ns`.

**gprMax:** may generate offline synthetic B-scan libraries only (GPL-3 tool, separate process); never import/link gprMax in this module. Golden path for CI: synthetic B-scans from analytic hyperbola rasterization + `gpr-wave-model` parameters — no gprMax in `registry.json` test command.

### Seeding / determinism contract

- Algorithm must be **fully deterministic**: fixed thresholds, fixed grid, no hash randomization, no `random` unless `--seed` selects among equal-score ties with `random.Random(seed)`.
- Same input array + params + seed → byte-identical JSON.
- Floating convolutions: use explicit rounding in the exported detection list.

### Makefile / CLI

```bash
make -C sar/gpr-void-detector sim SEED=42
python3 -m gpr_void_detector \
  --bscan fixtures/synthetic_air_void_bscan.json \
  --soil-er 9 --dx 0.05 --dt 0.1 --seed 42 --out detections.json
python3 -m unittest discover -s sar/gpr-void-detector -p 'test_*.py' -v
```

`make sim` should run the detector on a default synthetic fixture (not live acquisition).

### Synthetic fixtures

| Fixture | Content |
|---|---|
| `fixtures/synthetic_air_void_bscan.json` | rasterized hyperbola, soil ε_r=9, air scatterer, known (*x₀*,*z₀*) |
| `fixtures/synthetic_water_void_bscan.json` | same geometry, water polarity |
| `fixtures/synthetic_two_voids_bscan.json` | two apexes, non-overlapping |
| `fixtures/synthetic_null_bscan.json` | noise-only / no hyperbola (seeded) |
| `fixtures/synthetic_from_gpr_wave_model_meta.json` | metadata tying ε_r / TWT to `gpr-wave-model` numbers |

### FAILING golden tests to write first (`test_gpr_void_detector.py`)

1. **`test_hyperbola_apex_recovers_known_x0_z0`** — synthetic air void at *x₀*=2.0 m, *z₀*=1.0 m, ε_r=9 →  
   *v* = 0.299792458/3 ≈ 0.099931 m/ns; recover *x₀* ± 0.05 m, *z₀* ± 0.05 m.  
2. **`test_velocity_matches_gpr_wave_model`** — fitted *v* within 1e-4 of `gpr_wave_model.velocity(9.0)`.  
3. **`test_air_polarity_label`** — fixture with *R*>0 convention → `polarity == "air_like"`.  
4. **`test_water_polarity_label`** — water fixture → `polarity == "water_like"`.  
5. **`test_null_bscan_no_detections`** — null fixture → `detections == []`.  
6. **`test_seed_byte_identical`** — same inputs twice → identical JSON bytes.  
7. **`test_rejects_ultralytics_import`** — optional guard: module source must not import `ultralytics` (static string/AST check).  
8. **`test_cli_writes_valid_json`**.

### Proposed `registry.json` entry

```json
"530": {
  "name": "gpr-void-detector",
  "path": "gpr-void-detector",
  "what": "Deterministic GPR void detector (hyperbola fit + polarity/contrast) on synthetic B-scans; no Ultralytics",
  "test_cwd": "gpr-void-detector",
  "test": ["python3", "-m", "unittest", "discover", "-p", "test_*.py"],
  "source": "deepscan specs v0 — synthetic only; gprMax offline-only if used to build fixtures"
}
```

### Licences

| Component | Licence | Role |
|---|---|---|
| Module code | match repo | ship |
| `gpr-wave-model` (peer) | repo | travel-time / Fresnel cross-check |
| gprMax (optional fixture factory) | GPL-3 | **offline CLI only**; never ship/link |
| Ultralytics | AGPL | **FORBIDDEN** |
| Classical CV (optional): OpenCV | Apache-2.0 | only if needed; prefer stdlib/numpy |

### Open questions

- B-scan on-disk format (JSON lists vs `.npy` under `fixtures/*synthetic*` only).
- Single-channel analytic rasterizer in-module vs requiring precomputed fixtures.
- Multi-hyperbola matching cost and max detections.
- Exact polarity sign convention lockstep with `gpr_wave_model` `polarity` field naming (`same`/`reversed` vs `air_like`/`water_like` mapping table).

---

## forensic_pipeline vs rule 7 (no code bodies opened)

**Method (allowed only):** `sar/registry.json` entry text; file names via `find` / `rg -l`; import lines via `rg -n '^(import|from)'` and the continued `from forensic_pipeline.snow_wells_pipes import (...)` name list; `def`/`class` names via `rg -n '^(def |class )'`. **Did not open** function bodies or read `case/`, `hfmr/`, `evidence/`, `lpb/`, search_theory, or public-records code.

### Evidence

**Registry entry `990` (`what` / notes):**  
*"Private forensic pipeline: pure-function residuals for snow wells, rootball trenches, culvert ice trajectory, pipe airflow/odour, local image accent, **ISRID priors**, **finder confirmation**. Array-in/array-out, no I/O."*  
Registered 2026-11-04 after governance audit; pytest (not unittest); requires pytest, numpy, scipy.

**Files present:**

- `forensic_pipeline/__init__.py`
- `forensic_pipeline/snow_wells_pipes.py`
- `forensic_pipeline/tests/__init__.py`
- `forensic_pipeline/tests/test_snow_wells_pipes.py`

**Import lines only:**

- `numpy`, `pytest`, `scipy.ndimage.uniform_filter`
- From `forensic_pipeline.snow_wells_pipes`:  
  `tree_well_residual`, `rootball_trench_residual`, `culvert_ice_trajectory`, `pipe_airflow_residual`, `local_image_accent`, **`isrid_prior_map`**, **`finder_confirmation`**

**No import lines** referencing `case`, `hfmr`, `evidence`, `lpb`, `search_theory`, `optimal_search`, or public-records modules were observed.

### Flag

**Likely needs a rule-7 review: YES.**

**Why:** Rule 7 forbids case/PII/public-records paths and requires synthetic-only fixtures. This component does **not** show forbidden imports in the import lines checked, but its **registry description and exported names** (`isrid_prior_map`, `finder_confirmation`, “Private forensic pipeline”) sit next to Quill/ISRID search-scenario territory and SAR-adjacent forensic framing. That is enough to warrant an explicit rule-7 / synthetic-only audit (confirm no case fixtures, no PII, no coupling to deselected `evidence.*` tests, and that ISRID usage is statistical/synthetic only) before Deepscan or other pairs reuse it. Deepscan’s three new modules above must **not** import `forensic_pipeline` until that review clears.

---

## References cited (confidence-checked)

1. Telford, W.M., Geldart, L.P., Sheriff, R.E. *Applied Geophysics*, 2nd ed., Cambridge University Press, 1990. ISBN 0-521-33938-3.  
2. Blakely, R.J. *Potential Theory in Gravity and Magnetic Applications*, Cambridge University Press, 1995. DOI: 10.1017/CBO9780511549816.  
3. Daniels, D.J. (ed.) *Ground Penetrating Radar*, 2nd ed., IET, 2004. DOI: 10.1049/SBRA051E.  
4. pyGIMLi — Apache-2.0 (https://www.pygimli.org/about/license/).  
5. SimPEG — MIT (https://github.com/simpeg/simpeg/blob/master/LICENSE).

---

## Out of scope / non-actions for this task

- No implementation code, no `registry.json` edit, no commits, no pushes, no GitHub PRs.  
- No opening of forbidden trees.  
- Strata owns final registry number assignment and LEDGER lines when implementation starts.
