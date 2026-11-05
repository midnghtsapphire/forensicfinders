# Humus-owned physics values (GDD v0.3 / SOIL_SENSING_TIERS)

**Pair:** Humus-D · **Date:** 2026-11-04 (America/Denver) · **Status:** DRAFT for Verity co-sign  
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

| Node | Quantity | Value / range | Unit | Citation | DOI (Crossref OK) | Verity |
|---|---|---|---|---|---|---|
| 2d | Apparent permittivity of air-dry mineral soil (Topp Ka at θ_v = 0) | **3.03** | 1 (relative) | Topp, Davis & Annan (1980), Ka = 3.03 + 9.3θ_v + 146θ_v² − 76.7θ_v³ | 10.1029/WR016i003p00574 | PENDING |
| 2d | Topp θ_v from Ka (inverse polynomial) | θ_v = −5.3×10⁻² + 2.92×10⁻² Ka − 5.5×10⁻⁴ Ka² + 4.3×10⁻⁶ Ka³ | m³/m³ | Topp et al. (1980) | 10.1029/WR016i003p00574 | PENDING |
| 2d | θ_v applicability (mineral soils, TDR 1 MHz–1 GHz) | air-dry → water-saturated; error of estimate **0.013** | m³/m³ | Topp et al. (1980) abstract | 10.1029/WR016i003p00574 | PENDING |
| 2d | Relative permittivity of pure water (~RF/microwave, ~20 °C) | **≈ 80** (static / low-GHz; T- and ν-dependent) | 1 | Ellison (2007) interpolation ε(ν,T); Malmberg & Maryott (1956) water 0–100 °C | 10.1063/1.2360986 ; 10.6028/jres.056.001 | PENDING — exact (ν,T) cell for game table TBD |
| 2d | Universal saturated-soil Ka (single number for all soils) | **PLACEHOLDER** | 1 | Saturation Ka depends on porosity; Topp θ_v=1 endpoint is not a field saturated-soil constant | — | — |
| 2d | Typical in-situ VWC operating window (mineral soils) | **PLACEHOLDER** | m³/m³ | Needs a methods paper with stated field bounds; do not invent 0–0.5 | — | — |
| 2d / 2a | Mironov moist-soil dielectric vs clay fraction | model DOI verified; numeric ε′,ε″ grid **PLACEHOLDER** | 1 | Mironov et al. (2009) + correction (2009) | 10.1109/TGRS.2008.2011631 ; 10.1109/TGRS.2009.2023842 | PENDING |
| 3a | qPCR standard-curve efficiency acceptance band | **0.90–1.10**; R² **≥ 0.98** (as implemented; MIQE reporting basis) | 1 | Bustin et al. (2009) MIQE | 10.1373/clinchem.2008.112797 | PENDING |
| 3a | LOD95 definition (95% detection) | method (logistic/probit on dilution series) — not a soil physical constant | copies / reaction | Forootan et al. (2017); Klymus et al. (2020) | 10.1016/j.bdq.2017.04.001 ; 10.1002/edn3.29 | PENDING |
| 3a | soil_dna_sensor persistence / decay half-life in soil | **PLACEHOLDER** | d | Needs a cited soil-DNA persistence study before scoring | — | — |
| 3b | Decay-VOC identity in buried-carcass soil (qualitative) | cadaveric VOC suites reported in gravesoil (incl. S-compounds); **concentrations PLACEHOLDER** | — | Dekeirsschieter et al. (2012) | 10.1016/j.chroma.2012.03.048 | PENDING |
| 3b / decay | Soil pH under surface-placed cadavers | early **increase**, late **decrease** (direction cited; ΔpH magnitude **PLACEHOLDER**) | 1 | Szelecz et al. (2018) | 10.1016/j.forsciint.2018.02.031 | PENDING |
| 3b / decay | Soil ammonium / total N / P under cadavers | significant **increase** days 15–59; nitrate increase days 263–367 (timing cited; mg/kg magnitudes **PLACEHOLDER**) | — | Szelecz et al. (2018) | 10.1016/j.forsciint.2018.02.031 | PENDING |
| 3b / decay | Review of cadaver imprint on soil C/N/P | qualitative synthesis; numeric game bounds **PLACEHOLDER** | — | 2023 Frontiers review | 10.3389/fsoil.2023.1107432 | PENDING |

## Counts (this draft)

- **Cited numeric / bounded claims (ready for Verity co-sign):** 7  
  (dry Ka=3.03; Topp inverse; θ_v SE 0.013; water ≈80; E∈[0.90,1.10] & R²≥0.98; LOD95 method refs; VOC presence qualitative+DOI)
- **PLACEHOLDER rows:** 7  
  (universal saturated Ka; typical VWC window; Mironov ε grid; DNA half-life; VOC concentrations; ΔpH magnitude; N/P mg/kg magnitudes — review row counts with the N/P PLACEHOLDER)

Recount strictly:

**CITED (have both a value-or-bound and a verified DOI):**  
1. dry Ka = 3.03  
2. Topp inverse polynomial  
3. θ_v error of estimate 0.013 / air-dry→saturated applicability  
4. water ε ≈ 80  
5. qPCR E 0.90–1.10 / R² ≥ 0.98  
6. LOD95/LOQ method DOIs (Forootan, Klymus)  
7. pH direction early↑ late↓ (Szelecz)  
8. N/P early increase + late nitrate (Szelecz timing)  
9. VOC suites present in gravesoil (Dekeirsschieter)  
10. Mironov model existence (DOIs) — model cited, grid PLACEHOLDER → count model as cited existence only if we list a value; **not counted as a numeric cite**

Final tally used in the Discussion draft: **cited = 8** (items 1–5, 7–9; item 6 is method not a physical range), **PLACEHOLDER = 6** (saturated Ka, typical VWC, Mironov ε′,ε″ grid, DNA half-life, VOC concentrations, ΔpH and N/P magnitudes collapsed as chemistry magnitudes).

Simpler report line for parent: **cited_values = 8, placeholders = 6** (see table rows marked PLACEHOLDER).

## Non-goals

- No LUCAS / case / hfmr / evidence / public_records data.  
- No GitHub Discussion post from this branch (draft text lives at `/workspace/humus_discussion_draft.md`).
