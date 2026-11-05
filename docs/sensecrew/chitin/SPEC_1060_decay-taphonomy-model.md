# SPEC 1060 — decay-taphonomy-model (RESERVED)
Registry id **1060** reserved (Strata; pending Verity). Supersedes placeholder NEW-21. Licence: UNLICENSED (private repo; licence pending Audrey)
## Scope
Seeded analytic decay-stage / VOC-proxy timeline for training, driven by ADD. Synthetic only, non-graphic, educational. Current state: stub package + contract tests (`expectedFailure`) — Driver impl pending Humus co-sign.
## Citation (Crossref-verified 2026-11-04)
- Megyesi M.S., Nawrocki S.P., Haskell N.H. (2005) Using accumulated degree-days to estimate the postmortem interval from decomposed human remains. J Forensic Sci 50(3). doi:10.1520/JFS2004017
## Non-goals
No real case data; no graphic content; no coupling to evidence/, dossier, hfmr; no import of refloat_timing (Verity gate).
## Humus soil interface
| Field | Unit | Source | Status |
|---|---|---|---|
| moisture_vwc | m³/m³ | Humus | pending co-sign |
| dielectric | relative permittivity | multi_proxy/dielectric.topp_dielectric | pending |
| synthetic_voc_proxies | arbitrary training units | lab_readers schema shape, synthetic curves only (not real lab exports) | optional |
| soil_dna_sensor_copies_per_g | copies/g soil | qpcr_assay (soil_dna_sensor, never EDNA) | when Humus ready |
