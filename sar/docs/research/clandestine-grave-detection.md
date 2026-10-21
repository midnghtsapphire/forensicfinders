# Clandestine grave detection: case studies and a phased workflow

**Registry ID: 2080** · **Status: PROTOTYPE / RESEARCH** · Literature review only. Findings are the authors' own
statements (from the abstracts or full text read 2026-10-21). We claim no results.

Registry mapping key: thermal (no component yet; see 2070) · GPR / Gi* void detector **1100–1120** ·
3DEP lidar **920** · waveform lidar **985** (2060) · STAC NDVI/ΔNDVI **910** (the task said 940, but 940 is ArcGIS;
ArcGIS layers can still supply parcels) · ISRID rings **800** · SAR change **980**.

## Sources

| # | Source (verified) | Method | Findings as stated by the authors | Maps to |
|---|---|---|---|---|
| 1 | Koopman M, Milliet Q, Champod C (2025). *A review of predictive modelling and drone remote sensing technologies as a tool for detecting clandestine burials.* Forensic Sci Int 367:112375. doi:[10.1016/j.forsciint.2025.112375](https://doi.org/10.1016/j.forsciint.2025.112375) (PII S0379073825000131) | Review: predictive models (RAG mapping, geographic profiling) + drone LiDAR, RGB, multispectral, hyperspectral and thermal | Predictive models combined with drone sensors "can improve these searches" by cutting time and cost and reducing exposure. Names lidar, RGB, multi/hyperspectral and thermal as promising | 800 (priors), 920/985, 910, thermal |
| 2 | Molina CM, Wisniewski K, Salamanca A, Saumett M, Rojas C, Gómez H et al. (2024). *Monitoring of simulated clandestine graves of victims using UAVs, GPR, electrical tomography and conductivity over 4–8 years post-burial to aid forensic search investigators in Colombia.* Forensic Sci Int 355:111919. doi:[10.1016/j.forsciint.2023.111919](https://doi.org/10.1016/j.forsciint.2023.111919) (PII S0379073823003699) | 12 simulated graves at 0.5–1.2 m, savannah and rainforest; UAV multispectral + GPR, ERT, bulk conductivity, years 4–8 | At year 8 the graves "could still be located using NDVI and NIR multi-spectral data, but not using optical or other multi-spectral data". At years 4–8 they were still detectable with bulk conductivity, GPR horizontal time slices and 2D ERT. Recommends UAV first, then ground reconnaissance and geophysics, before any digging | 910 (NDVI), 1100s/1120 (GPR), conductivity/ERT (no component) |
| 3 | Pringle JK, Stimpson IG, Wisniewski KD, Heaton V, Davenward B, Mirosch N et al. (2020). *Geophysical monitoring of simulated homicide burials for forensic investigations.* Sci Rep 10:7544. doi:[10.1038/s41598-020-64262-3](https://doi.org/10.1038/s41598-020-64262-3) | 10 years of electrical resistivity (ER) and 110–900 MHz GPR over naked and wrapped animal-analogue burials | Naked burial: large low-resistivity anomalies for up to 4 years, then hard to image. Wrapped burial detected by GPR throughout. 225 MHz was the best frequency. Naked burial poorly imaged after 6 years. Do both ER and GPR when burial style is unknown. Winter and spring surveys gave the best data | 1100s/1120 (GPR, dielectric), ER (no component) |
| 4 | Servello JA (2010). *Thermal Identification of Clandestine Burials: A Signature Analysis and Image Classification Approach.* MS thesis (Biology), University of North Texas. doi:[10.12794/metadc33201](https://doi.org/10.12794/metadc33201); <https://digital.library.unt.edu/ark:/67531/metadc33201/> | Helicopter-mounted 3–5 µm thermal imager over simulated graves of different depths; signature analysis plus object-oriented classification | Shows "a relationship between the depth of burial disturbance and the resultant signature"; object-oriented classification "can be successfully applied to single band thermal imagery" | thermal (future) |
| 5 | Riley-Carrier P, Greco M, D'Ottavio A, Schiliro K, Tipple CA (2025). *Screening for clandestine graves via the analysis of infrared images and temperature metrics.* J Forensic Sci 70(3):889–904. doi:[10.1111/1556-4029.70019](https://doi.org/10.1111/1556-4029.70019) (Wiley; PMID 40099769) | Six simulated graves in forest, monitored for 2 years with long-wave IR cameras plus surface/subsurface temperature probes | Statistically significant temperature differences between graves and controls over the whole period. Grave location and time of day mattered. At this site, imaging between 1700 and 0800 h best separated graves from undisturbed ground. Probe and camera data differed | thermal (future) |
| 6 | Berezowski V, Moffat I, Shendryk Y, MacGregor D, Ellis J, Mallett X (2022). *A multidisciplinary approach to locating clandestine gravesites in cold cases: Combining geographic profiling, LiDAR, and near surface geophysics.* Forensic Sci Int: Synergy 5:100281. doi:[10.1016/j.fsisyn.2022.100281](https://doi.org/10.1016/j.fsisyn.2022.100281) | Three steps: (1) geographic profiling, (2) lidar, (3) near-surface geophysics; two Australian cases + one experiment | Each step narrows the area while adding detail. "Although each technique on its own can successfully locate graves, combining the techniques can provide the most efficient approach" | 800 (priors), 920/985 + 1100 Gi*, 1120 |
| 7 | Narreddy V (2024; sole author listed in Crossref). *Geoforensic Methods for Detecting Clandestine Graves and Buried Forensic Objects in Criminal Investigations – A Review.* J Forensic Sci Med 10(3):234–245. doi:[10.4103/jfsm.jfsm_85_22](https://doi.org/10.4103/jfsm.jfsm_85_22) | Review: metal detectors, magnetics, EM conductivity, GPR, probing, detector dogs, gravity/seismic; soil for PMI | Describes the geoforensic search strategy and how soil can help set a primary search area and estimate the postmortem interval | 1120, 2070, 1000s (taphonomy) |
| 8 | Bramble J, Lydon D (2025). *Benefits and barriers: An exploratory study of drone use and LiDAR technology application in UK policing.* Int J Police Sci Manag 27:303–312. doi:[10.1177/14613557251340913](https://doi.org/10.1177/14613557251340913) | FOI requests to 45 UK police services | Drones help operations, but forensic use is held back by "excessive costs, insufficient training, and procedural and regulatory constraints". Recommends SOPs, training and lidar pilots | Process / deployment context (no code) |
| 9 | Singh HN (2018). *The methods used in searching for clandestine burials.* JETIR 5(10), paper JETIR1810B66. <https://www.jetir.org/papers/JETIR1810B66.pdf> | Narrative review of macro-scale search methods | Gives a generalised search workflow and a detection-technique table. **Caution:** the abstract and introduction closely match the wording of Pringle et al. (2012) Earth-Sci Rev 114:108–123 (doi:10.1016/j.earscirev.2012.05.006; cited in 2070). Prefer the original | secondary only |

## Recommended phased search workflow
Each phase narrows the area, following Berezowski et al. (2022) and Molina et al. (2024). Phases 1–3 are
desk or remote work. Nothing goes on the ground without the investigating agency (see HANDOFF guardrails).

1. **Priors (desk).** Size the area with ISRID rings (**800**, Dementia only so far) or a case-specific
   geographic profile. Add access constraints: roads, parcels via ArcGIS (**940**), and slope from 3DEP (**920**).
2. **Change and vegetation (remote).** ΔNDVI/NIR over pre- and post-event epochs (**910**). Molina et al. found
   NDVI/NIR still worked at 8 years where optical did not. Optional SAR change (**980**).
3. **Micro-relief (remote).** Multi-epoch 3DEP lidar → detrend/epoch difference → Gi* (**1100/1110**);
   waveform ground under canopy (**985**) where discrete lidar is sparse. Output: a ranked candidate list, not detections.
4. **Thermal (drone, optional).** Long-wave IR passes in the evening-to-morning window that Riley-Carrier et al.
   reported as best *for their site*. Re-check the timing locally.
5. **Ground geophysics on candidates (agency-led).** GPR around 225 MHz plus ER or bulk conductivity when the burial
   style is unknown, preferably in winter or spring (Pringle et al. 2020). Use **1120** to set dielectric/depth expectations.
6. **Confirmation (agency/forensic).** Probing, dogs, soil/eDNA (**2000**, **1300** QC), excavation by forensic archaeologists.

## Optional connector ideas (not built)
- **PermitStack** — <https://github.com/PermitStack/permitstack-python>. A Speakeasy-generated Python SDK
  (`permitstack` 1.2.5) for a commercial building-permit API (<https://permit-stack.com>), Apache-2.0 per
  `pyproject.toml` and README. GitHub shows no detected license file. Real and actively maintained: created
  2026-05-21, release 1.2.5 on 2026-10-21, 0 stars. It is a vendor SDK, so check the API's terms before any use.
  It claims 119M+ permits from about 898 official city/county sources. Free tier: 100 requests/day and the last
  30 days only; history needs a paid tier. Endpoints include permit search, permits by address and permit events.
  **Possible SAR use:** dated grading, excavation, demolition, septic or pool permits on a candidate parcel can
  explain a lidar/NDVI anomaly (legitimate ground disturbance) or date a disturbance window. Use it only as a
  *disturbance-date lookup by location*. Do not use contractor or owner lookups on people.
- **BackgroundCheckAPI** — <https://github.com/stevedvy/BackgroundCheckAPI>. A README-only repo (2 commits on
  2018-06-20, no license, no code) advertising a commercial people-records API (criminal history, arrests,
  warrants, "U.S. people records"). The vendor site did not answer an HTTPS request on 2026-10-21.
  **Not maintained, no code to review, and it is a person-lookup service.** Not adopted, and no code that touches
  people will be added. Any person-record checks belong to the investigating agency.
