# Detecting small buried or surface personal items

**Registry ID: 2070** · **Status: PROTOTYPE / RESEARCH** · No results are claimed.

Targets: metal zippers, rivets, buttons, synthetic fabric, shoe soles. These are small, often
partly non-metallic, and near the surface. Below are the sensing methods with the published
forensic geophysics we can cite. Every DOI was checked against Crossref on 2026-10-21.

## Methods and forensic literature
| Method | Fits which items | Source |
|---|---|---|
| Review of all methods | Search planning, method choice by target and ground | Pringle, Ruffell, Jervis et al. (2012) *The use of geoscience methods for terrestrial forensic searches.* Earth-Science Reviews 114:108–123. doi:[10.1016/j.earscirev.2012.05.006](https://doi.org/10.1016/j.earscirev.2012.05.006) |
| Metal detector | Zippers, rivets, metal buttons, eyelets | Rezos, Schultz, Murdock et al. (2010) *Controlled research utilizing a basic all-metal detector in the search for buried firearms and miscellaneous weapons.* Forensic Sci Int 195:121–127. doi:[10.1016/j.forsciint.2009.12.003](https://doi.org/10.1016/j.forsciint.2009.12.003) |
| Magnetometry / magnetic susceptibility | Ferrous fittings; disturbed soil | Pringle, Giubertoni, Cassidy et al. (2015) *The use of magnetic susceptibility as a forensic search tool.* Forensic Sci Int 246:31–42. doi:[10.1016/j.forsciint.2014.10.046](https://doi.org/10.1016/j.forsciint.2014.10.046) |
| GPR | Larger buried items and disturbed fill; small items only at high frequency and shallow depth | Schultz (2007) *Using ground-penetrating radar to locate clandestine graves of homicide victims.* Homicide Studies 11:15–29. doi:[10.1177/1088767906296234](https://doi.org/10.1177/1088767906296234); van Schoor et al. (2017) *A controlled monitoring study of simulated clandestine graves using 3D GPR.* Near Surface Geophysics 15:274–284. doi:[10.3997/1873-0604.2017007](https://doi.org/10.3997/1873-0604.2017007) |
| Search protocols (hidden objects) | Objects under floors and in walls | Ruffell, Pringle, Forbes (2014) *Search protocols for hidden forensic objects beneath floors and within walls.* Forensic Sci Int 237:137–145. doi:[10.1016/j.forsciint.2013.12.036](https://doi.org/10.1016/j.forsciint.2013.12.036) |
| Multispectral / hyperspectral | Surface disturbance and vegetation stress, not items directly | Kalacska & Bell (2006) *Remote sensing as a tool for the detection of clandestine mass graves.* Can Soc Forensic Sci J 39:1–13. doi:[10.1080/00085030.2006.10757132](https://doi.org/10.1080/00085030.2006.10757132) |
| Lidar (micro-relief) | Ground disturbance, not small items | See `full-waveform-lidar.md` (2060) and `vhr-radar-lidar-fusion.md` (2030) |
| Thermal | Surface items with different emissivity or heat capacity than soil (e.g. synthetic fabric, rubber soles) | Covered in the Pringle et al. (2012) review. We found no controlled forensic study specific to clothing items, so this is an open question. |

## Adjacent sources only (not detection studies)
These describe how clothing materials look to *other* sensors. They are not field detection evidence.
- Montusiewicz, Miłosz, Kęsik, Żyła (2021) *Structured-light 3D scanning of exhibited historical
  clothing — a first-ever methodical trial and its results.* npj Heritage Science / Heritage Science.
  doi:[10.1186/s40494-021-00544-x](https://doi.org/10.1186/s40494-021-00544-x). Museum scanning of garments.
- Żyła, Kęsik, Santos, House (2021) *Scanning of Historical Clothes Using 3D Scanners: Comparison
  of Goals, Tools, and Methods.* Applied Sciences 11(12):5588. doi:[10.3390/app11125588](https://doi.org/10.3390/app11125588).
- Rentz, Malone, Vettiyil, Sillaste et al. (2024) *New Perspectives for Estimating Body Composition
  From Computed Tomography: Clothing Associated Artifacts.* Academic Radiology.
  doi:[10.1016/j.acra.2024.01.013](https://doi.org/10.1016/j.acra.2024.01.013). Shows zippers, buttons
  and similar items show up as artifacts in medical CT.
- ISCD DXA Atlas: <https://iscd.org/learn/resources/dxa-atlas/>. Reference images that include
  clothing and external artifacts in DXA scans.

## Near-surface imaging: what a security scanner can and cannot tell us
- **News source:** Stephen Chen, *Chinese body scanner can see through 30 layers of clothing using space tech*,
  South China Morning Post, 13 Jan 2022 (22:30 HKT).
  <https://www.scmp.com/news/china/science/article/3163290/chinese-body-scanner-can-see-through-30-layers-clothing-using>.
  The article says "space radar technology" (synthetic aperture), a mirror-sized unit with 32 small antennas,
  millimetre-level resolution, and a printed "S" still identifiable through up to 30 garment layers. It names
  Prof. Liu Jinsong's team at Huazhong University of Science and Technology and a paper in *Optics and
  Optoelectronic Technology*.
- **Underlying paper (found by title/authors; no DOI located):** Hong Weitao, Chen Hanjiang, Zhang Ze, You Chengwu,
  Liu Jinsong, Wang Kejia, Yang Zhengang (2022). 毫米波步进频连续波SAR成像系统研究 (*Research on a millimetre-wave
  stepped-frequency continuous-wave SAR imaging system*). 光学与光电技术 (Optics & Optoelectronic Technology)
  2022(01):58–64. Abstract mirror: <https://journal.yuanpingjia.com.cn/Journal/ArticleDetails/696607>.
  **Technology: millimetre-wave SFCW SAR, not terahertz.** The abstract does not state the band. It reports
  resolution of about 8–9 mm (x), 12 mm (y) and 40 mm (z), a best imaging range of **5–16 cm** from the antennas,
  and penetration of five common fabrics "at normal clothing thickness".
- **Relevance:** it shows mmWave SAR can image small, mm-scale contrast through dry textiles. That fits the
  *surface* case: a zipper, rivet or button under leaf litter or a garment, scanned at close range.
- **Limits for buried items:** clothing is thin, dry and low-loss. Soil is not. Moist soil has much higher
  permittivity and conductivity, so attenuation at tens of GHz rises steeply and depth falls to millimetres
  or centimetres. The 5–16 cm stand-off and the 40 mm range resolution also mean a handheld scan right on the
  ground surface. Treat this as evidence for dry-surface or litter-covered items only. Deeper burial is GPR work
  (hundreds of MHz to a few GHz; see the GPR rows above and 1120). We make no claim that this system works on soil.

## Matching a found item to public unsolved-case listings (lookup-table design only)
**Sources**
- **The Suitcase Detective — *Searchable Database of Personal Items for Unsolved Cases*.**
  <https://thesuitcasedetective.com/searchable-database-of-personal-items-for-unsolved-cases/> (page dated 8 Jul 2025).
  This is the personal-items table of *Never Quit Looking*, which the site's terms describe as "a section of The
  Suitcase Detective … not a separate legal entity, investigative agency, law enforcement agency, or official tip
  line". The Suitcase Detective calls itself an independently operated mystery and true-crime website. It is
  **not** an official source. Each item row links to the case record in the main Never Quit Looking database.
  - **Fields shown:** Photo, Description, Victim Identity (name, Record ID, Status: Missing Person / Unidentified /
    Unidentified Remains), Category (Clothing, Jewelry, Tattoo, Vehicle, Possessions (Other)…), Color, Year,
    Brand or Make, Specific Type, Design, Location (Tattoo), Name.
  - **Terms** (<https://thesuitcasedetective.com/about/terms-conditions/>): a limited, non-commercial use
    licence. Prohibited uses include "Scrape, crawl, or systematically extract content using automated tools",
    redistribution, derivative works, and framing or mirroring. Permission requests go to the address listed in
    the terms. Their disclaimer says to verify details with official sources. (Their robots.txt allows all
    crawlers, but the terms still forbid scraping, so we follow the terms.)
- **NamUs** (National Missing and Unidentified Persons System, NIJ / U.S. DOJ): <https://namus.nij.ojp.gov/>.
  Unidentified-person case pages include clothing and personal-effects details. I did not find a terms-of-use
  page at a predictable URL on 2026-10-21. Until one is read, use manual search only and store case URLs.

**Design (no scraping, links only)**
- `sar/data/item_lookup.csv` (future; not created here) holds *our* scene items and *pointers*, never copied listings:
  `scene_item_id, category, color, brand, specific_type, design_note, source (suitcase|namus), case_url,
  case_record_id, checked_by, checked_at, match_strength (none|weak|possible), note`.
- A person searches each site by hand using the site's own filters (category, color, brand, type) and pastes
  the URL and record ID. No photos, descriptions or names are copied into the repo.
- `match_strength` is an analyst label for triage, never an identification. Any "possible" goes to the agency
  that owns the case (NamUs case contact, or police for Never Quit Looking entries), not to the public.
- Before any automation, get written permission from The Suitcase Detective and read the NamUs terms. Until then, all lookups are manual.

## Roadmap (start simple)
1. **Crawl:** a hand metal detector over a labelled test strip of zippers, rivets and buttons at
   0, 5, 10 and 20 cm. Log hits and misses with GPS. The aim is a written detection table, not a claim.
2. **Walk:** add a magnetometer or susceptibility meter and a high-frequency GPR line over the same strip;
   add synthetic fabric and a rubber sole to see what the non-metal items show, if anything.
3. **Run:** thermal and multispectral drone passes over the strip at dawn and midday; only then
   think about fusion with 2030/2060 terrain layers.
