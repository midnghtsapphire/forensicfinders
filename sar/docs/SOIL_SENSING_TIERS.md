# Soil sensing: what "atomic-level" actually buys, and where each technique sits

**Who:** Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
**When:** 2026-10-24
**Why:** Sort the atomic-level soil-detection techniques by what they can actually do, and
place them against what this repository already has.
**What:** New file. Assessment only; no code changed.

---

## The thing that matters most

**You already built what you described, and it works on LiDAR.**

`blue-ocean-sar/realdata/microtopo.py` — M-TMAT. It differences two bare-earth DEMs from
different years, flags every cell whose change exceeds the level of detection, and
classifies each anomaly as **`excavation_pit`** (a drop) or **`fill_mound`** (a rise). It
writes a ledger, GeoJSON and KML with distance and bearing from a reference point.

That is "something is different and I don't know what it is", already implemented, already
tested. It does not care what caused the change. InSAR would **add** to this, not replace
it — and LiDAR has one advantage InSAR cannot match: it penetrates canopy, so forested
sites that defeat C-band interferometry are still reachable.

---

## "Atomic-level" means elemental analysis of a sample, not finding objects

This is the confusion worth clearing. In every source listed, "atomic" refers to measuring
**which elements are present in material you already have in hand or under the instrument**.
None of them locate a buried object from a distance.

| Technique | What it actually measures | Finds where to dig? |
|---|---|---|
| **LIBS** | elemental composition of material at the laser focus (mm to a few m standoff) | **No** — needs the sample |
| **Gamma-ray spectrometry** | natural radionuclides (K-40, Th-232, U-238) and Cs-137 in topsoil → soil properties | **No** — maps soil, not objects |
| **Nanosensors / quantum dots** | labelled analytes in a prepared sample | **No** — lab prep, research stage |
| **Magnetic induction spectroscopy** | buried **metallic** objects, handheld, in difficult soil | **Yes, for metal** |
| **GPR** | dielectric contrasts — voids, fill, disturbed layers | **Yes** |

So four of the five are confirmation tools. That is not a criticism — confirmation is half
the job — but they belong after a screening step, not instead of one.

---

## Three tiers, and what the repo already holds

| Tier | Job | Techniques | Already in repo |
|---|---|---|---|
| **1 Screening** — where to look | wide area, remote | LiDAR DEM differencing, InSAR, NDVI change, SAR change | `realdata/microtopo.py` (pit/mound), `geo_connectors/stac.py`, `realdata/s2_change.py` |
| **2 Ground survey** — narrow it on site | metres, on foot | GPR, magnetic induction, ground gamma | `gpr-wave-model/`, `instrument_input/` (GPR CSV, LAS), `sensor-fusion-grid/` (permittivity) |
| **3 Sample analysis** — what is it | the recovered sample | LIBS, qPCR/eDNA, GC-MS, 16S | `realdata/lab_readers.py` (GC-MS TIC + 16S), `realdata/qpcr_assay.py` (LOD95/LOQ, copies per gram), `qpcr_interpret.py` |

**Tier 3 already exists.** `lab_readers.py` reads real GC-MS and 16S exports and — per its
own docstring — replaced an app whose peak counts and abundances were typed in. The
atomic/molecular capability you are reaching for is partly built, and built honestly.

---

## What is genuinely missing, ranked

1. **Magnetic induction / EMI survey.** Nothing in the repo touches it. It is the one
   technique on the list that genuinely finds things, it complements GPR (metal vs. voids),
   and the hardware is cheap relative to everything else here. Caveat: metallic only — a
   buckle, zip, jewellery or casing, never remains themselves.
2. **LIBS reader.** Would slot beside `lab_readers.py` as another instrument export parser.
   Needs an actual instrument or a lab partner; the code is the easy part.
3. **Gamma-ray spectrometry.** Best use here is *context*, not detection: soil texture and
   moisture drive GPR velocity and eDNA preservation, both of which the repo already models.

---

## lasR — worth a look, with a licence flag

- C++ core, R package, and **`pylasr`, a Python API** (3.9+, build from source for now).
- Reads `.las/.laz/.copc.laz/.pcd`, does CHM, area metrics, decimation, multicore pipelines.
- Positioned as faster and more memory-efficient than lidR; single strong dependency on GDAL.
- **Licence: GPL-3** (bundled LASlib/LASzip are LGPL).

That last point needs a decision, not a shrug. GPL-3 is copyleft. Private internal use is
fine. If forensicfinders is ever distributed or sold, linking GPL-3 code has consequences
for the whole work. Worth settling before it gets woven in, not after.

---

## What I could not verify

- **IAEA gamma-ray page** — returned HTTP 402, could not read it.
- **Springer chapter 10.1007/978-981-97-4784-9_19** — paywalled behind an auth redirect.
  Send the title or abstract if it matters.
- **ScienceDirect S0584854718302039** — the ISSN (0584-8547) is *Spectrochimica Acta Part B:
  Atomic Spectroscopy*, so almost certainly LIBS, but I could not read the article.
- **Gamma sensing depth.** A search did not confirm a specific figure, so none is stated
  here. The physics bounds it to a shallow surface layer; the exact number needs a methods
  paper.
