# Decode injection: where it goes, and why

**Who:** Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
**When:** 2026-10-24
**Why:** Record the design behind `sar/decode_hooks.py` so the next person does not have to
reconstruct it, and so proposals can be placed without re-arguing the architecture.
**What:** New file. Describes the three decode tiers, the rules that assign work to each,
and what can and cannot run in this repository today.

---

## The answer first

"The encoding/decoding layer" is **not one layer here. It is three**, at different distances
from the sensor. A correction belongs at the tier whose physics it matches. Most of the
trouble so far has come from aiming everything at a single point.

| Tier | Where in this repo | Payload it sees | What belongs here | Status |
|---|---|---|---|---|
| **0 — raw signal** | *does not exist* | complex IQ `s_r(τ, t_a)`; photon histograms | range compression with matched filter `h*(τ)`, guard-band noise floor `P_N`, NSR, anything phase-preserving | **Not reachable.** Needs Sentinel-1 SLC (CDSE) or GEDI L1B |
| **1 — product decode** | `decode_hooks` via `read_cog_window`, `read_points`, `read_gpr_csv` | one window of a raster; one point list; one trace list | per-pixel radiometric scaling, no-data masking, unit conversion, incidence-angle normalisation, GPR time-zero / dewow, provenance stamping | **Built.** Identity until a hook registers |
| **2 — analysis** | `stac.ndvi`, `delta_ndvi`, `log_ratio_db`, `anomalies`, `realdata/*` | two or more decoded arrays, or a whole scene | anything comparing acquisitions, anything needing scene statistics | Exists already |

---

## Three rules that decide the tier

**1. One payload.** A decode hook is handed exactly one payload. ΔNDVI and the S1 log-ratio
need *two* acquisitions, so they cannot be decode hooks. They are tier 2, permanently.

**2. One window, not one scene.** `read_cog_window` reads the bbox, not the image. Any
correction that estimates statistics — histogram stretch, Lee filter variance, sigma
thresholds — computed inside that window is biased by the window and will change when the
bbox changes. Those go to tier 2, or the scene statistics must be passed in explicitly.

**3. No phase at tier 1.** Sentinel-1 GRD is detected and multi-looked; its phase was
discarded before the file was written. Nothing registered at tier 1 can recover it. This is
the rule that rules out most of what has been proposed.

---

## Where the existing proposals actually land

| Proposal | Correct tier | Runs today? |
|---|---|---|
| NSR / FiLM injector (PDF §1.3) | 0 | No — no raw IQ reaches this repo |
| Ryberb phase kernel (QPI-RDI) | 0 | No — and it fails its own unit test (73.4 dB → 3.8 dB) |
| TAI leap-second sync | 1, metadata path | Partly — see below |
| Freeman–Durden / Pauli PolSAR | 2 | No — needs the full complex scattering matrix; S1 GRD gives detected VV/VH only |
| Lee speckle filter | 2 (needs scene statistics) | Yes, on a full read |
| FFT notch hotspot detector | 2 | Yes |

The PolSAR row is worth dwelling on: **this repo cannot do polarimetric decomposition at
all today**, regardless of whose implementation is used, because no fetched product carries
`hh`/`vv`/`hv` as complex values. That needs full-pol data (RADARSAT-2, ALOS-2), which is
not wired.

---

## TAI: what it actually buys, and what it does not

The 7,500 m azimuth figure applies to geolocating **raw** data from orbit state vectors.
GRD and L2A products arrive already geocoded by the provider, using correct time. So TAI
sync here **does not fix geolocation**. Saying it does would be a marker nobody checks.

What it does buy is real: correct Δt between acquisitions, which feeds change-detection
intervals and the eDNA decay clock. Worth doing, worth not overselling.

Concrete gap: `stac.summarize()` passes `properties["datetime"]` straight through as a
string, and nothing decodes it anywhere. That is the place to fix it — decode once, carry
both the parsed time and TAI nanoseconds in `meta`.

---

## The seam contract

```python
decode_hooks.register(name, fn, decoders=["read_cog_window"])   # scope it
# fn(payload, meta) -> payload
```

- Hooks run in **registration order**; a despeckle after a calibration stays after it.
- **Scope every hook that assumes a payload type.** Unscoped hooks run at every decode
  point, which is right only for type-agnostic work (stamping, logging, counting). A numpy
  hook handed a list of tuples is the defect scoping exists to prevent.
- A failing hook **aborts the decode**. It is not skipped — skipping returns data that
  looks conditioned and is not, and the caller cannot tell.
- `meta["decode_hooks_applied"]` records what **ran**, not what was installed.

---

## Wiring the receipt into the evidence chain

`run_sectors` already writes JSON per sector. The receipt should go in it, so the custody
record states what conditioned the data rather than leaving it implied.

Use `evidence/core.py:canonical()` for any hashing — `sort_keys` **plus**
`separators=(",", ":")`, `ensure_ascii=False`, `allow_nan=False`. A bare
`json.dumps(..., sort_keys=True)` produces different bytes and a digest that will not match
the existing chain.

---

## Next, in order

1. **Decode acquisition time in `summarize()`** into the tier 1 metadata path. Small, testable, real.
2. **Carry the receipt into `run_sectors` output** and on into the evidence chain.
3. **Give Lee and the FFT notch a tier 2 home**, operating on full reads.
4. **Then Route B** — an S1 SLC fetch from CDSE. That, and only that, creates a real tier 0
   with real input for the injector in the PDF.

## Do not

- Register a value-changing hook without `decoders=`.
- Put cross-acquisition maths in a decode hook (rule 1).
- Use the acronym **NSR** until it is settled. Two incompatible definitions are in play:
  *Normalized Signal-to-Noise Ratio* (PDF §1.1, the FiLM parts) and *Nanometer /
  Sub-millimetre Spatial Resolution* (later note). Pick one and say which in this file.
