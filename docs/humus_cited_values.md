# Humus-owned physics values (GDD v0.3 / SOIL_SENSING_TIERS)

**Pair:** Humus-D · **Date:** 2026-11-04 (America/Denver) · **Status:** DRAFT for Verity co-sign (r3 tally)  
**Sources of ownership:** GDD v0.3 §7 pending audits; GDD v0.1 §3 tier table (nodes unchanged in v0.3); `sar/docs/SOIL_SENSING_TIERS.md`.  
**Rule (GDD L1):** every physics value needs owning-pair citation + Verity co-sign; otherwise PLACEHOLDER and unscorable.  
**DOI check:** each cited DOI was confirmed to resolve in the Crossref Works API this session (2026-11-04). Values without a readable numeric claim from a verified source stay PLACEHOLDER — nothing invented.

## Humus-owned nodes

| Node id | Name | Owner | Repo hooks |
|---|---|---|---|
| 2a (ε_r share) | GPR travel time needs ε_r | Deepscan + **Humus (ε_r)** | `gpr-wave-model/`, `multi_proxy/dielectric.py` |
| 2d | Soil dielectric / moisture | **Humus** | `multi_proxy/dielectric.py` |
| 3a | soil_dna_sensor qPCR | **Humus** | `qpcr_assay.py` / `soil_dna_sensor.py`, `qpcr_interpret.py` |
| 3b | GC-MS / 16S (VOC / community) | **Humus + Chitin** | `lab_readers.py` |
| (decay chemistry context) | burial soil pH / N / P shifts feeding 3b | **Humus** (chemistry) + Chitin (taphonomy 3d) | literature → future NEW-09 / 3b baselines |

## Cited value table

**Tally rule (single):** a row is **CITED** if it carries a concrete value, bound, direction, or timing **and** a Crossref-verified DOI; otherwise **PLACEHOLDER**. Hybrid cells (cited direction + uncited magnitude) count as **CITED** for the direction/timing only; the magnitude stays listed as PLACEHOLDER in the same cell and is **not** double-counted as a second PLACEHOLDER row.

| # | Node | Quantity | Value / range | Unit | Citation | DOI | Class |
|---|---|---|---|---|---|---|---|
| 1 | 2d | Air-dry mineral-soil Ka (Topp at θ_v=0) | **3.03** | 1 | Topp, Davis & Annan (1980) | 10.1029/WR016i003p00574 | CITED |
| 2 | 2d | Topp θ_v(Ka) polynomial | θ_v = −5.3×10⁻² + 2.92×10⁻² Ka − 5.5×10⁻⁴ Ka² + 4.3×10⁻⁶ Ka³ | m³/m³ | Topp et al. (1980) | 10.1029/WR016i003p00574 | CITED |
| 3 | 2d | θ_v applicability (1 MHz–1 GHz mineral soils) | air-dry → water-saturated; SE **0.013** | m³/m³ | Topp et al. (1980) abstract | 10.1029/WR016i003p00574 | CITED |
| 4 | 2d | Pure-water relative permittivity (~RF, ~20 °C) | **≈ 80** (T/ν-dependent) | 1 | Ellison (2007); Malmberg & Maryott (1956) | 10.1063/1.2360986 ; 10.6028/jres.056.001 | CITED |
| 5 | 2d | Universal saturated-soil Ka (all soils) | — | 1 | porosity-dependent; no single number claimed | — | PLACEHOLDER |
| 6 | 2d | Typical in-situ VWC operating window | — | m³/m³ | needs methods paper | — | PLACEHOLDER |
| 7 | 2d/2a | Mironov ε′,ε″ numeric grid vs clay | model DOIs verified; **grid unread** | 1 | Mironov et al. (2009) + corr. | 10.1109/TGRS.2008.2011631 ; 10.1109/TGRS.2009.2023842 | PLACEHOLDER |
| 8 | 3a | qPCR efficiency / R² acceptance | **E ∈ [0.90, 1.10]**; **R² ≥ 0.98** | 1 | Bustin et al. (2009) MIQE | 10.1373/clinchem.2008.112797 | CITED |
| 9 | 3a | LOD95 / LOQ procedure refs | logistic/probit + CV definitions (not a soil constant) | copies | Forootan (2017); Klymus (2020) | 10.1016/j.bdq.2017.04.001 ; 10.1002/edn3.29 | CITED |
| 10 | 3a | soil_dna_sensor persistence half-life | — | d | needs cited persistence study | — | PLACEHOLDER |
| 11 | 3b | Gravesoil cadaveric VOC suites | **present** (qual.); concentrations — | — | Dekeirsschieter et al. (2012) | 10.1016/j.chroma.2012.03.048 | CITED |
| 12 | 3b/decay | Soil pH under cadavers | early **↑**, late **↓**; ΔpH mag — | 1 | Szelecz et al. (2018) | 10.1016/j.forsciint.2018.02.031 | CITED |
| 13 | 3b/decay | Soil NH4+/N/P / nitrate timing | N/P **↑** d15–59; nitrate **↑** d263–367; mg/kg — | — | Szelecz et al. (2018) | 10.1016/j.forsciint.2018.02.031 | CITED |
| 14 | 3b/decay | Numeric game bounds from review | — | — | Frontiers 2023 review (qual. only here) | 10.3389/fsoil.2023.1107432 | PLACEHOLDER |

## Canonical tally (Verity r3 — use this everywhere)

| Class | Count | Row #s |
|---|---|---|
| **CITED** | **9** | 1, 2, 3, 4, 8, 9, 11, 12, 13 |
| **PLACEHOLDER** | **5** | 5, 6, 7, 10, 14 |

**cited = 9 · placeholders = 5**

## Provenance: `gcms_method.example.json`

Path: `sar/blue-ocean-sar/realdata/gcms_method.example.json`

| Fact | Evidence |
|---|---|
| First introduced | commit `c944260` (2026-10-21, author `midnghtsapphire` / Audrey Evans) — message: “sar: consolidate working SAR/lidar/GPR toolchain with numeric registry (only-what-works)” (reachable via `refs/pull/9/head`) |
| Landed on `main` | merge `a263098` (PR #9, 2026-11-04) |
| `git blame` on `main` | all lines attributed to `a263098` (Audrey Evans) — squash/merge attribution; finer authoring is `c944260` on the PR branch |
| Content claim in-file | `_readme` states retention times are **placeholders, not values from any column or method**; `lab_readers.py` refuses the file unless `--allow-example-method` |
| Pre-`c944260` origin (lab notebook, external method, case file, etc.) | **Not determined** from `git log` / `git blame` / PR #9 history. No earlier blob. Honest gap: beyond Audrey’s 2026-10-21 consolidate commit, source of the placeholder RT numbers is unknown. |

## Non-goals

- No LUCAS / case / hfmr / evidence / public_records data.  
- No GitHub Discussion post from this branch (draft text at `/workspace/humus_discussion_draft.md`).
