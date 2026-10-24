# Q2: InSAR — measuring ground displacement for cold cases

**Who:** Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
**When:** 2026-10-24
**Why:** Audrey specified InSAR (interferometric phase / displacement), not coherent change
detection. The distinction decides which cases are reachable and which tools apply.
**What:** Replaces the earlier CCD-framed draft of this file. Plan only; no code changed.
**Note:** The NSR naming question is dropped at Audrey's instruction and is not pursued here.

---

## InSAR vs CCD — and why your correction matters for COLD cases

Both read the same complex SLC pair. They use different halves of it.

| | Uses | Tells you | Needs |
|---|---|---|---|
| **CCD** | coherence magnitude \|γ\| | *scatterers rearranged* — disturbance, no measurement | images **bracketing the event** |
| **InSAR** | interferometric **phase** ∠γ | *ground moved N mm toward/away from the sensor* | a stack; the event can predate it |

For a cold case this is decisive. CCD needs imagery from before and after the disturbance.
Sentinel-1 only launched in 2014, so a 2006 case has no S1 bracket at all.

InSAR does not have that constraint. Excavated and refilled soil **compacts and subsides
for years afterwards**. A time series built from a recent stack can measure that ongoing
differential settlement regardless of when the ground was disturbed. That is why your
correction is the right one for this work.

---

## The honest limits — read before committing time

**1. Terrain decides whether this works at all.** C-band InSAR holds coherence over bare
rock, arid ground and built surfaces. Over grass, crops and forest it decorrelates in days
to weeks. PSI needs persistent scatterers, which are essentially man-made structures.

| Case type | InSAR outlook |
|---|---|
| Paved / urban / sub-pavement | plausible |
| Arid, bare, rocky | plausible |
| Pasture, cropland | marginal, seasonal |
| Forest, alpine, snow-covered | very poor — this rules out alpine sites |

**2. Dilution.** A grave is 1–2 m. Sentinel-1 IW resolution is ~5 × 20 m, and multi-looking
makes the effective cell larger. Any subsidence signal is averaged across a pixel mostly
made of undisturbed ground.

**3. Magnitude.** Grave subsidence is centimetres over years. PSI line-of-sight precision is
millimetres *on good scatterers*, far worse on distributed ones. This sits near the limit,
not comfortably inside it.

**Conclusion:** InSAR is a **screening and corroboration layer over favourable terrain**,
not a detector. That is exactly the role `sensor-fusion-grid` exists to fill — it already
produces "a weighted anomaly index on a 0-100 scale, not a calibrated probability".

---

## Your links, sorted

Three of the seven are SAR interferometry. Three are astronomy or optics interferometry —
they share the word, not the technique.

| Link | What it is | Use here |
|---|---|---|
| **pygmtsar** (AlexeyPechnikov) | Python InSAR for S1 SLC + bursts. Fetches SLC, DEM and orbits; interferograms, correlation, SBAS / PSI / PSI-SBAS; 3D viz. **BSD-3-Clause** | **Start here.** Free, does the whole chain |
| **InSARdev/core** | Successor ecosystem to PyGMTSAR. Per-burst S1 TOPS, also NISAR | **Check the licence.** `insardev` core is InSARdev-SAL-1.0 — *funded academic or professional use requires a subscription*. `insardev_pygmtsar` and `insardev_toolkit` are BSD-3. You just cut paid tooling; this would add some back |
| **MultiDEFusion** | Fuses GNSS + InSAR (DInSAR/SBAS/PSI) deformation series. MIT, Python | Downstream only — consumes displacement series. Relevant *after* you have InSAR output |
| OpenVLBI | **Astronomical** Very Long Baseline Interferometry | Not SAR. Won't read an SLC |
| LightPipes Michelson | **Optical** wave-propagation simulation | Not SAR |
| astronomy.me.uk list | Astronomy interferometry tools | Not SAR |

The astronomy and SAR families do share deep roots — aperture synthesis, correlation, van
Cittert–Zernike. The mathematics are cousins. The software is not interchangeable, and
chasing the astronomy tools would cost weeks for nothing.

---

## Plan

1. **PyGMTSAR on one favourable test site.** It fetches SLC, DEM and orbits itself, so there
   is no separate fetch layer to build first. Pick a site with known ground truth and
   favourable terrain before pointing it at a case.
2. **Validate against something known.** A documented subsidence feature, not a case. If it
   cannot see a known signal, it cannot see an unknown one.
3. **Export the displacement series**, then feed rate-of-subsidence into `sensor-fusion-grid`
   as an additional input alongside the existing four.
4. **Set `complex_slc` / `co_registered_epochs` from the real run** so
   `hfmr/evidence_engine.py:sensor_compatibility()` reports `insar: True` because it is.
   That gate is already written and nothing currently satisfies it.
5. **MultiDEFusion later**, only if GNSS or levelling data for the area exists.

## Decide before step 1

- **Which case or site first**, and is its terrain in the plausible row of the table above?
- **Subscription or not** — PyGMTSAR (BSD-3, free) or InSARdev core (subscription for
  professional use). The free path is complete; the paid one is newer.
