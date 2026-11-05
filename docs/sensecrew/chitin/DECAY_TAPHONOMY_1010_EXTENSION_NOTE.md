# Decay-taphonomy → extend registry 1010 (doc-only, awaiting Verity)
Licence: UNLICENSED (private repo; licence pending Audrey)
Supersedes NEW-21 and withdrawn 1060 (collision, Discussion #25). **No new id allocated.** Chitin will extend existing registry **1010** (`forensic_models/taphonomy`, present on `sar-consolidation` / `sar-make-it-work`, not on main) **after Verity clears case-file lineage**. Until then taphonomy.py and INSECT_TRACES.md are not opened, copied, vendored, or imported; no 1010 entry is added to registry.json in this PR.
## Intended scope once cleared
Seeded analytic decay-stage / VOC-proxy timeline for training driven by ADD (consume 2350's clean-room ADD). Synthetic only, non-graphic. Non-goals: real case data, graphic content, coupling to evidence/, dossier, hfmr; refloat_timing reuse (Verity gate).
Citation (Crossref-verified 2026-11-04): Megyesi M.S., Nawrocki S.P., Haskell N.H. (2005) Using accumulated degree-days to estimate the postmortem interval from decomposed human remains. J Forensic Sci 50(3). doi:10.1520/JFS2004017
## Humus soil interface (pending co-sign)
| Field | Unit | Source |
|---|---|---|
| moisture_vwc | m³/m³ | Humus |
| dielectric | relative permittivity | multi_proxy/dielectric.topp_dielectric |
| synthetic_voc_proxies | arbitrary training units | lab_readers schema shape, synthetic curves only |
| soil_dna_sensor_copies_per_g | copies/g soil | qpcr_assay (soil_dna_sensor, never EDNA), when Humus ready |
