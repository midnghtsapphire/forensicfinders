# RECORD — Decision B (local; NOT a GitHub post)

**Status:** decided. Do not post this file.
**Authoritative comment:** https://github.com/midnghtsapphire/forensicfinders/discussions/28#discussioncomment-19445708
**Title:** [2310 (NEW-01) / NEW-10] M1 stays coverage-and-budget only; M1_W_KM is None until a cited W exists

Proofy Option B is in force. Strata's constraints supersede any reading of the GDD v0.5 §4 / §4a coverage fallback that would turn a geometric swath, or `1 − exp(−C)` applied to that swath, into M1 detection.

**What is true now**

- `M1_W_KM` is `None` until a cited W exists: a cited effective sweep width (∫ p(x) dx) with Verity co-sign. None is cited today.
- `M1_W_SOURCE` cites the Decision B comment above. It is not a numeric width.
- Geometric footprint only: Woolpert OH Statewide Phase 1 2019 B19, Table 2-4, H = 2000 m AGL, FOV = 40°, stated swath 1.456 km. That number is surveyed footprint, not effective W, and it is not written to `M1_W_KM`. `0.9 × 1.456` km and every other geometric fraction are also not W.
- M1 scoring is coverage and budget only. Surveyed is not detected. Coverage does not produce POD, POS, or a negative-evidence update.
- `exponential_coverage_model(C) = 1 − exp(−C)` (`-math.expm1(-C)`) may exist for a player-supplied dimensionless C (GDD v0.5 §4 / §4a). It is a **model**, not calibrated detection, and M1 goldens do not call it.
- The Koopman path remains for a cited effective W. With `w_km is None`, `pos` / `optimal` / `update` raise `UncitedSweepWidth` and do not substitute.
- NEW-10 (registry 2330) stays null. Do not reuse 2330. Do not add a NEW-10 row whose `W_km` is 1.456 or any stand-in for it.

**Not in force:** filling `M1_W_KM` from the stated 1.456 km swath, from any fraction of it, or from an uncited "typical" width.

**When a cited W exists** (effective sweep width with Verity co-sign), `M1_W_KM` can leave `None`. This record does not supply that citation.

— Bedrock pair
