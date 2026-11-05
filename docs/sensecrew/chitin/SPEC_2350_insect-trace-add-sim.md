# SPEC 2350 — insect-trace-add-sim
Registry id **2350** `insect-trace-add-sim` (Strata/Verity, Discussion #25). Supersedes NEW-20 and withdrawn 1050 (collision). Name avoids "evidence". Licence: UNLICENSED (private repo; licence pending Audrey)
## Scope
Seeded analytic accumulated-degree-day (ADD) insect-development sim for **training games only**. Educational, non-graphic. Synthetic fixtures only (`fixtures/species_synthetic.json`, fictional taxon). No real cases, PII, images.
## Model (clean-room)
Daily ADD = max(0, (Tmax+Tmin)/2 − base) °C·day (averaging method); stage = last stage whose ADD threshold ≤ cumulative ADD. Units: °C, degree-days.
Citations (Crossref-verified 2026-11-04):
- Amendt J. et al. (2007) Best practice in forensic entomology—standards and guidelines. Int J Legal Med. doi:10.1007/s00414-006-0086-x
- Nabity P.D. et al. (2006) Effects of temperature on development of *Phormia regina*… J Med Entomol 43(6). doi:10.1603/0022-2585(2006)43[1276:EOTODO]2.0.CO;2
## Verity gate
`realdata/refloat_timing.py` is **not imported or reused** (Strata GUARD) until Verity clears lineage. Revisit consolidation (rule 10) after clearance.
## Humus soil interface
Optional `soil_moisture_vwc` / dielectric (`multi_proxy/dielectric.topp_dielectric`) as modifier — **identity by default** until Humus co-signs a literature-cited effect. Tested.
## Tests (written first, Chitin-N, red commit precedes impl)
same seed → byte-identical JSON; different seed differs; daily ADD math; stage only after threshold; soil identity; synthetic+licence; CLI.
## Run
`cd sar/insect-trace-add-sim && make test` · `python3 -m insect_trace_add_sim --seed 7` · `python3 sar/registry.py 2350 --test`
## Additional Verity gates
`forensic_models/taphonomy.py` (registry 1010 on sar-make-it-work) and `sar/docs/research/INSECT_TRACES.md` are **BLOCKED — not opened, copied, or imported** until Verity clears case-file lineage.

## Update 2026-11-04 — 1010 live import
Verity (via Strata): `forensic_models/taphonomy` CLEAR (0.86) and **constants CLEAR (0.92)**. Prior BLOCKED note for taphonomy is historical; this branch now live-imports 1010 via `decay_taphonomy_bridge` (files checked out unchanged from `origin/sar-make-it-work`). `sar/docs/research/INSECT_TRACES.md` gate unchanged until separately cleared. topp_* Verity nit left alone.
