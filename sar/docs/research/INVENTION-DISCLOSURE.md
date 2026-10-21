# Invention disclosure — Audrey Evans (PROTOTYPE / RESEARCH)

**Registry ID: 2040** · **Status: PROTOTYPE / RESEARCH** · **Not legal advice.**

This note records concepts invented / reduced to writing by **Audrey Evans** for possible U.S. patent protection. It is an internal disclosure for counsel and filing prep. It is **not** a patent application, **not** an opinion on patentability or infringement, and **not** legal advice. Consult a registered patent attorney or the [USPTO Patent Pro Bono Program](https://www.uspto.gov/patents/basics/using-legal-services/pro-bono/patent-pro-bono-program) before filing or publishing.

**Confidentiality:** Keep this document and related code in a **private** repository until a provisional (or nonprovisional) is on file. Do not post public blogs, open PRs to public forks, or demo videos that enable others to practice the claimed combination. The `forensicfinders` remote is private; leave it that way.

**Disclosure date (America/Denver):** 2026-10-21.

**Contemporaneous evidence (git commits on `sar-make-it-work`, author times America/Denver):**

| Commit | Date (America/Denver) | Evidence |
|---|---|---|
| `f7093ad` | 2026-10-21 11:40 | Soil eDNA research **2000** + PROTOTYPES index |
| `ce505ec` | 2026-10-21 11:52 | Phone-GPR / mmWave add-on roadmap **2020** |
| `e59e3cb` | 2026-10-21 11:57 | VHR SAR + lidar fusion **2030**, `sar_pair` **980**, Pi host + `pi_radar_logger` **811** |

Related registry notes: `phone-gpr-addon.md` (**2020**), `pi_radar_logger.py` (**811**), `vhr-radar-lidar-fusion.md` (**2030**), `sar_pair.py` (**980**), `soil-edna-detection.md` (**2000**).

---

## Concept 1 — Phone- or Raspberry Pi–attached shallow radar for SAR

**Registry:** **2020** (+ logger **811**).

### Dated description (2026-10-21)
A field kit in which a **USB / SPI shallow radar board** (mmWave crawl class such as Infineon BGT60 / TI IWR6843, or a lower-frequency GPRino-class walk unit) is hosted by a **smartphone and/or Raspberry Pi 5 / Zero 2 W**. The Pi (or phone) logs **raw returns** with **GNSS + UTC**, optionally using a Pico/ESP32 for timing/ADC, streams a **preview** to a phone over local Wi-Fi or BLE, and feeds profiles into a SAR pipeline (dielectric/depth model **1120**, instrument ingest **810**, timeline **1913**). Depth claims for 60 GHz kits are limited to drywall-class media; soil/concrete GPR needs MHz-class antennas (documented honestly in **2020**).

### Problem
Search-and-rescue and forensic field teams lack a **cheap, portable, raw-export** shallow radar package that (a) stamps every burst with survey-grade enough GPS/time for evidence chains, (b) works offline with a Pi host when phones are restricted, and (c) plugs into an existing SAR sector/timeline toolchain—not only a consumer wall-stud cartoon app.

### Novel elements (as conceived)
1. **SAR-specific capture contract:** `meta.json` + `gps.jsonl` + raw `radar/` + optional `preview/` under a capture directory, registry-tagged, authority-noted, case PII kept out of git.
2. **Dual-host packaging:** phone as UI/preview; **Pi as rugged logger** with power bank + NEO-M8N-class GPS; optional Pico/ESP32 sync.
3. **Honest band ladder:** 60 GHz crawl for walls/pavers → MHz GPR walk for soil, with dielectric model **1120** for depth uncertainty—not marketing “through concrete” at mmWave.
4. **Pipeline join:** bursts become instrument rows and timeline events for the same case sectors as cameras/satellites.

### Claim-style feature list (illustrative — not filed claims)
- A portable SAR radar logging system comprising a shallow radar transceiver, a single-board computer host, a GNSS receiver, and non-transitory storage storing instructions to write co-located raw radar bursts and GPS/time records to a structured capture directory.
- The system of above, further comprising wireless preview of a downsampled range-profile summary to a handheld device on a local link without requiring a cloud service.
- The system of above, further comprising transforming a range profile into a depth estimate using a sourced dielectric mixing model and emitting a timeline event consumable by a SAR case merger.
- A method of field shallow-radar survey for search operations comprising capturing vendor IQ or range-profile data on a Pi host, stamping GNSS fixes, and refusing soil-penetration claims for mmWave bands in the recorded metadata.

---

## Concept 2 — Separate VHR SAR change and lidar micro-relief add-ons with shared interchange (optional light fusion)

**Registry:** **2030** (+ stub **980**).

### Dated description (2026-10-21)
Two **separate** software/data add-ons—(B1) VHR / satellite **SAR change** (amplitude-ratio and optional coherent-change on co-registered GeoTIFF pairs; band metadata required) and (B2) **lidar / DEM micro-relief** (DTM residual + Gi\* clustering)—that exchange a common **GeoTIFF + GeoJSON (+ timeline JSONL)** contract. Prefer option **B** over a monolithic fusion score. Free-data crawl: Sentinel-1 via **910** + 3DEP via **920** + Gi\* **1100/1110**; VHR X-band (Umbra/Capella open) for method practice; L-band (ALOS-2 where accessible) when canopy penetration matters. Explicit physics: **X-band does not meaningfully penetrate leaf-on canopy**; L/P-band better. No claimed person detection from space.

### Problem
Operators are sold vague “radar sees through trees / finds graves” narratives. Existing tools either fuse sensors into an opaque score or leave SAR and lidar in disconnected apps. Missing-person work needs **triage layers** with band-honest metadata, shared files, and human review—not an unsupervised grave classifier.

### Novel elements (as conceived)
1. **Product shape B:** two shippable add-ons + interchange, deferring fusion until labelled cells exist.
2. **Band-aware sidecar** on every cue raster (`sensor`, `band`, `t0`/`t1`) that forbids mislabeling X-band as penetrating.
3. **Join to SAR ops stack:** cues → **1913** timeline and sector runners; Gi\* ROC only with user labels (**1100**).
4. **Stubbed pair math (**980**):** GeoTIFF amplitude-ratio dB + windowed coherent-change index with synthetic tests—implementation evidence, not a field result.

### Claim-style feature list (illustrative)
- A computer-implemented SAR triage method comprising generating a first georeferenced change raster from two SAR amplitude images, generating a second georeferenced micro-relief raster from a digital terrain model, writing both to a shared raster/vector schema, and presenting both as separate timeline events without computing an automatic detection score.
- The method of above, wherein metadata associated with the SAR raster identifies radar band and the system suppresses or flags canopy-penetration assertions when the band is X-band or C-band.
- A non-transitory medium storing instructions to compute a log-ratio GeoTIFF and a local complex-coherence index from a SAR image pair and to refuse processing when transforms differ without an explicit resample flag.
- Optionally, after obtaining labelled disturbance cells, joining the two cue layers and reporting ROC metrics without claiming person detection.

---

## Concept 3 — Soil eDNA detection, human then canine

**Registry:** **2000**.

### Dated description (2026-10-21)
A staged forensic product: validate **human** DNA / eDNA recovery from **soil** (published extraction + human-specific qPCR/mtDNA assay + QC **1300**), then add **canine** markers; later consider CDI chemistry and only then remote proxies (NDVI/lidar triage → sample grids). Crawl cites peer-reviewed soil/forensic DNA and CDI literature; Hirashima et al. 2022 FSI abstract (DOI [10.1016/j.forsciint.2022.111284](https://doi.org/10.1016/j.forsciint.2022.111284)) noted for BSA additives. Canine is explicitly **after** human validation—not a parallel first SKU. No claimed field detections yet.

### Problem
Burial and deposition sites leave chemical and genetic traces in soil, but field kits and “grave from space” products skip validated soil assays, inhibition QC, and species order (human vs dog). Investigators need a **crawl → portable kit → optional remote triage** path with chain-of-custody QC.

### Novel elements (as conceived)
1. **Ordered product ladder:** human soil assay → canine add-on → remote proxies only as sampling guides.
2. **Integration with existing SAR QC/timeline:** QuantStudio/Bio-Rad exports through **1300**; positive grids become timeline/sample events, not pixel scores.
3. **Explicit rejection of speculative satellite-only grave detectors** until labelled panels exist (**2000** Run section).

### Claim-style feature list (illustrative)
- A method of forensic soil screening comprising extracting nucleic acids from a soil sample associated with a search sector, amplifying a human-specific marker, applying quantitative PCR quality-control rules including inhibition checks, and recording a pass/fail result into a SAR case timeline.
- The method of above, further comprising, only after human-marker validation on a spiked-soil panel, amplifying a canine-specific marker on subsequent samples with the same QC path.
- A system comprising a portable amplification device and a computer configured to refuse reporting a remote-sensing anomaly as a biological detection without an associated soil QC record.

---

## Prior-art search (verified links and numbers only)

Searches used: [Google Patents](https://patents.google.com/), USPTO Patent Public Search / Patent Center via Google Patents bibliographic pages, and published papers (DOI/NTRS/PMC). **Only patents whose Google Patents pages returned HTTP 200 with matching numbers are listed.** This is a **preliminary** search, not a freedom-to-operate or patentability opinion.

### Concept 1 — shallow / phone radar

| Prior art | Link | How Concept 1 differs |
|---|---|---|
| **US11580725B2** (Vayyar) — RF array imaging in/behind media; mobile pairing; wall studs/pipes | https://patents.google.com/patent/US11580725B2/en | Consumer/pro **wall imaging** + DAS energy thresholds. Evans focuses on **SAR field logging contract**, Pi host + GPS evidence chain, and **honest mmWave vs MHz GPR ladder** into a case timeline—not DAS wall visualization claims. |
| **US9696421B2** (SRC) — through-wall sensing using Wi‑Fi/cellular radar on handheld/smartphone | https://patents.google.com/patent/US9696421B2/en | Uses phone radios as radar for **activity behind walls**. Evans uses a **dedicated USB/SPI radar board** + Pi logger for **range profiles / shallow GPR**, not Wi‑Fi entropy metrics. |
| **US7999722B2** — through-wall imaging device with antenna extensions | https://patents.google.com/patent/US7999722B2/en | Hardware form factor for through-wall imaging. Evans is a **SAR ops package** (GPS JSONL, preview, pipeline IDs), not that antenna geometry. |
| Commercial Walabot DIY (product; see Vayyar family) | https://walabot.com/products/walabot-diy-2 | Closed consumer UI; limited raw export; drywall-focused. Evans requires **raw export**, Pi logging, and SAR timeline integration. |

### Concept 2 — SAR change + lidar

| Prior art | Link | How Concept 2 differs |
|---|---|---|
| **US10895637B1** (BGA Technology) — UAV with GNSS + SAR + GPR to map buried manmade objects | https://patents.google.com/patent/US10895637B1/en | Airborne **contactless GPR+SAR+GNSS** object ID with calibration spectra. Evans is **orbital/VHR SAR pair change + terrestrial/USGS lidar DEM micro-relief**, separate add-ons, **no automatic buried-object ID**, band-honest metadata. |
| **US10578735B2** — multilook coherent change detection | https://patents.google.com/patent/US10578735B2/en | CCD processing patents broadly cover coherence change. Evans’ **980** stub implements known ratio/CCD math; novelty sought in **two-add-on SAR-triage product + interchange + band sidecars + ops timeline**, not CCD formulas alone. |
| Depoy / Shaw SPIE & thesis — UHF-SAR + lidar DEM to reject above-ground false alarms for buried munitions | https://doi.org/10.1117/12.921950 · https://corescholar.libraries.wright.edu/etd_all/676 | Military **UHF-SAR + lidar** fusion for IED/UXO. Evans targets **missing-person triage**, **separate** cues first, free S1/3DEP crawl, forbids X-band canopy myths. |
| Corcoran et al. (2018) terrestrial lidar elevation change at grave surfaces | https://doi.org/10.1016/j.forsciint.2018.05.038 | Closest **paper** on lidar micro-relief for graves. Evans combines that *idea class* with a **shipped Gi\* toolpath** and a **paired SAR change add-on** under one interchange—still no claimed detections. |

### Concept 3 — soil eDNA / burial chemistry

| Prior art | Link | How Concept 3 differs |
|---|---|---|
| **US11221292B2** (Univ. Akron) — in-situ NIR spectroscopy for fatty-acid salts from burials | https://patents.google.com/patent/US11221292B2/en | **Chemistry/NIR probe**, not nucleic acids. Evans is **DNA/eDNA + qPCR QC**, human-then-canine order, SAR timeline integration. |
| **US11725202B2** — soil DNA extraction (microbial; cTAB/humics) | https://patents.google.com/patent/US11725202B2/en | Microbial soil DNA workflow. Evans targets **human (then canine) forensic markers** and ops QC integration, not microbial community kits. |
| WO2000025108A1 — volatile gas combinations to locate corpses | https://patents.google.com/patent/WO2000025108A1/en | Gas sensors. Different modality from eDNA. |
| Emmons (2015) thesis — human mtDNA persistence in grave soil | https://trace.tennessee.edu/entities/publication/a52cb7b6-25e1-4bd2-89b3-152c00101c12 | Scientific prior art for recoverability. Evans’ disclosure is a **product ladder + QC + canine sequencing**, not the biological observation alone. |
| Hirashima et al. (2022) FSI — BSA/skim milk soil DNA extraction (abstract) | https://doi.org/10.1016/j.forsciint.2022.111284 | Extraction additive study. Inputs to crawl chemistry; not a SAR-integrated human→canine kit claim by itself. |
| Lang et al. (2023) — NanoSTR, STR detection from nanopore sequencing data | https://doi.org/10.3389/fmolb.2023.1093519 | Cited as STR-calling method literature (nanopore path). Not soil-specific; no claim of soil performance. |
| Butler (1998) MiMB 98 — capillary electrophoresis genotyping of STR loci (Springer protocol) | https://doi.org/10.1385/0-89603-443-7:279 | Standard CE STR protocol reference for the typing step. |
| *Ecological Indicators* (2025) — eDNA for soil health monitoring (review) | https://doi.org/10.1016/j.ecolind.2025.113438 | Soil eDNA methods/review background for sample prep; non-forensic scope. |
| Promega **Paradyme™ 27GY STR System** (product page) | https://www.promega.com/products/forensic-dna-analysis-ce/str-amplification/paradyme-27gy-str-system/ | Example commercial CE STR chemistry cited for the typing step; no endorsement or validation claim. |
| Ali & Rasheed (2024) JPMS 13(2):164–169 — soil factors and degradation of STR DNA from skeletal remains | https://doi.org/10.61091/jpms202413224 | Published soil-chemistry effect on STR recovery from remains; cited as background, not as our result. |
| Xu et al. (2026) *ACS Sens* — centrifugal microfluidic soil-to-DNA prep (Soil-on-a-Disc), CRISPR/Cas12a readout | https://doi.org/10.1021/acssensors.6c01885 (PMID 42859054) | Soil-to-DNA sample-prep format; target in the paper is a **plant pathogen**, not human DNA. |
| Linacre et al. (2011) — ISFG recommendations, non-human (animal) DNA in forensic genetics | https://doi.org/10.1016/j.fsigen.2010.10.017 | Governing recommendations for the later canine add-on. |
| Validation of two canine STR multiplex-assays following the ISFG recommendations (2013) | https://doi.org/10.1016/j.fsigen.2013.07.002 | Real published canine 13-STR panel cited for the canine add-on; not implemented here. |

---

## Top prior-art risks (summary for counsel)

1. **Highest (Concept 1):** Phone-paired RF wall imagers (**US11580725B2**, Walabot/Vayyar ecosystem) and phone Wi‑Fi through-wall (**US9696421B2**) are crowded. Risk that examiners treat “phone + radar accessory + GPS log” as obvious. Differentiation must emphasize **SAR evidence capture contract**, Pi host, and **band-limited depth claims**—and may need strong dependent claims on the logging schema / timeline join.
2. **Highest (Concept 2):** SAR coherent change (**US10578735B2** and large non-patent CCD literature) and SAR+lidar fusion for buried objects (**US10895637B1**, Depoy/SPIE) are strong. Pure math of log-ratio/CCD is **not** a safe novelty bet. Better bet: **two-add-on architecture + band-honest sidecars + missing-person triage UX** tied to labelled ROC—still a hard sell if described only as “fuse SAR and lidar.”
3. **High (Concept 3):** Burial detection by **NIR adipocere** (**US11221292B2**) and soil DNA extraction patents/papers mean **detecting remains via soil biology/chemistry** is known. Novelty likely limited to **specific assay+QC+human-then-canine+SAR workflow** combinations; biological facts (mtDNA in soil) are published (Emmons).
4. **Publication bar:** This private repo + commits help as **invention records**, but any public demo, conference talk, or open-sourcing **before** provisional filing can start clocks / destroy novelty in some jurisdictions. Keep private until filed.
5. **Abstract idea / natural phenomenon:** Software-only SAR math and naturally occurring DNA persistence face §101 / patent-eligibility scrutiny in the U.S.—another reason to involve counsel early.

---

## Next steps (process — not legal advice)

1. **Do not publish** these concepts (keep repo **private**; no public marketing that teaches the combination).
2. **Confirm current USPTO fees** on the official schedule before paying: [USPTO fee schedule (PDF)](https://www.uspto.gov/sites/default/files/documents/USPTO-fee-schedule_current.pdf). As of the schedule marked *Effective January 19, 2025 (Last Revised August 14, 2026)*, fee code **1005/2005/3005** — *Provisional application filing fee* — is **$325** (large) / **$130** (small entity) / **$65** (micro entity) under 37 CFR 1.16(d). Micro-entity requires certification (forms PTO/SB/15A or 15B) and meeting [micro-entity rules](https://www.uspto.gov/patents/laws/micro-entity-status).
3. **File a USPTO provisional** (or have counsel file) describing Concepts 1–3 with enough detail to support later claims; attach drawings of Pi wiring, capture directory layout, interchange schema, and assay ladder. Provisionals last 12 months.
4. **Counsel options:** hire a registered patent attorney/agent, **or** apply to the [USPTO Patent Pro Bono Program](https://www.uspto.gov/patents/basics/using-legal-services/pro-bono/patent-pro-bono-program) (regional eligibility; income and “more than an idea” requirements apply; inventors still pay USPTO fees).
5. After provisional: decide whether to pursue nonprovisional / PCT; budget search + exam fees separately (utility search/exam are **not** included in the provisional fee).
6. Continue technical reduction (kits, labelled panels) **under NDA** with collaborators; update this disclosure with new commit hashes when material improvements land.

---

## Document control

| Field | Value |
|---|---|
| Inventor (named) | Audrey Evans |
| Preparer | Internal SAR research note (registry 2040) |
| Branch | `sar-make-it-work` |
| Classification | Confidential — invention disclosure |
| Legal status | **Not legal advice.** Not a patent application. |

