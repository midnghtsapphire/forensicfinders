# HySUPP comparison harness (NEW-22 / registry 2360)

*Who:* Grok Bot as Sense-Quartz (Quartz-N navigator, Quartz-D driver) for Audrey Evans · *When:* 2026-11-04
*Licence of our code:* `UNLICENSED (private repo; licence pending Audrey)`
*Confidence:* ~0.62 SUPPORTED (CONFIDENCE_FRAMEWORK engineering adaptation).

## What HySUPP is
HySUPP — "an open-source **Hy**per**S**pectral **U**nmixing **P**ython **P**ackage" (Rasti, Zouaoui,
Mairal, Chanussot, IEEE TGRS 2024, doi:10.1109/TGRS.2024.3393570). ~20 supervised, semi-supervised
and blind unmixing methods. We use it **only as a comparison reference**, never as a dependency of
the game client or of `multi_proxy`.

## Licence verification
- Repo: https://github.com/BehnoodRasti/HySUPP, **pinned commit `cb7d633a3b4a458504e31d1e5fcd3f6a00be688d`** (HEAD on 2026-11-04).
- `LICENSE` at that commit begins: *"MIT License — Copyright (c) 2023 Behnood Rasti — Permission is hereby granted, free of charge…"*. GitHub API reports `spdx_id: MIT`.
- **Licence risk (transitive):** `src/model/supervised/FCLS.py` (and SUnAA, AA, …) do `import spams`. The
  pinned `requirements.txt` pins `spams-bin==2.6.10`, whose wheel ships a **GPL-3.0** `LICENSE`
  (checked 2026-11-04). Also pulls `torch` for other methods. Therefore:
  - we **do not** vendor, submodule, or pip-install HySUPP or spams in this repo or CI;
  - the harness loads HySUPP only from a developer-local checkout via `HYSUPP_ROOT`, and the
    HySUPP test **skips** otherwise. Whether running it locally against GPL spams is acceptable
    is an open question for **Strata / Audrey** (not shipped, not distributed, but flagged).
- Repo is ~40 MB with datasets → not vendored regardless.

## How we compare
1. Endmembers: USGS splib07 PD fixture (`fixtures/splib07_subset/`, default first 3: quartz,
   kaolinite, montmorillonite); falls back to synthetic Gaussians if fixture is missing.
2. Abundances: seeded Dirichlet(1) draws (default seed `20261104`, 64 pixels); `Y = E·A + N(0, 0.005)`.
3. Methods: our `constrained_nnls_unmix` (always) vs HySUPP `FCLS` (optional).
4. Metrics: **abundance RMSE** vs known truth (primary); mean **SAM** (deg) of reconstruction (secondary).
5. Output: JSON-serialisable dict; identical for identical seed.

Current baseline (seed 20261104, splib07, noise 0.005): abundance RMSE **0.00867**, mean SAM **0.409°**.

## Run offline
```bash
cd sar/blue-ocean-sar
python3 -m multi_proxy.hysupp_compare          # baseline; hysupp_fcls -> "skipped"
python3 -m pytest -q multi_proxy/test_hysupp_compare.py
# optional, developer-local only, after Strata/Audrey OK on spams GPL-3.0:
#   git clone https://github.com/BehnoodRasti/HySUPP /path/HySUPP && git -C /path/HySUPP checkout cb7d633a
#   pip install cvxopt spams-bin   # into a throwaway venv, never into project requirements
#   HYSUPP_ROOT=/path/HySUPP python3 -m multi_proxy.hysupp_compare
```

## Out of scope / guardrails
No LUCAS, no case/hfmr/evidence/PII, no GPL/AGPL/Ultralytics deps, PySptools (Apache-2.0,
unmaintained) reference only — not a dependency. `registry.json` untouched.
