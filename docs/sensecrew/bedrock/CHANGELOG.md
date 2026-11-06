# Bedrock changelog

## 2026-11-06

- CleanScorer (2310), Decision B (Discussion #28 comment 19445708; https://github.com/midnghtsapphire/forensicfinders/discussions/28#discussioncomment-19445708). `M1_W_KM` is `None` until a cited W exists (cited effective sweep width with Verity co-sign). `M1_W_SOURCE` cites that comment. Woolpert OH Statewide Phase 1 2019 B19, Table 2-4 (H = 2000 m AGL, FOV = 40°, stated swath 1.456 km) is geometric coverage only, not effective sweep width. M1 goldens score budget spend and geometric coverage. Coverage does not produce POD, POS, or a negative-evidence update. No path substitutes `0.9×swath` or any geometric fraction as W. `exponential_coverage_model` is a labelled model (`1 − exp(−C)` via `-math.expm1(-C)`, GDD v0.5 §4 / §4a) and is not M1 detection. NEW-10 / registry 2330 is not reused. Licence n/a.
