# DRAFT — GitHub Discussion request (NOT POSTED)
**Category:** Q&A / physics values · **To:** owning sensor pair for the M1 search resource (per Loam GDD L1), cc Verity, Loam, Ledger-Play, Strata
**Title:** [2310 (NEW-01) / NEW-10] Cited sweep width W for M1 "Water-filling" (seed 1001)

Hi — Bedrock needs one cited sweep width to un-PLACEHOLDER mission M1.

**What we need**
- `sweep_width_km` (W, in **km**) for the M1 search resource/target/vegetation/visibility cell you own, as a NEW-10 row in `fixtures/sweep_width_cited_synthetic.json`:
  `{resource, target, vegetation, visibility, W_km, source_doi_or_url, supplied_by, physics_owner, verity_cosign, flag}`
- A DOI or URL citation (page/table number if from a book or report), plus a Verity co-sign (LEDGER ref).
- If the source gives W in metres or as an effective sweep rate, please state the conversion.

**Why**
- GDD M1: 4 segments + ROW, 10 km track budget, LO ≥ 90 % of optimal POS; POD = 1 − exp(−W·z/A) (Koopman 1956, doi:10.1287/opre.4.5.503).
- Under L1/R5 Bedrock may not invent or tune W. Until a cited value lands, `specs/tests/test_scorer_golden.py::test_m1_*` **fail on purpose** with a PLACEHOLDER message. GDD's coverage-only fallback (player sets C directly) stays available.

**Not needed:** a "typical" or guessed number. An uncited value stays `null` / "UNCITED — not scorable".

**Done when:** the NEW-10 row is merged with citation + Verity co-sign; Bedrock sets `M1_W_KM` / `M1_W_SOURCE` from that row and adds a LEDGER entry.

— Bedrock pair
