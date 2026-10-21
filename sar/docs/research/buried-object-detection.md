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

## Roadmap (start simple)
1. **Crawl:** a hand metal detector over a labelled test strip of zippers, rivets and buttons at
   0, 5, 10 and 20 cm. Log hits and misses with GPS. The aim is a written detection table, not a claim.
2. **Walk:** add a magnetometer or susceptibility meter and a high-frequency GPR line over the same strip;
   add synthetic fabric and a rubber sole to see what the non-metal items show, if anything.
3. **Run:** thermal and multispectral drone passes over the strip at dawn and midday; only then
   think about fusion with 2030/2060 terrain layers.
