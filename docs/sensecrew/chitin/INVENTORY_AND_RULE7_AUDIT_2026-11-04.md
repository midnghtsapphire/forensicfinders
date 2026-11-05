# Chitin inventory + rule-7 audit — 2026-11-04
Licence: UNLICENSED (private repo; licence pending Audrey) · Author: Sense-Chitin (Strata task 1) · Base: origin/main a263098

## Path scan (~420 paths, names only)
- insect / taphonomy / degree-day / entomol: **NONE**.
- qpcr: `sar/blue-ocean-sar/realdata/qpcr_assay.py`, `qpcr_interpret.py`, `test_qpcr_assay.py`.

## Quarantine — PRESENT by path name, UNREAD (not opened)
search_theory.py (+test); optimal_search.py (+test); lost_person_behavior.py (+test, lpb_mpb2003.json); sar/case/ (README, example.config.yaml); sar/hfmr/** ; evidence/ under blue-ocean-sar, evidence_fusion/scoring, hfmr evidence_engine; public_records_engine.py (+test); dossier.py (+css, test); case-files: no path match on default branch.

## Safe adjacent (headers/imports only)
| Path | Note |
|---|---|
| realdata/refloat_timing.py | Has accumulated degree-days (river refloat). **Verity R7: CLEAR** to reuse ADD (`daily_contribution`/`accumulate`); **2350** reuses them via `refloat_adapter.py`. LABEL kept always: river-refloat primary model is a **preprint / not peer-reviewed** (surfaced in 2350 JSON `add_engine.label` + CLI stderr). |
| realdata/qpcr_assay.py, qpcr_interpret.py | Humus soil_dna_sensor (copies/g soil). Name is soil_dna_sensor, never EDNA. |
| realdata/lab_readers.py | GC-MS/16S schema; example VOC names; example method refused without flag. |
| realdata/burial_signature.py | DEM mound/sink timeline; not insect; imports only microtopo locally. |
| multi_proxy/dielectric.py | Topp dielectric from moisture (Humus). |
| realdata/fixtures/*synthetic* | Usable pattern. hfmr synthetic_grid is under quarantine — not used. |

## Registry outcome (Discussion #25)
1050/1060 withdrawn (collisions). Insect = **2350 `insect-trace-add-sim`**. Decay = extend **1010** after Verity (doc-only now). `forensic_models/taphonomy.py` + `sar/docs/research/INSECT_TRACES.md`: Verity **CLEAR (0.86)**; live on `sar-make-it-work`, not main. 1010 extension: see SPEC_1010_EXTENSION.md.
