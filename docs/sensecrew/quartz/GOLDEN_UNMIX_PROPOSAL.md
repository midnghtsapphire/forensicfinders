# Golden unmixing tests — proposal (NEW-22 mineral-spectral-unmix)

- **Who:** Grok Bot as Quartz-N / Quartz-D, for Audrey Evans
- **When:** 2026-11-04
- **Licence:** UNLICENSED (private repo; licence pending Audrey)
- **Registry id:** NEW-22 (provisional, assigned by Strata; final number pending Verity)

## What
Golden tests that report unmixing error against **known** synthetic abundances for
`sar/blue-ocean-sar/multi_proxy/nnls_unmix.py` (FCLS-style NNLS) and `sam.py` (Spectral Angle Mapper).

## Step A (this branch)
`multi_proxy/test_nnls_sam_golden.py`: seeded (`default_rng(20261104)`) 6x7x16 cube from four
analytic endmembers (Gaussian absorptions on flat/ramp continua) mixed with Dirichlet abundances
plus sigma=1e-3 noise. Metrics/thresholds:

| Check | Threshold |
|---|---|
| Max abs abundance error, noise-free | < 1e-6 |
| Max abs abundance error, noisy | < 1e-2 |
| RMS residual, pure pixels (noisy) | < 3e-3 |
| SAM, matching reference | < 0.01 rad |
| SAM, mismatched reference | > 0.1 rad and > 10x match |

## Step B (next)
Replace the analytic stand-ins with a small committed subset of **USGS Spectral Library v7
(splib07)**, which is a US-Government public-domain work: Kokaly, R.F., et al., 2017, USGS
Spectral Library Version 7, USGS Data Series 1035, https://doi.org/10.3133/ds1035 (data:
https://doi.org/10.5066/F7RR1WDJ). Resampled to the test band set, same error report.

## Rule-7 audit
`nnls_unmix.py` imports only numpy and scipy.optimize.nnls; `sam.py` imports only numpy;
nothing under `multi_proxy/` references case/, hfmr/, dossier.py, evidence/,
public_records_engine.py, or any PII. No GPL deps, no Ultralytics, no LUCAS.
