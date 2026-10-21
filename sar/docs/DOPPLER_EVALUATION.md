# Evaluation: `doppler_frequency_corrector.py` (Gemini Notebook)

**Verdict: doesn't belong in the SAR toolchain. Not imported, and no registry ID.**

## What it does
It predicts the Doppler shift of a satellite downlink (NOAA APT, Meteor-M LRPT, CubeSats) so that an SDR receiver can tune to it: `f_obs = f_c (1 - v_r / c)`.

## Problems found
1. **The radial velocity is invented.** `v_radial = v_orbital * sin(norm_t) * cos(0.3 * max_elev)` is a made-up curve. A real Doppler profile needs orbit propagation from current TLEs (SGP4) plus observer geometry, e.g. `skyfield` or `sgp4`. The formula gives the right sign and rough magnitude but the wrong shape and timing.
2. **The default observer location is a case-area coordinate** (privacy). It must never ship.
3. **No tests**, and nothing in the repo calls it.

## Why there's no SAR use
- Receiving NOAA APT or Meteor imagery yourself gives about 1–4 km pixels. The 900-series connectors already pull 10 m Sentinel-2, Sentinel-1 SAR and 3DEP lidar, which are orders of magnitude better for search.
- Doppler correction is a radio-reception chore, not an analysis step, and none of the search outputs depend on it.

## If it's ever wanted
Rebuild it on `skyfield` with a TLE input and test it against a published pass prediction. Keep it in a separate radio-tools repo.
