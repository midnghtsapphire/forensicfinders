# SenseCrew Fusion LEDGER (append-only)

## 2371 (provisional) — sensegame/fusion combine + anomaly
- who: Sense-Fusion (Fusion-D drive, Fusion-N review)
- why: Strata GO (2026-11-05 08:22 MST) to implement FUSION_SPEC v0.2 §2–§7 as a synthetic-only hint layer.
- sources: FUSION_SPEC v0.2 (PR #18 @ 6fb9960); Bedrock scorer-spec 2310 (docs/sensecrew/bedrock/specs/scorer-spec.md, PR #41 @ 8e745c6); Hampel (1974) JASA 69:383–393; Rousseeuw & Croux (1993) JASA 88:1273–1283; Li et al. ECOD (2022, IEEE TKDE); Zadrozny & Elkan (2002) isotonic calibration; Naeini et al. (2015) ECE; Efron & Tibshirani (1993) bootstrap.
- data: procedural synthetic scenes only (synth.py); no case/, hfmr/, dossier, evidence/, public-records, realdata/fusion.py, TerraMesh, TerraTorch, LUCAS, Ultralytics.
- licence: UNLICENSED (private repo; licence pending Audrey)
- review: see sensecrew/ledger for Fusion-N APPROVE (<sha>)

## 2371 — Decision B null-W (coverage and budget only)
- who: Sense-Fusion
- why: Proofy Option B. M1_W_KM is None until a cited W exists. Fusion must not invent W or score M1 as detection.
- sources: https://github.com/midnghtsapphire/forensicfinders/discussions/28#discussioncomment-19445708 ; Bedrock PR #41 @ 21774e2215ea07aadddac62a4085d841b488a401 (scorer-spec §4b, CleanScorer coverage/budget methods, M1 goldens; includes origin/main @ 2ef0d0afcfd98e604bfaae5d6655a8dccd8bae23, same tip as daily/2026-11-06).
- ruling: M1_W_KM is None until a cited W exists. M1_W_SOURCE cites that comment. Woolpert OH 2019 Table 2-4 (H = 2000 m, FOV = 40°, stated swath 1.456 km) is geometric coverage only. Surveyed is not detected. Coverage does not produce POD, POS, or a negative-evidence update. No path substitutes 0.9×swath, or any geometric fraction, as effective W. exponential_coverage_model is a labelled model (GDD v0.5 §4 / §4a) on player-supplied C and is not M1 detection. Registry 2330 untouched.
- data: no change to combine.py, anomaly.py, or synthetic fixtures. Fusion production modules do not set a numeric M1 width and do not call pod/pos/optimal/update.
- licence: UNLICENSED (private repo; licence pending Audrey)
