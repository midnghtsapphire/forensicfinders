<!-- PROPRIETARY - ALL RIGHTS RESERVED. (c) 2026 Audrey Evans / Walter-Evans Forensic Intelligence Systems. Keep private. -->
# Retrospective Validation Protocol (run BEFORE filing)

## Blinding
1. A case officer who knows the resolved location writes truth.json and the
   SHA-256 seal (truth.sha256). The analyst running the system never opens it.
2. run_case() contains no code path that reads truth.*; validate() re-checks
   the seal hash before scoring and aborts on mismatch.
3. Score first, unseal second, reseal immediately.

## Metrics (pre-register these; do not shop for metrics after the fact)
- detection_rate at P>0.5 within 10 m of truth
- truth_rank in the deduped candidate list (report distribution, not just top-1)
- top1_error_m median/IQR
- false alarms per case at the operating threshold
- calibration: binned predicted P vs empirical hit rate (is 0.7 really ~70%?)

## Design targets
- >=20-30 resolved cases, spanning soil classes, climate, burial age, wrap type
- buried-pre-window cases counted separately (lidar is blind to them by design;
  they test the reports/dogs/nitrate layers, not the timeline layer)
- WRAP TYPE recorded: Pringle 10-year data shows GPR detectability diverges
  sharply (naked ~6y weak; wrapped 10y). Your sample must not confound this.

## Known synthetic-study finding to watch for in real cases
In the 3-case synthetic study: detection rate 1.0 but truth-in-top-3 = 0 -
detection is not prioritization. If real cases show the same pattern, the
fusion weights and the nitrate/report priors need recalibration per region.
