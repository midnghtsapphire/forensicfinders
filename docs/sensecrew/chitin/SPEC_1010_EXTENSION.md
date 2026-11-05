# SPEC — Chitin extension of registry 1010 (forensic_models/taphonomy)
Licence: UNLICENSED (private repo; licence pending Audrey) · Sense-Chitin · 2026-11-04 · Verity CLEAR 0.86

## Status
- **No new registry id.** Parent = **1010** (`forensic_models/taphonomy.py`), registered on `sar-make-it-work` (commit 1117fed), **not on main**. main's `sar/registry.json` has no 1010; we do NOT add it here — it lands when that component merges.
- Cleared files: `sar/forensic_models/taphonomy.py`, `sar/docs/research/INSECT_TRACES.md` (the latter is registry 2210 research note).
- `taphonomy.py` imports `.constants` (`load`, `value`) which reads `constants.json`. Those are **not** in the cleared set, so this PR does **not** check out taphonomy.py (it would not import standalone). No forensic_models siblings pulled.

## Interface observed (origin/sar-make-it-work)
`topp_theta(eps, consts=None)`, `topp_eps(theta, consts=None)` (0≤θ≤0.55), `megyesi_add(tbs, consts=None)` (TBS 3–35 → add, low, high), `accumulated_degree_days(daily_mean_c, base_c=0.0)`, `vass_pmi(decomposition_pct, temp_c, humidity_pct, buried=False, consts=None)`, `saponified_fraction(years, consts=None)`.

## This PR
- `sar/insect-trace-add-sim/insect_trace_add_sim/decay_taphonomy_bridge.py`: tries `from forensic_models import taphonomy`; else a **synthetic stub** with identical signatures (pure `accumulated_degree_days` implemented; constant-dependent functions raise `NotImplementedError`). `decay_hook(run)` cross-checks 2350 ADD vs 1010 ADD and records clamped soil VWC.
- Soil hooks in 2350: VWC validated (finite real), clamped 0.0–0.5 (inside Topp's 0–0.55 fit range), logged as `soil_moisture_vwc_input/_clamped`; moisture→ADD modifier is identity (no cited effect adopted).

## Production path
When 1010 (+ its constants loader) merges to main, the bridge imports the real module automatically (`backend_name()` → `forensic_models.taphonomy`); stub-only assertions are skipped. Then Chitin may wire `topp_theta` (soil permittivity→VWC) into the 2350 soil input and `megyesi_add` as a TBS cross-check. Insect thresholds remain synthetic.
