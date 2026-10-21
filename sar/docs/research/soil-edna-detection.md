# Soil eDNA / decomposition-signature detection (PROTOTYPE / RESEARCH)

**Registry ID: 2000** · **Status: PROTOTYPE / RESEARCH** · No code claims, no results claimed.

Audrey's idea: detect human (then canine) DNA or decomposition chemistry in soil samples, and later look for landscape proxies from the air or from space. This note is a crawl → walk → run roadmap with published sources only.

Canine is an **add-on after human** is working, not a parallel first product.

---

## Crawl — what is already published

### Human DNA from soil and related matrices
| Finding | Source |
|---|---|
| Human mtDNA can be recovered from soil associated with buried remains; yields and persistence vary with soil type, moisture and time | Young, J. M., Rawlence, N. J., Weyrich, L. S. & Cooper, A. (2014). Limitations and recommendations for successful DNA extraction from forensic soil samples. *Science & Justice* 54(3):238–244. doi:[10.1016/j.scijus.2014.02.006](https://doi.org/10.1016/j.scijus.2014.02.006) |
| Environmental DNA (eDNA) methods for vertebrates in soil/sediment are established in ecology; transfer to forensic soil still needs assay validation | Taberlet, P., Coissac, E., Hajibabaei, M. & Rieseberg, L. H. (2012). Environmental DNA. *Molecular Ecology* 21(8):1789–1793. doi:[10.1111/j.1365-294X.2012.05542.x](https://doi.org/10.1111/j.1365-294X.2012.05542.x) |
| Forensic soil DNA extraction protocols and inhibition issues are well described | Young et al. (2014), above; see also MIQE reporting: Bustin, S. A. et al. (2009). The MIQE guidelines. *Clinical Chemistry* 55(4):611–622. doi:[10.1373/clinchem.2008.112797](https://doi.org/10.1373/clinchem.2008.112797) |
| Skim milk / BSA as additives can raise human DNA yield from soil-mixed blood/buccal/skin; BSA preferred for STR (skim milk introduced a non-specific peak) | Hirashima, H. et al. (2022). Development of an effective method of human DNA extraction from soil as forensic evidence. *Forensic Science International* 335:111284. doi:[10.1016/j.forsciint.2022.111284](https://doi.org/10.1016/j.forsciint.2022.111284) (abstract only; paywalled; PII S0379073822001141) |
| Human-specific mtDNA qPCR assays exist in the forensic literature (e.g. ND1/ND4 regions); each assay needs its own validation | Exemplars include Alonso, A. et al. (2004) Real-time PCR designs for quantification of nuclear and mitochondrial DNA; and subsequent forensic mtDNA qPCR papers. Use a peer-reviewed assay with published primers, not an ad-hoc design |

### Cadaver decomposition island (CDI) chemistry
| Finding | Source |
|---|---|
| Buried remains create a cadaver decomposition island: elevated nutrients (N, P), pH shifts, vegetation change | Carter, D. O., Yellowlees, D. & Tibbett, M. (2007). Cadaver decomposition in terrestrial ecosystems. *Naturwissenschaften* 94:12–24. doi:[10.1007/s00114-006-0159-1](https://doi.org/10.1007/s00114-006-0159-1) |
| Soil chemistry and microbial succession after burial are measurable over months–years | Benninger, L. A., Carter, D. O. & Forbes, S. L. (2008). The biochemical alteration of soil beneath a decomposing carcass. *Forensic Science International* 180(2–3):70–75. doi:[10.1016/j.forsciint.2008.07.001](https://doi.org/10.1016/j.forsciint.2008.07.001) |
| Adipocere formation and persistence are condition-dependent (moisture, anaerobic pockets, clay) | Forbes, S. L., Stuart, B. H. & Dent, B. B. (2005). The effect of the burial environment on adipocere formation. *Forensic Science International* 154(1):24–34. doi:[10.1016/j.forsciint.2004.09.107](https://doi.org/10.1016/j.forsciint.2004.09.107) |
| Accumulated degree days and burial PMI models exist but have wide error bands | Megyesi, M. S., Nawrocki, S. P. & Haskell, N. H. (2005). Using accumulated degree-days to estimate the postmortem interval from decomposed human remains. *J Forensic Sci* 50(3):618–626. doi:[10.1520/JFS2004017](https://doi.org/10.1520/JFS2004017); Vass, A. A. (2011). The elusive universal post-mortem interval formula. *Forensic Science International* 204(1–3):34–40. doi:[10.1016/j.forsciint.2010.04.052](https://doi.org/10.1016/j.forsciint.2010.04.052) |

**Crawl next small step:** pick one published human-specific mtDNA qPCR assay + one soil extraction protocol; run the existing `qpcr_qc` (1300) on synthetic standards first, then a blind soil panel with known spiked and blank samples. No field claims until that panel passes.

---

## Walk — portable field kits (research existing devices)

| Class | Examples (public products / papers) | Feasibility note |
|---|---|---|
| Portable qPCR | Biomeme Franklin / two3-style handheld thermocyclers with lyophilized assays ([Biomeme](https://biomeme.com/)) | Real devices used for environmental and some forensic-adjacent work. Assays still need human-specific validation in **soil**, not just clean matrix |
| Portable LAMP / isothermal | Multiple research and commercial LAMP readers; open literature on soil pathogen LAMP | Faster, often less equipment; still needs primer validation and inhibition controls |
| Nanopore sequencing | Oxford Nanopore MinION ([nanoporetech.com](https://nanoporetech.com/)) | Can sequence eDNA/metagenomes in the field. Species assignment from short/dirty reads needs a clear bioinformatics pipeline and false-positive controls |
| Phone-attached USB sensors | Various USB spectrometers / colorimeters used in DIY chemistry; not forensic-validated for CDI | Useful for turbidity/OD of extracts, not a DNA detector by itself |

**Walk next small step:** evaluate one portable qPCR or LAMP platform against the crawl assay on the same spiked-soil panel. Document LOD, inhibition rate and false positives. Keep results private until validated.

---

## Run — remote sensing add-ons (honest feasibility)

| Sensor idea | What the literature supports | Speculative / weak |
|---|---|---|
| Hyperspectral vegetation stress over CDI | Vegetation response to nutrient pulses is real in ecology; burial-specific spectral signatures are **not** a settled forensic product | Claiming "detect graves from hyperspectral" without a labelled training set is speculative |
| Thermal | Surface thermal anomalies from recent disturbance or differential moisture are sometimes reported; effect size vs background noise is often small | Not a standalone detector |
| Lidar / DEM change | Microtopography and canopy gaps from disturbance are measurable (we already have 3DEP + Gi* tools: 920, 1100) | Lidar finds **terrain change**, not DNA |
| Satellite NDVI / ΔNDVI proxies | ΔNDVI over seasons is real (we ship it: 910). Linking a pixel anomaly to a CDI without ground truth is an **hypothesis**, not a detection | Use only as a triage cue for where to sample soil |

**Run next small step:** for any candidate sector from 910/1100, plan a **soil sample grid** (crawl assay), not an automated "grave score" from pixels alone.

---

## Canine add-on (after human)

Dog-specific assays and canine eDNA exist in ecology (e.g. conservation studies of free-ranging canids). Sequence of work:
1. Human assay validated on soil.
2. Then add a published canine-specific marker with the same extraction and QC path (1300).
3. Do **not** train operators on canine-first field kits; that confuses the product and the chain of custody.

---

## Blue-ocean gaps (where published work is thin)
- Human mtDNA persistence curves for **Ozark / Midwest / alpine** soils under burial (most papers are site-specific).
- Blind proficiency tests that mix CDI chemistry + human eDNA + negative controls in one panel.
- Open, labelled hyperspectral/thermal datasets over **known** burials (almost none public).
- Cross-lab reproducibility of portable qPCR on inhibited soil extracts.

---

## Real today vs. speculative

| Real today | Speculative |
|---|---|
| Soil DNA extraction + inhibition handling (published) | "Phone app detects graves" |
| Human-specific qPCR assays (published; need soil validation) | Universal remote-sensing grave detector |
| CDI nutrient / pH / vegetation chemistry (published) | Satellite NDVI alone as proof of remains |
| Portable qPCR / MinION hardware exists | Plug-and-play field kit with courtroom-ready sensitivity out of the box |
| Our stack: 1300 qPCR QC, 910 ΔNDVI, 1100 terrain anomalies | Claiming any of those already "detects eDNA" |

---

## Data needed (before claiming anything)
1. Spiked-soil dilution series (known human DNA copies per gram) across at least two soil types.
2. True blanks: the same soils with no spike, processed in the same batch.
3. Time-series cores from a **research** burial facility or published open dataset (not active case soil).
4. Instrument export files for every run (feed 1300).
5. For remote sensing: labelled polygons of known disturbed vs undisturbed ground with dates.

**This document does not claim any detection performance.** Next engineering step lives under crawl above; code belongs in a future registry ID only after the spiked panel exists.
