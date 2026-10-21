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

---

## Additional verified sources (added 2026-10-21)
Titles, authors and DOIs were checked against Crossref / PMC. Findings are the authors' own statements.
Blog and marketing pages (nanotechsci, climate.com, MIT Technology Review, MGI) and the pasted "game technology"
claims are **not** cited.

| Source | What it is | Use here |
|---|---|---|
| Domenech MB, Amiotti NM, Costa JL, Castro-Franco M (2020). *Prediction of topsoil properties at field-scale by using C-band SAR data.* Int J Appl Earth Obs Geoinf 93:102197. doi:[10.1016/j.jag.2020.102197](https://doi.org/10.1016/j.jag.2020.102197) (PII S0303243419311353) | 51 Sentinel-1 GRD scenes + Random Forest to predict topsoil properties on two Argentine Pampas fields; relates C-band backscatter to apparent electrical conductivity | Soil *properties*, not DNA. Context for the remote "Run" tier and SAR change (980): backscatter tracks soil state, so a soil-change anomaly needs a property baseline |
| Nagesh D, Kumari K, Tripathi A, Chittayil Raveendran V, Dalal J, Sekar P et al. (2026). *Intelligent Soil Analytics for Forensic Applications: Emerging Technologies, Trends, and Transformative Paradigms.* Engineering Reports 8(2):e70538 (Wiley). doi:[10.1002/eng2.70538](https://doi.org/10.1002/eng2.70538) | Review: nanobiosensors, DNA metagenomics for microbial fingerprinting, proximal/remote soil sensing, ML classification | Its ">90% classification accuracy" refers to studies it reviews, not to our use case. Do not quote it as a performance figure |
| Garg D, Patel N, Rawat A, Rosado AS (2024). *Cutting edge tools in the field of soil microbiology.* Curr Res Microb Sci 6:100226. doi:[10.1016/j.crmicr.2024.100226](https://doi.org/10.1016/j.crmicr.2024.100226) | Review of metagenomic sequencing methods in soil microbiology and their limits | Background for the necrobiome / microbial-fingerprint idea (canine and "blue-ocean" rows) |
| IAEA (2025). CRP **D12015** *Combining Gamma Ray Sensing and Digital Technology for Soil Moisture and Soil Property Mapping* (approved 13 May 2025; 2025–2030) <https://www.iaea.org/projects/crp/d12015>; news 7 Jul 2025 <https://www.iaea.org/newscenter/news/assessing-soil-with-gamma-ray-spectrometry-and-digital-technology>; Cheng Y et al., *Portable Gamma-Ray Spectrometry for Non-Invasive Soil Texture Mapping*, IAEA Soils Newsletter 48(1), Jul 2025 <https://www-pub.iaea.org/MTCD/Publications/PDF/p15962-snl48.pdf> | Gamma-ray spectrometry (K, U, Th) on fixed, mobile or drone platforms for texture, carbon, nitrogen and moisture. The newsletter reports R² 0.80 (silt) and 0.78 (clay) for a ²³⁸U model at their Austrian sites | Soil-texture and moisture baseline for interpreting GPR (1120) and soil-change layers. Not a remains detector |
| Zhao Y, Yavari K, Wang Y, Pi K, Van Cappellen P, Liu J (2022). *Deployment of functional DNA-based biosensors for environmental water analysis.* TrAC Trends Anal Chem 153:116639. doi:[10.1016/j.trac.2022.116639](https://doi.org/10.1016/j.trac.2022.116639) | Review of field deployment of functional DNA biosensors (aptamers/DNAzymes) for water | Water, not soil. Shows which field formats are mature enough to borrow |
| Billington C, Schmidt J, Mundle R, Prenner E, Pang L et al. (2023). *Comparative quantitation of DNA water tracers using OptiQ, Qubit, and Nanodrop.* Agrosyst Geosci Environ 6(1):e20344 (Wiley/ACSESS). doi:[10.1002/agg2.20344](https://doi.org/10.1002/agg2.20344) | Compares three **portable** DNA quantitation instruments | Authors: all three agree at high concentration. Qubit and OptiQ (fluorescent) had LODs of **0.1–2 ng/mL** vs **5×10³ ng/mL** for Nanodrop |
| Pang L, Abeysekera G, Hanning K, Premaratne A, Robson B et al. (2020). *Water tracking in surface water, groundwater and soils using free and alginate-chitosan encapsulated synthetic DNA tracers.* Water Res 184:116192. doi:[10.1016/j.watres.2020.116192](https://doi.org/10.1016/j.watres.2020.116192) | Synthetic DNA tracers tested in a stream, two aquifers and silt-loam lysimeters | DNA moves and persists differently by medium. Relevant to how far soil DNA could travel from a source (spiked-soil panel design) |
| Kumar V, Guleria P (2020). *Application of DNA-Nanosensor for Environmental Monitoring: Recent Advances and Perspectives.* Curr Pollut Rep (online 12 Dec 2020; Crossref lists 10(4):765–785). doi:[10.1007/s40726-020-00165-1](https://doi.org/10.1007/s40726-020-00165-1); PMC7732738 | Review of DNA nanosensors for pollutants | Background only; pollutant targets, not human DNA |
| Yoon H, Seo J, Shin S, Abdelhamid M, Pack SP et al. (2025). *Bioinformation and Monitoring Technology for Environmental DNA Analysis: A Review.* Biosensors 15(8):494. doi:[10.3390/bios15080494](https://doi.org/10.3390/bios15080494) | eDNA methods across air, soil, groundwater, sediment and water, including field-deployable detection | Up-to-date survey for the "Walk" tier (portable kits) |

### Field meter choice for the 2020 Pi kit
From Billington et al. (2023): for low-concentration DNA, a **fluorometer (Qubit or OptiQ class)** is the right field meter.
A UV-absorbance micro-spectrophotometer (Nanodrop class) was about three orders of magnitude less sensitive in their test.
So the Pi kit (`phone-gpr-addon.md`, 2020 / 811) should log a fluorometer's readings (manual entry or its export file)
alongside GPS and time, and must not treat a Nanodrop-style reading near zero as "no DNA". Caveats: their samples were
synthetic DNA tracers in water, not soil extracts. A fluorometer measures **total** dsDNA, not human DNA, so a human
result still needs qPCR (1300 QC). Re-check each instrument's own LOD with our extraction kit before relying on it.

## STR typing from soil samples

Literature and vendor sources only. Each entry was opened/verified on 2026-10-21 (America/Denver). **No performance or detection claims are made here**; these are citations for background reading.

### Sources

1. **NanoSTR: A method for detection of target short tandem repeats based on nanopore sequencing data.** Lang J, Xu Z, Wang Y, Sun J, Yang Z. *Frontiers in Molecular Biosciences* 10:1093519 (2023). DOI: [10.3389/fmolb.2023.1093519](https://doi.org/10.3389/fmolb.2023.1093519) · PMC: [PMC9889824](https://pmc.ncbi.nlm.nih.gov/articles/PMC9889824/) · PMID 36743210.
2. **Power of Short Tandem Repeat (STR) Analysis for Analysis of Genetic Differences and Genotype Identification.** Torres A, Gaudino R. In: Torres A (ed), *Genotyping*, Methods in Molecular Biology vol. 2943, Humana, New York (2025), chapter 13; online 29 June 2025. DOI: [10.1007/978-1-0716-4642-7_13](https://doi.org/10.1007/978-1-0716-4642-7_13). Covers DNA isolation (FTA cards or leaf tissue), PCR of STR regions, fragment analysis, and building a reference STR table. (Additional CE protocol references: Butler JM, *The Use of Capillary Electrophoresis in Genotyping STR Loci*, in *Forensic DNA Profiling Protocols*, MiMB vol. 98, Humana (1998), pp. 279–289 — DOI: [10.1385/0-89603-443-7:279](https://doi.org/10.1385/0-89603-443-7:279); and Hill CR, *Capillary Electrophoresis and 5-Channel LIF Detection of a 26plex Autosomal STR Assay for Human Identification*, MiMB vol. 830, Humana (2012) — DOI: [10.1007/978-1-61779-461-2_2](https://doi.org/10.1007/978-1-61779-461-2_2).)
3. **Environmental DNA as a tool for soil health monitoring and unveiling new ecological frontiers.** *Ecological Indicators* (2025), article 113438. DOI: [10.1016/j.ecolind.2025.113438](https://doi.org/10.1016/j.ecolind.2025.113438) · ScienceDirect: https://www.sciencedirect.com/science/article/pii/S1470160X25003681. Systematic review of 723 soil-eDNA papers (2001–2023).
4. **Paradyme™ 27GY STR System** (Promega product page; 8-dye multiplex, 23 autosomal STRs + 3 Y-STRs + Amelogenin + QIS/QIL, Cat.# RS2705 / RS2720). https://www.promega.com/products/forensic-dna-analysis-ce/str-amplification/paradyme-27gy-str-system/
5. **Studying the Role of Soil Factors on Degree of Degradation of DNA of Human Remains.** Ali SS, Rasheed MN. *Journal of Pioneering Medical Sciences* 13(2):164–169 (2024). DOI: [10.61091/jpms202413224](https://doi.org/10.61091/jpms202413224).
6. **Centrifugal Microfluidic Soil-to-DNA Preparation for the Portable Detection of *Phytophthora infestans* Using a CRISPR/Cas12a-Based Quantum Dot Fluorescent Lateral Flow Assay.** Xu C, Cao L, Li S, Ye W, Zhao J, Li X, Luo S, Zhang L, Liu G, Gao F, Wang Y. *ACS Sensors* (2026, online 10 Oct 2026). DOI: [10.1021/acssensors.6c01885](https://doi.org/10.1021/acssensors.6c01885) · PMID [42859054](https://pubmed.ncbi.nlm.nih.gov/42859054/). Note: the "Soil-on-a-Disc" chip in this paper is applied to a **plant pathogen** target, not human DNA; it is cited for the soil-to-DNA sample-prep format only.
7. **ISFG: Recommendations regarding the use of non-human (animal) DNA in forensic genetic investigations.** Linacre A, et al. *Forensic Science International: Genetics* 5(5):501–505 (2011). DOI: [10.1016/j.fsigen.2010.10.017](https://doi.org/10.1016/j.fsigen.2010.10.017).
8. **Validation of two canine STR multiplex-assays following the ISFG recommendations for non-human DNA analysis.** *Forensic Science International: Genetics* (2013); 13 STRs + 2 sex markers, repeat-based nomenclature, allelic ladders, 295 dogs (AT/DE). DOI: [10.1016/j.fsigen.2013.07.002](https://doi.org/10.1016/j.fsigen.2013.07.002). Later population data: CaDNAP 13-STR panel in 1,184 dogs — https://www.fsigenetics.com/article/S1872-4973(19)30181-4/abstract

### Workflow outline (plain research terms — proposed reading order, not validated)

1. **Sample prep.** Collect soil cores with blanks and spiked controls in the same batch; extract DNA with a soil kit or a microfluidic soil-to-DNA cartridge format (source 6); handle humic/inhibitor carryover explicitly. Background on soil eDNA method choices: source 3.
2. **Human-specific qPCR screen.** Run a published human-specific qPCR assay on each extract to decide whether anything downstream is worth attempting, and log every instrument export through the existing QC path (registry **1300**). Soil chemistry effects on recoverable human DNA: source 5.
3. **STR typing.** For extracts that pass the screen, type STRs either by a capillary-electrophoresis multiplex kit (protocol background: source 2; example commercial chemistry: source 4) or by nanopore sequencing with STR-aware calling (source 1).
4. **Canine STR panel — later add-on.** Only after the human path is validated, add a real published canine panel following the ISFG non-human recommendations (source 7) — e.g. the 13-STR canine multiplex validated against those recommendations (source 8) — reusing the same extraction and QC path.

No step above has been run on case or research soil in this project; nothing here asserts sensitivity, specificity, or recovery.
