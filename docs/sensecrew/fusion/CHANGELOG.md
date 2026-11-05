# SenseCrew Fusion CHANGELOG

## 2371 (provisional) — combine.py + anomaly/calibration — 2026-11-05
- Added `sar/sensegame/fusion/` per FUSION_SPEC v0.2 (PR #18 @ 6fb9960): `combine.py` (robust z, Hampel 1974 / Rousseeuw & Croux 1993; MAD=0 layers flagged degenerate + excluded, not zeroed; per-layer raw/normalised/weight/contribution per cell; grid-index cells only; lat/lon/address rejected; fixtures/*synthetic* path guard), `anomaly.py` (PyOD 3.6.7 ECOD, isotonic calibration, B=1000 seeded bootstrap via SeedSequence([seed,i]), ECE 15-bin gate ≤0.05 on synthetic holdouts, writer refuses unbanded scores), `run.py`, `__main__.py` CLI, `synth.py` procedural generator, synthetic fixtures (seeds 1002/1003 run, 2001–2010 calibration, 3001–3010 holdout).
- Makefile: `fusion`, `fusion-replay`, `fusion-test`. Outputs `out/fusion/<seed>/fusion_<seed>.json` (%.17g floats, sorted keys, no timestamps) + `uncertainty_map_<seed>.tif` (no CRS); `out/fusion/seeds.jsonl` append-only hash log.
- Depends on PR #41 (`sensegame/search_core.py`, NEW-01 = 2310). Hint layer only; never changes POA.
