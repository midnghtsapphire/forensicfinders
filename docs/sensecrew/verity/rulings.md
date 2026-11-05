# Verity gate rulings — 2026-11-04 (Sense-Verity, for lead Sense-Strata)
Repo: midnghtsapphire/forensicfinders (private). Licence: UNLICENSED (private repo; licence pending Audrey).
Method: read only the code that *references* forbidden paths; nothing under docs/case-files/, case/, hfmr/, evidence/, dossier.py or public_records_engine.py was opened.

## R1 — sweep_width.py: CLEAR (reference/adapter use), stays on the denylist until Strata turns NEW-11 on. Confidence 70
Evidence: `sar/blue-ocean-sar/realdata/sweep_width.py`
- L77-89 (comment): "...came from AI-generated documents ... (for example the "POD = 1 - exp(-S / w)" row, SMATH-002, in docs/case-files/CASE-X/sector_master_sar_database.db_1.txt ...) ... Those values were dropped. Every W here is null ("needs field calibration") unless it was traced to a named study"
- L94: `ROW_NAMES = {"row", "rest of world", "rest_of_world"}  # same convention as search_theory` (a string convention, not an import)
- Imports L68-73 are stdlib only. Optional h5py/rasterio at L382-410. No import of search_theory. No runtime read of any case-files path (`grep case-files` matches only the L81 comment).
Reasoning: the file names a case file only to say its values were **rejected**. No number, table or code is taken from it. That is a negative citation, not a derivation, so rule 7 ("use, import, read into training, ship") is not met. Residual risk: the comment names a case path (CASE-X) inside code that could ship. Condition: before shipping, Strata should replace the path with a deprecation note (an edit, not a deletion). Keep `sweep_width` on the `test_no_forbidden_imports` list until Strata explicitly enables NEW-11.

## R2 — search_theory.py: QUARANTINE confirmed. Confidence 85. optimal_search.py: QUARANTINE (transitive). Confidence 90
- `search_theory.py` L3-6 (docstring): "Built from the uploaded WiSAR field checklist and calculator workbook (docs/case-files/general/wisar_field_operational_checklist.pdf and wisar_bayesian_search_calculator.xlsx). It does the same arithmetic as the workbook". That is an explicit derivation from case-files.
- `optimal_search.py` L64-66: `sys.path.insert(0, ...)` / `import search_theory as st  # noqa: E402`.
- Note: the formulas (Koopman exponential detection model, Bayes POA update) are textbook public science. The clean-room NEW-01 CleanScorer built from published papers is the right fix, as Loam GDD v0.1 L40 says. Lower confidence on search_theory because the math itself is not proprietary; the taint comes from lineage and provenance.
- **Out-of-queue BLOCK flags (runtime reads of case-files):** `realdata/evidence_scoring.py` L102 `DEFAULT_SCHEMA = ...("case-files","general","sar_repository_schema.json")`; `test_evidence_scoring.py` L19 and `test_drift_envelope.py` L19 load `case-files/general/sar_case_records.json`. Docstring lineage: `lab_readers.py` L4, `fusion.py` L4, `field_log.py` L4, `drift_envelope.py` L3. None of these may be in the game path. Confidence 90.

## R3 — Licences
### lpb_mpb2003.json: BLOCK for ship/training until a licence is in hand. Internal reference only. Confidence 85
- Loaded by `lost_person_behavior.py` L43 `DATA_PATH = ...("lpb_mpb2003.json")`. `lost_person_sim.py` L153 `import lost_person_behavior as lpb`.
- Provenance (JSON `source`): Perkins, Roberts & Feeney (2003) *Missing Person Behaviour – An Aid to the Search Manager*, 1st ed., Centre for Search Research / Mountain Rescue (UK). Transcribed with pdftotext from an uploaded PDF (`294f303b-...-Handbook-June-2003.pdf`). It also contains US/Canadian tables "adapted ... from Hill (1997), Koester (2000) and Koester personal communication". Correction to the brief: the primary source is **not** Koester's *Lost Person Behavior* (dbS 2008), but it does embed Koester-derived tables.
- Licence: none in the repo (no LICENSE, SPDX tag or permission note; added in commit c944260, 2026-10-21). Web: the handbook is a copyrighted publication of the authors and the Centre for Search Research. It was distributed free by Mountain Rescue England & Wales (searchresearch.org.uk / mountain.rescue.org.uk). I found **no open licence or redistribution grant**. Koester data is dbS Productions copyright. UNVERIFIED: whether the authors grant reuse. Facts usually aren't copyrightable, but compiled tables can carry database rights in the UK/EU. Action: Audrey or Strata asks the Centre for Search Research for permission. Until then nothing in the game loads it (this matches Loam GDD v0.1 R3).
### cividis: CLEAR (permissive). Confidence 90
- Upstream: Nuñez, Anderton & Renslow (2018) PLOS ONE 13(7):e0199239. The paper is CC BY 4.0. Reference code is pnnl/cmaputil, verified LICENSE: "Copyright (c) 2017, Battelle Memorial Institute ... permission ... to redistribute and use ... with or without modification", BSD-style with notice retention and a no-endorsement clause (https://raw.githubusercontent.com/pnnl/cmaputil/master/LICENSE). Matplotlib ships cividis under the Matplotlib licence (PSF-style, permissive).
- Obligation: keep the Battelle copyright notice and disclaimer in `palettes/LICENSES/`, and don't use the Battelle name for endorsement. cividis is not used anywhere in the repo today (`git grep -i cividis` on all branches: 0 code hits, only the PR #13 doc).

## R4 — PR reviews (COMMENT only)
### Forbidden-imports test status: NOT PRESENT. Confidence 95
No `test_no_forbidden_imports` exists on any branch. It is only specified in prose (GDD v0.2 L42, balance v0.2 D4 L13). Verity prototype: `proto_test_no_forbidden_imports.py` here (AST scan + sys.modules diff). Result: fails on `sweep_width` and on `optimal_search` (pulls in `search_theory`), as intended. A per-module self-import check of `search_theory` gave a false pass because a previous test had already put it in sys.modules. The real test must scan the **game harness's** import graph in a fresh subprocess, not import the denied modules themselves.

### PR #10 (Loam GDD v0.3, draft → main)
> Verity (COMMENT): Rules R2/R3 agree with gate rulings R2/R3. (1) `test_no_forbidden_imports` is still prose only. Please add it as code in a fresh subprocess that scans the harness import graph. Verity's prototype false-passes on self-import, so a self-import check won't do. (2) sweep_width.py: Verity CLEAR for reference/adapter use (conf 70), but NEW-11 stays OFF until Strata flips it and the L77-89 CASE-X path is replaced by a deprecation note. (3) Registry: provisional 1010/1020 collide with `forensic_models/taphonomy` (1010) and `soil_nitrogen` (1020) on merged branch sar-make-it-work, and 1000 is double-booked. Use the 2300 block (see R5). (4) Out-of-scope reminder: evidence_scoring.py, drift_envelope.py and their tests read case-files at runtime and must stay out of the game path. Base is `main`, which is fine for a draft. Do not merge until Verity-N APPROVE is in the LEDGER.
### PR #11 (Ledger-Play balance v0.2, draft → main)
> Verity (COMMENT): D4 blocks search_theory/optimal_search/sweep_width, consistent with gate R2. sweep_width is now CLEAR-conditional (R1), so it stays blocked until Strata enables NEW-11. D4 L13 test spec: require a fresh-subprocess import-graph scan (self-import gives false passes). L124 still says "derive from W × speed via sweep_width.py" and L151 still uses "POA from lost_person_sim". Both conflict with the blocks, so mark them SUPERSEDED. lost_person_sim → lpb_mpb2003.json has no licence (R3). D6 registry ids → 2300 block.
### PR #12 (LEDGER entry, → sensecrew/ledger)
> Verity (COMMENT): Append-only diff. The licence field is correct. The entry has no Verity-N APPROVE line yet (rule 1), so it isn't mergeable until one is added. Wording is fine.
### PR #13 (PixelLantern palette/a11y, draft → main)
> Verity (COMMENT): cividis licence confirmed permissive (R3): pnnl/cmaputil Battelle BSD-style, paper CC BY 4.0, Matplotlib PSF-style. You may lift the EXCLUDED status. Obligation: ship the Battelle notice in `palettes/LICENSES/` and no endorsement use. Please verify the Crameri "MIT per Zenodo" claim against the pinned release file (Verity hasn't checked it) and viridis CC0 (matplotlib `_cm_listed.py` header). No forbidden-path references.
### PR #14 (LEDGER PixelLantern entry → sensecrew/ledger)
> Verity (COMMENT): Append-only. The licence field is correct. Add a follow-up line once #13 is updated for cividis, and add a Verity-N APPROVE line before merge.
### Discussion #15 (Chitin, insect-trace ADD sim) — not commented (see summary)
- Claim "registry highest id today: 1000 ... no insect-trace or taphonomy component" is true **only for main**. Merged branch `sar-make-it-work` (PR #3, marked merged but NOT an ancestor of origin/main) has `1010 forensic_models/taphonomy` (`sar/forensic_models/taphonomy.py`) and `2210 docs/research/INSECT_TRACES` (`sar/docs/research/INSECT_TRACES.md`). Reuse order (rule 10) says check these first. Their lineage is UNVERIFIED by Verity and needs a case-files/evidence import check before any reuse.
- Name `insect-trace-evidence` → **RENAME**. It collides with the forbidden `evidence/` namespace (registry 110 = `blue-ocean-sar/evidence`). Suggest `insect-trace-add-sim`. Also "decay-taphonomy-model" overlaps existing 1010 taphonomy, so extend that rather than duplicate it (rule 10). Confidence 85.

## R5 — Registry numbering. Confidence 90
- Max id: **origin/main and sensecrew/ledger = 1000** (`language_scan`, 29 components). **origin/sar-make-it-work and sar-consolidation = 2210** (61 components). There, 1000 = `forensic_models` (collision with main's 1000 = `language_scan`), plus 1010, 1020, 1100-1450, 1900-2210. So the real max is **not** 1000 repo-wide.
- Strata provisional collisions: 1010 ✗ (taphonomy), 1020 ✗ (soil_nitrogen), 1030-1070 free on every branch but sit inside the `forensic_models` 1000 block on sar-make-it-work. Wrong parent and a namespace clash, so reject.
- Recommended (free on all branches, new top-level block): **2300 sensegame (parent) · 2310 NEW-01 CleanScorer · 2320 NEW-03 synthetic DEM · 2330 NEW-10 clean sweep-width table · 2331 NEW-11 adapter (disabled) · 2340 NEW-12 sweep harness · 2350 insect-trace-add-sim · 2360 NEW-22 mineral-spectral-unmix**. Decay-taphonomy should extend 1010 and needs no new id.
- Also flag to Strata: main vs sar-make-it-work registry divergence (1000 double-booked), which needs an owner decision. "Never reuse a retired number" (registry `_doc`).

---
# Round 2 — 2026-11-04 ~20:30 MST
**How the confidence is scored.** These use the bands in revvel-standards `fraud-signal-verification-fleet/docs/CONFIDENCE_FRAMEWORK.md`: SUBSTANTIATED 0.85–1.00, SUPPORTED 0.55–0.84, WEAK 0.30–0.54, UNSUBSTANTIATED 0.00–0.29. That framework was written for claims about people, so Verity adapted it to engineering:
- base = tier 4 "primary official" 0.80 × provenance "filing" 1.00 for a primary artefact read this turn (code at a pinned sha, a LICENSE file, an HF/GitHub API licence field, or a local test re-run);
- +0.06 for each independent corroboration (cap +0.24);
- −0.12 for each contradicting signal;
- capped at "alleged" 0.45 when the claim depends on a file Verity is not allowed to open.
The refusal gate does not apply.

## R6 (a) realdata/fusion.py lineage: QUARANTINE kept (game path); no taint found in its body. 0.74 SUPPORTED
- L4: "Replaces the "SFAI probability" in ryverly_recon_app-v6.py (docs/case-files), which multiplied typed-in anomaly scores by invented ... "decay" curves". This is a negative citation: the case-file design was rejected, and no weights or curves were carried over ("There are no built-in weights and no time-decay curves", L9-10).
- Imports L54-61 are stdlib only. `grep case-files` matches only L4, so it reads nothing at runtime.
- The shared commit with evidence_fusion.py is **not** evidence. `c944260` is the 2026-10-21 consolidation commit that added the whole toolchain at once.
- Score: 0.80 + 0.06 (grep corroboration) − 0.12 (it was written by reading the case-file app) = 0.74.
- Ruling: it may be kept as a reference. Fusion's clean-room 2370 replacement is still the right call, and fusion.py stays out of the game path. evidence_fusion.py is a separate file and is not ruled here.

## R7 (b) realdata/refloat_timing.py lineage: CLEAR. 0.92 SUBSTANTIATED
- Imports L71-79 are stdlib only. Zero case-files, ryverly, evidence/ or hfmr hits in refloat_timing.py or test_refloat_timing.py.
- Sources: L10-13 Delhez et al. EGUsphere preprint egusphere-2026-5071 (the file labels it "not peer-reviewed"), and L40 doi:10.1029/2022WR034358.
- Score: 0.80 + 0.06 (grep) + 0.06 (cited DOIs) = 0.92.
- Caveats: the domain is drowned-body refloat, so a game should reuse only the generic `ADD` accumulator idea, not the presets. PR #27 already writes its own clean-room ADD and doesn't import this file, which is also fine.

## R8 (c) TerraMind / TerraTorch licence: weights and code Apache-2.0; TerraMesh data CC-BY-SA-4.0. 0.92 SUBSTANTIATED
- Weights: HF API `cardData.license` = `apache-2.0`, `gated: false` for ibm-esa-geospatial/TerraMind-1.0-{tiny,small,base,large}. The model card README front-matter says `license: apache-2.0`.
- Code: GitHub IBM/terramind is Apache-2.0. IBM/terratorch redirects to torchgeo/terratorch, also Apache-2.0.
- Pre-training data: HF dataset ibm-esa-geospatial/TerraMesh is **cc-by-sa-4.0** (share-alike). Any bundled TerraMesh samples or derived datasets would carry share-alike terms; weights alone don't.
- Score: 0.80 + 0.06 + 0.06 = 0.92.
- Note: TerraMind is a *generative* model. Strata's Discussion #21 rule "Generative AI stays out of the science core and game logic" still applies, so ON HOLD in #18 is correct for a rule reason, not a licence one.

## R9 (e) forensic_models/taphonomy.py and docs/research/INSECT_TRACES.md (branch sar-make-it-work): CLEAR, no case-files derivation. Unblocks the 1010 extension
- taphonomy.py (head 1117fed): its only import is `from .constants import load, value`, plus math. Constants are sourced:
  - `megyesi_add` "Megyesi, Nawrocki & Haskell (2005) J Forensic Sci 50(3):618-626, doi:10.1520/JFS2004017";
  - `topp_forward` "Topp, Davis & Annan (1980) ... doi:10.1029/WR016i003p00574".
- The "notebook" mentioned in constants.json L67/L72 ("the notebook's 0.4 had no source") is the Gemini Notebook bootstrap (HANDOFF.md L102 `master_unified_sar_bootstrap.py`), not case-files, and those values were rejected.
- Zero case-files, ryverly, evidence/, hfmr or dossier hits. Score: 0.80 + 0.06 = **0.86 SUBSTANTIATED**.
- INSECT_TRACES.md (2210, commit 619a525): L3 "literature summary only. It has no code". Every claim has a DOI (Gaudry 2009, Mazzanti 2010, Wells 2001, Amendt-family reviews ...). No case references. The word "evidence" in its title is prose, not the forbidden evidence/ namespace. Score 0.80 + 0.06 = **0.86 SUBSTANTIATED**.
- Caveat: both live only on sar-make-it-work, which is not an ancestor of main. A 1010 extension must branch from there or bring the file across. Also, `vass_pmi` is null in constants.json.

## R10 (d) PR reviews, round 2 (COMMENT only; tests re-run in /workspace/sensecrew/wt/verity-*)
- **#18 Fusion (ba1a3e2 → main, NOT draft).**
  - 2370 is free on every remote branch (0 hits across 15+ registry.json files).
  - `2370.1` is not a valid id: the registry uses integer keys, so use **2371**.
  - Clean-room combiner math (robust z, Hampel 1974 / Rousseeuw & Croux 1993) is public statistics, OK even though fusion.py uses the same normaliser.
  - The forbidden-imports list matches gate R1/R2/R6.
  - Ask: convert to draft (team rule: draft PRs only).
  - Score 0.86.
- **#19 Quartz ledger.**
  - Independent re-grep of main `multi_proxy/` (incl. nnls_unmix.py, sam.py) for case-files, hfmr, dossier, evidence, public_records, search_theory, lost_person found **0 hits**, so the PASS is confirmed.
  - The diff is append-only (0 removed lines).
  - It now **conflicts** with the sensecrew/ledger tip 98cb463 and needs an update by *merge* (rule 8: don't rewrite pushed history).
  - Score 0.86.
- **#20 Quartz NNLS/SAM golden.**
  - Re-run: `pytest test_nnls_sam_golden.py` gives **8 passed**.
  - Imports are numpy plus the repo's own nnls_unmix/sam only.
  - splib07 is cited as USGS public domain (Kokaly et al. 2017) ✔.
  - NEW-22 → **2360** per Discussion #25.
  - Score 0.86.
- **#24 Humus Topp+Mironov.**
  - Re-run: **13/13 passed** (claim confirmed). The whole multi_proxy suite has 35 passed + 19 subtests, so there are no regressions.
  - Determinism: same seed 20261104 gives the same sha256 twice (3582b287…); seed 7 differs.
  - Imports: stdlib + numpy.
  - DOIs: Topp 1980 10.1029/WR016i003p00574, Mironov 2009 10.1109/TGRS.2008.2011631 + correction 10.1109/TGRS.2009.2023842.
  - The fixture is `*_synthetic.json` ✔.
  - The one removed line is a docstring rewrite in dielectric.py, not a deletion of behaviour.
  - Humus-N APPROVE line is present (PR body L27). The full component-100 run timed out locally, so it was not confirmed.
  - Score 0.86.
- **#13 PixelLantern re-check (2eb02c6).**
  - cividis re-added with "BSD-style (licence-cleared 2026-11-04)" and an obligation to keep the Battelle notice. Pixel Lantern-N APPROVE is present (L109).
  - Gap: the PR describes the notice but doesn't include it. Add `palettes/LICENSES/BSD-Battelle-cividis.txt` with the verbatim text from https://raw.githubusercontent.com/pnnl/cmaputil/master/LICENSE when assets land.
  - The Crameri "MIT" claim is still unverified by Verity.
  - Score 0.80.
- **#14 PixelLantern ledger (ce6585d).**
  - Behind the sensecrew/ledger tip by 8 commits and **CONFLICTS** (`git merge-tree`), so it needs an update, by merge, not a force-push rebase.
  - Its L6 still says "cividis excluded until Verity confirms". It is superseded by its own L14 addendum (fine for append-only).
  - N-APPROVE is present; Verity-N APPROVE is not.
  - Score 0.86.
- **#11 LedgerPlay re-check (ceebf3d).**
  - D9 adopts 2330/2331/2340 and the sweep_width CLEAR-reference ruling.
  - L126 and L153 are now marked DEPRECATED ✔.
  - Remaining issue: L153 still names `lost_person_sim` as the POA source inside the deprecated sentence. The bracket addresses only W, so add "POA from the Bedrock procedural prior (lpb blocked, R3)".
  - Score 0.86.
- **#12 LedgerPlay ledger re-check (16ff66b).**
  - Append-only (0 removed lines vs the merge base). Ledger-Play-N APPROVE lists 3 shas. "Verity: pending" is accurate.
  - **CONFLICTS** with the ledger tip 98cb463, so it needs an update by merge.
  - Score 0.86.
- **#27 Chitin 2350 (a806584).**
  - 2350 exists only on its own branch, so there's **no collision** on any other remote branch.
  - Clean-room confirmed:
    - sim.py imports only json, os and random;
    - its docstring says "Does NOT import realdata/refloat_timing.py";
    - the ADD is the textbook averaging method with citations (Amendt 2007 doi:10.1007/s00414-006-0086-x; Nabity 2006);
    - the fixture is a fictional taxon, `species_synthetic.json`, "NOT real species data".
  - Re-run: **7 passed**; `registry.py 2350 --test` OK. Determinism: same seed gives identical sha256 (988186f2…).
  - The registry diff only adds lines (no '-' lines).
  - Nits: `open()` without close at sim.py L19 (ResourceWarning). The registry entry sits on main's 29-entry registry, so the 2300 parent doesn't exist there yet.
  - With R9 CLEAR, the 1010 extension note can proceed, but on a branch carrying sar-make-it-work's forensic_models.
  - Score 0.92.

---
# Round 3 — 2026-11-04 ~20:40 MST (same bands and adaptation as round 2)

## R11 ACE-Step 1.5 licence (Discussion #30)
**Code and weights: MIT. 0.92 SUBSTANTIATED.**
- GitHub `ace-step/ACE-Step-1.5`: licence is MIT, per the API `license.spdx_id`. The README says "licensed under [MIT](./LICENSE)".
- These Hugging Face repos all report `cardData.license=mit` and `gated=false`:
  - ACE-Step/Ace-Step1.5
  - acestep-5Hz-lm-0.6B
  - acestep-5Hz-lm-4B
  - ace-step-v1.5-1d-vae-stable-audio-format
- The older v1 repos (`ACE-Step/ACE-Step`, `ACE-Step-v1-3.5B`) are **Apache-2.0**, not MIT. Don't mix them up.
- **Exclude** `ACE-Step-v1.5-chinese-new-year-LoRA`, which is **creativeml-openrail-m** and comes with use restrictions.
- The LM planners are fine-tuned from Qwen3-0.6B/1.7B/4B, according to the model card. Verity did not re-verify the Qwen3 upstream licence this round, so treat it as an open item.
- 1.7B LM: not found under the ACE-Step author listing, so its licence is unverified.

**Training data: "Licensed / royalty-free / synthetic MIDI-to-audio" is self-reported only. 0.45 WEAK.**
- No dataset card or manifest was found.
- The README disclaimer acknowledges "potential risks such as unintentional copyright infringement due to stylistic similarity". It asks users to "verify the originality of generated works, clearly disclose AI involvement". This is a soft, non-binding responsible-use clause, not a licence restriction.
- Ruling: OK for the entertainment skins only, as baked tracks with the prompt, seed and model hash recorded (Loam's plan). Add an AI-music disclosure line in credits.
- Loam's 92/100 rubric is not the CONFIDENCE_FRAMEWORK; this R11 is the gate score.

## R12 PR #31 Humus soil_dna_sensor (9134f90, draft → main)
**Changes.** The rename is additive. It adds 2 re-export shims plus docs `eDNA→soil_dna_sensor` (3 removed lines, all doc wording). Nothing was deleted; `qpcr_*` are kept.

**lab_readers.py lineage: CLEAR as a reader of the user's own lab exports. 0.80 SUPPORTED.**
- L4: "Replaces the GC-MS and 16S tabs of ryverly_recon_app-v6.py (docs/case-files), whose peak counts, retention times and abundances were typed in". This is a negative citation.
- It has no built-in retention times or abundances. The method comes from the user's file, and the example method is refused without `--allow-example-method`.
- `DEFAULT_TARGET_NAMES` contains putrescine, cadaverine, indole, skatole and DMDS. These are generic cadaveric VOC names from the literature, not values.
- `case-files` and `ryverly` appear only in the L4 docstring. Every `open()` is on a CLI-supplied path.
- Score: 0.80 + 0.06 (grep) + 0.06 (no embedded values) − 0.12 (written against the case-file app) = 0.80.
- I did not check where `gcms_method.example.json` comes from (that check was interrupted).

**Audit corrections.**
- humus_rule7_audit_qpcr.md says lab_readers has "**No imports**". That is wrong: it imports argparse, csv, json, math, os, sys, numpy, optional scipy and pyteomics/pymzml. None are forbidden, so the PASS stands, but the row should be fixed (append a correction).
- humus_cited_values.md gives three different tallies (7/7, then 10 listed, then "cited = 8, placeholders = 6"). Pick one.
- The 2 shims have no tests.

## R13 PR #24 re-check at 5b6daed (`make sim`). 0.92 SUBSTANTIATED
- `make` is not installed on the box, so I ran the Makefile recipe verbatim (SEED 20261104, N_THETA 8, N_CLAY 6, FREQ 1.4 GHz):
  - seed 20261104 twice gives sha256 3582b287d438 both times (same as round 2);
  - seed 7 gives bec09d3370a8.
- multi_proxy: 35 passed, 19 subtests.
- **Full component 100 (`registry.py 100 --test`, 1500 s timeout): Ran 441 tests, OK (skipped=1), rc=0.** This closes the round 2 gap.

## R14 forensic_models/constants.py + constants.json (sar-make-it-work f9efac6)
**CLEAR for the 1010 extension to import live. 0.92 SUBSTANTIATED.**
- The loader imports only json and pathlib. It **raises** if any constant has an empty source, and it requires a source on every override.
- Every value has a citation:
  - Topp 1980 doi:10.1029/WR016i003p00574
  - Megyesi 2005 doi:10.1520/JFS2004017
  - Vass 2011 doi:10.1016/j.forsciint.2010.04.052
  - Gabriel 1996 doi:10.1088/0031-9155/41/11/003
  - Kätterer 1998 doi:10.1007/s003740050430
  - Linn & Doran 1984 doi:10.2136/sssaj1984.03615995004800060013x
- These have `null` values with a "supply with source" note: eps_soap, k_saponification, k_ammonification, k_nitrification.
- "Notebook" refers to the Gemini Notebook bootstrap; its values were rejected. There are zero case-files, ryverly, hfmr, evidence, dossier or public_records hits.
- Nit: `topp_forward` holds the θ(Ka) coefficients and `topp_inverse` holds Ka(θ). The names look swapped relative to Topp's paper; check before reuse.

## R15 Re-checks (COMMENT only; force-push counts from the REST timeline)
| PR | Head checked | Force-pushes | Finding | Score |
|---|---|---|---|---|
| #11 | 4f63fba | 0 | L159 `lost_person_sim` POA sentence now carries a DEPRECATED marker ✔ | 0.86 |
| #12 | a9f7e7f | 0 | Merge c648079 brings in ledger 98cb463. 16ff66b is an ancestor (no rewrite). 0 removed lines vs the ledger. Conflicts again with the new tip 50b7069, so merge again. | 0.86 |
| #13 | 32fa46b | 0 | cividis-NOTICE: the pnnl/cmaputil LICENSE (sha256 3282e3c5…) appears **verbatim and contiguous** under a 5-line `#` header. crameri-LICENSE: MIT text. Zenodo API for 8409685 shows v8.0.1, licence `mit-license`, file ScientificColourMaps8.zip md5 e63c1d2d…. **PDF sha256 e2facd02… NOT independently verified** (66.9 MB download interrupted). | 0.86 |
| #14 | 99f49dd (251a5d9 merge) | 0 | ce6585d is an ancestor, and 251a5d9 merged the ledger at f623746. 0 lines lost. It does not include the newest tip (5d455f0/50b7069). | 0.86 |
| #18 | 6a1fdd5 | 0 | Draft again ✔. 2370 is the module and 2371 the combiner. Neither is a key in any branch's registry.json. Every textual mention across branches refers to Fusion, with no other claimant. 2370.1 survives only in changelog history. | 0.92 |
| #27 | 174b65d | — | **14/14 pass.** Seed 7 twice gives 269ced7c5b8f; seed 8 gives c6989b7c205f. 0 removed lines. It now reuses `refloat_timing` ADD via `refloat_adapter` (allowed by R7) and prints the preprint LABEL. `decay_taphonomy_bridge` imports forensic_models.taphonomy (R9/R14 CLEAR). | 0.92 |

## R16 LEDGER head-insert correction (50b7069, on sensecrew/ledger, Humus 20:33)
- It appends a one-line note at EOF, covering the two head entries at L1 (20:30 Humus) and L28 (20:28 Chitin). Present ✔; Verity did not add a duplicate.
- Flag for Strata: L48–80 (20:25 Humus Topp+Mironov and its correction) also sit above the 20:15 Loam entry, and the note doesn't mention them. They could be another head insert, or the original file order. Strata should rule.

## Round 4 — 2026-11-04 ~20:45 MST (Verity, single instance; Verity-N pending)

- R17 PR #29 82b7cb6 — splib07 subset: 11/11 ascii files byte-identical to USGS ScienceBase ASCIIdata_splib07b_cvAVIRISc2014.zip; citation Kokaly et al. 2017, doi:10.5066/F7RR1WDJ (USGS DS 1035, doi:10.3133/ds1035). Licence: US Government work, public domain (17 USC 105); no rights field in the ScienceBase JSON, and the policy page returns 403 to curl. Provenance SUBSTANTIATED 0.92; PD licence SUBSTANTIATED 0.86. RULE-8 NAMING: real reference data in fixtures/splib07_subset, not *synthetic* → does NOT meet literal rule 8 → needs a Strata/Audrey exception or reclassification. SenseCrew-only gate: HOLD.
- R18 PR #32 b422e96 — 34 passed; same seed → same sha (20261104: b8372e52fdbb ×2; seed 7: 71b3a795eb39). SUBSTANTIATED 0.92. Inherits #29 fixtures → gate HOLD on the same naming item.
- R19 PR #20 be054b1 — still says "NEW-22 (provisional…)"; 2360 does NOT appear in #20. 2360 is free: no registry.json key on any branch, and no "2360" string in history (2360 is used only by the Quartz #29/#32/#33 text). Ask 3 FAILS until #20 is updated. Gate: otherwise clean (synthetic, no forbidden imports) → PASS once the id is updated.
- R20 PR #13 — Crameri +LICENCE.pdf sha256 e2facd02…3a02 verified by Verity from Zenodo ScientificColourMaps8.zip (md5 e63c1d2d… matches Zenodo); MIT, (c) 2023 Fabio Crameri. SUBSTANTIATED 0.92.
- R21 LedgerPlay — #12 a0bb4a1 (contains eff6c1a; 96bbca8 is an ancestor; 0 removed lines vs 96bbca8; 0 force-pushes; "Ledger-Play-N APPROVE 0ba21b4…" is present) is clean as of 96bbca8. But the ledger tip is now 7c973d1 and #12 conflicts with it. #11 0ba21b4: 0 force-pushes, mergeable, but balance-proposal-v0.2.md L116 ("Also present: `lost_person_sim.py` …") is NOT tagged DEPRECATED (L92 and L153 are tagged) → not every reference is tagged → NO PASS on #11/#12. Fix: tag L116, then re-merge #12 onto 7c973d1.
- R22 PixelLantern — #14 d09eb9e: 96bbca8 is an ancestor, 0 removed lines, 0 force-pushes, but GitHub mergeable=CONFLICTING (ledger tip moved to 7c973d1) → NO PASS on #13/#14 until #14 is re-merged.
- R23 PR #33 — 79d692c FAILED rule 5 (it loaded HySUPP FCLS in-process via sys.path/importlib, which pulled GPL spams into our interpreter). Re-audited at 97474e2189aec414d4984107621ce13cbe5efcd2: subprocess-only (subprocess.run of SPAMS_COMPARE_CMD or $HYSUPP_VENV/bin/python $HYSUPP_ROOT/hysupp_fcls_cli.py), gated by HYSUPP_ROOT, and it refuses runners inside the repo. spams appears only in docs/comments; it is not in any requirements*, lock, toml or cfg file; nothing is vendored. Tests (no external venv): hysupp+splib07 files 26 passed, 1 skipped. HySUPP MIT per Quartz's doc (not re-verified upstream by Verity). Rule 5: SUBSTANTIATED 0.88. Still stacked on the #29 fixtures (rule-8 naming HOLD).
- R24 PR #27 dcc7412 — 15/15 passed twice; CLI --seed 42 --days 30 → sha 237d09369254 twice, seed 7 → b24d0dfa7253. Live imports: forensic_models.taphonomy → .constants (cleared), plus the pre-cleared refloat_timing adapter (R7, an opt-in engine). No forbidden-path imports. SUBSTANTIATED 0.90 → Verity PASS.
- R25 PR #31 809e58a — alias tests 3/3; qpcr+lab_readers 43/43; tally 9 cited (1,2,3,4,8,9,11,12,13) / 5 placeholder (5,6,7,10,14), consistent across the table and summary. gcms_method.example.json: added only in c944260 (Audrey, 2026-10-21), which reached main via **PR #2** (commits c944260…; merge 19bee3d), NOT PR #9 (PR #9's commits do not touch the file). Content self-declares placeholder RTs. The audit row for lab_readers omits the optional pyteomics/pymzml imports (L107/L123, not forbidden). → NO PASS until the PR #9→#2 attribution and the audit row are fixed. Provenance SUBSTANTIATED 0.90.
- R26 Qwen3-Embedding-0.6B (ACE-Step 1.5 text encoder): NOT covered by the earlier exclusion (that open item was about the LM planner bases). HF API at sha 97b0c614: licence apache-2.0, gated=false, base_model Qwen/Qwen3-0.6B-Base (also apache-2.0, ungated). No LICENSE file in the repo (card metadata only) → SUPPORTED 0.80.

## Round 5 — 2026-11-04 ~20:50 MST (single instance; Verity-N pending)
Strata ruling adopted: ledger PRs are judged on content, not on ledger-tip conflicts (they re-merge before Audrey merges). #29 → reference/ oracle move, so no rule-8 exception is needed.
- R27 #11 6501477: line 116 is tagged DEPRECATED; 0 untagged lost_person references in any changed file; 0 force-pushes → PASS 0.90. #12 e3bc657: "Ledger-Play-N APPROVE 65014777…" is present; LEDGER +56/−0 vs the ledger base; 0 force-pushes → PASS 0.90.
- R28 #13 32fa46b: cividis NOTICE verbatim; Crameri MIT with PDF sha verified; +156/−0 → PASS 0.92. #14 d09eb9e: 96bbca8 is an ancestor, 0 removed lines, 0 force-pushes → PASS on content 0.88.
- R29 #20: head still be054b1 with NEW-22 provisional; 2360 not applied → no PASS yet (2360 still free).

- R30 (2026-11-04 ~20:50 MST) #31 54b70fa: provenance corrected to c944260 via PR #2 (merge 19bee3d), with the PR #9 claim retracted; the audit row lists the optional pyteomics/pymzml imports; alias tests 3/3, qpcr+lab_readers 43/43; 0 force-pushes; LEDGER 92e2c5f is append-only (+1/−0, bb0c0a0 is an ancestor) and corrects bb0c0a0 in substance (it does not cite the SHA) → PASS 0.90.

- R31 (2026-11-04 ~20:55 MST) Quartz: splib07 moved by git mv to multi_proxy/reference_oracle/splib07_subset (oracles, not seeds); 11/11 ascii files byte-identical to USGS; README cites Kokaly 2017 with doi:10.5066/F7RR1WDJ and doi:10.3133/ds1035; 16 renames, 0 deletion commits; no non-synthetic files under multi_proxy/fixtures; 2360 free on all branches; 0 force-pushes. #20 38c7087e834f labels 2360, 30 passed → PASS 0.90. #29 04d5aa328a98 38 passed → PASS 0.92. #32 0e343b0bcd64 56 passed, determinism 8b70182af528 ×2 (seed 7 b1bb3db41119) → PASS 0.92. #33 cb6e2ac63fb7 48 passed/1 skipped, no spams import or pin → PASS 0.90. Rule-8 naming issue from R17 resolved by the reference_oracle move (Strata).

- R32 (2026-11-04 ~21:00 MST) #34 a011ba7 (draft → main): registry adds only 2360 (0 removed/changed; 2360 free elsewhere); registry.py 2360 --test → 22 ran OK, 1 skipped; strict forbidden-imports gate (e017094, empty allowlist) → 2 hits (dynamic importlib in pre-existing multi_proxy/test_package_imports.py:54,59), 22 files scanned, exit 1; no opendata/realdata or forbidden-path hits. Depends on #20/#29/#32/#33 (all PASS R31). NOT gate-green: narrow the 2360 scope, or rule on/allowlist the guard. Registry 0.92; gate result SUBSTANTIATED (primary run).

- R33 (2026-11-04 ~21:05 MST) #34 95b28a7 (draft → main, after the Strata R32 narrowing): registry adds only 2360 (0 removed/changed), and 95b28a7 vs a011ba7 changes only the `path` line → `blue-ocean-sar/multi_proxy/nnls_unmix.py`. registry.py 2360 --test → 22 OK, 1 skipped (HySUPP not configured); 100 → 450 OK, 2 skipped; 995 → 3 OK. Strict forbidden-imports gate (golden-gate f2ea3ed, empty allowlist, --strict): 1 file scanned (sar/blue-ocean-sar/multi_proxy/nnls_unmix.py), 0 hits, exit 0. Determinism: no output files written; the two test logs have identical sha256 cbb4a8d36afa… → PASS 0.92. COMMENT review https://github.com/midnghtsapphire/forensicfinders/pull/34#pullrequestreview-5779684990. Verity-N approval pending.

- R35 (2026-11-05 ~07:35 MST) PR #36 5fbcc20 (Deepscan specs 510/520/530; doc-only, sar/docs/deepscan_module_specs_v0.md): forbidden-path and import scan of the diff found 0 hits (case/, hfmr/, dossier, evidence/, public_records*, PII appear only in prohibitions); 0 EDNA/eDNA; 0 realdata/opendata; Ultralytics is FORBIDDEN and has a guard test; gprMax is offline CLI only; seeds only fixtures/synthetic_*. forensic_pipeline (import and def lines only, no bodies opened): numpy/scipy.ndimage/pytest only, no I/O, no fixtures; isrid_prior_map(shape, last_seen_xy, category_radius) is parametric. Renames APPROVED: isrid_prior_map→synthetic_prior_map 0.90; finder_confirmation→confirmation_event 0.88; "Private forensic pipeline"→"Synthetic search-scenario pipeline" 0.90. The forensic_pipeline package name stays (CLEAR 0.80; game path 2300 imports only the renamed symbols). Conditions: the code PR updates the registry text, tests, and callers together; no ISRID data files. Specs CLEAR 0.90. COMMENT https://github.com/midnghtsapphire/forensicfinders/pull/36#pullrequestreview-5786554224. Verity-N pending.

- R36 (2026-11-05 ~07:34 MST) PR #39 73efc1c (Bedrock specs 2310 CleanScorer + 2320 synthetic DEM; docs/sensecrew/bedrock/ only, +558/−0): Rule 7 CLEAR (0 forbidden paths; dem_synthetic_* seeds 1001/1002/1003; PII only as prohibition; 0 EDNA/eDNA/realdata/opendata). Rule 5 CLEAR (Ultralytics forbidden; GPL not on write path; rasterio/GDAL optional read-back only; stdlib GeoTIFF writer). No registry.json this PR; when 2310/2320 land → UNLICENSED (private; licence pending Audrey). Determinism notes present (stdlib math / PCG64 random_raw / SHA-256 exact / TOL 1e-12 & 1e-9). 2300 game-path forbidden-imports mindset CLEAR for specs (proposed deps: math; stdlib+numpy). Non-blockers agreed: DEM SHA PENDING; M1 W PLACEHOLDER; Loam GDD wording; failing goldens by design. Specs CLEAR / PASS 0.90. COMMENT https://github.com/midnghtsapphire/forensicfinders/pull/39#pullrequestreview-5786613165. Verity-N pending.

- R37 (2026-11-05 ~07:45 MST) PR #40 422c9edf (Deepscan 510/520/530 code + forensic_pipeline renames, draft): renames are applied, with deprecated aliases that emit DeprecationWarning (tested), and registry 990 now reads "Synthetic search-scenario pipeline"; 0 forensic_pipeline imports in the Deepscan modules (stdlib+numpy); fixtures are all synthetic_*; axial dipole is 0.2 nT (test delta 1e-6; spec 2.0 nT was a typo). make test: ert 7/7, mag 6/6, gpr-void 8/8, forensic_pipeline 13/13. sim SEED=42 is deterministic (results sha ert adaf9f95…, mag 95d3abf1…, void 8f56fbc8…, same on both runs). Forbidden-imports and Rule 5/7 scan: 0 hits. BLOCKER: registry 510/520/530 have no licence field; needs "licence": "UNLICENSED" (licence pending Audrey). Nit: results_seed42.json is not gitignored. CHANGES-REQUIRED 0.90. COMMENT https://github.com/midnghtsapphire/forensicfinders/pull/40#pullrequestreview-5786718278. Verity-N pending.

- R38 (2026-11-05 ~07:48 MST) Verity-D PR #40 5b1149d (R37 fix): diff vs 422c9ed has 4 files +9/−3 (registry licence ×3 plus 3 .gitignore files with results_seed42.json; the −3 are trailing commas); 0 forbidden paths or imports; JSON valid. Licence 510/520/530 = "UNLICENSED (private repo; licence pending Audrey)". Tests: ert 7, mag 6, void 8, gpr-wave 15, forensic_pipeline 13 all OK; sim output is git-ignored. PASS 0.92. COMMENT https://github.com/midnghtsapphire/forensicfinders/pull/40#pullrequestreview-5786766722. Verity-N pending.

- Verity-N (independent; 2026-11-05 07:47 MST) PR #40 5b1149d: APPROVE. Supersedes same-workstream note a8fea7f. Licence exact; renames+aliases OK; 0 forensic_pipeline imports in Deepscan; synthetic_* fixtures; axial dipole 0.2 nT; pytest ert 7 / mag 6 / void 8.
- R39 (2026-11-05 ~08:20 MST) Verity-D PR #41 8e745c6 (Bedrock NEW-01/2310 CleanScorer, draft → main, branch sensecrew/bedrock/new-01-cleanscorer): Independent Verity-D review at exact head SHA `8e745c6ea010a7197621690506ee7136b43056d0` (worktree `/workspace/sensecrew/wt/verity-pr41`, detached). Diff: 13 files +868/−2 (Makefile test-scorer; docs/sensecrew/bedrock/{LEDGER.md,specs/scorer-spec.md,specs/tests/test_scorer_golden.py,specs/discussion-drafts/*}; sar/sensegame/search_core.py + tests; sar/ledgerplay/scoring.py re-export; registry 2300/2310). Rule 7 CLEAR for PR-added modules: search_core imports only math/dataclasses/typing/__future__; scoring re-exports CleanScorer only; 0 imports of case/, hfmr/, dossier, evidence/, public_records*, Ultralytics, raw LUCAS, EDNA/eDNA, realdata/opendata, ISRID data, or quarantined search_theory/optimal_search/sweep_width. Registry ΔNDVI unicode escapes on 910/970 are incidental re-serialization (no new forbidden content). Licence 2300/2310 = exactly `UNLICENSED (private repo; licence pending Audrey)` (same string as Deepscan 510/520/530). CleanScorer in sar/sensegame/search_core.py; ledgerplay.scoring sets `Scorer = CleanScorer`. M1_W_KM = None / M1_W_SOURCE = None (PLACEHOLDER; 2 xfail strict); no invented numeric W. DEM SHA-256 still PENDING (DEM/2320 not in this PR tree; carry-forward from #39). Tests observed: `make test-scorer` and pytest sensegame/tests + docs path → **31 passed, 2 xfailed**. Spot-check pod 0.6321205588285577; same optimal plan → same sha256. Bedrock LEDGER.md present, single-commit append-only history (0 force-pushes). PR remains draft. Discussion draft m1-sweep-width.md present, NOT posted. Optional gate tip scan (verity-gate-clean, empty allowlist): flags `__future__` and `pytest` as not on SAFE_STDLIB — gate-policy gap (gate tip not merged); not a PR fail. **Verdict: PASS-with-hold 0.90.** Hold conditions: (1) DEM SHA-256 PENDING / must be regenerated independently from impl before merge of DEM/full game path; (2) M1 W still PLACEHOLDER — Waveform citation + Verity co-sign required before CLEAR of that; (3) keep draft; (4) do not post m1-sweep-width.md without Audrey approval. Merge-ready ONLY after DEM SHA regen + cited M1 W. Verity-N pending.

- Verity-N (independent; 2026-11-05 08:21 MST (America/Denver)) PR #41 8e745c6: APPROVE-with-hold 0.90. Fresh worktree /workspace/sensecrew/wt/verity-n-41 (not verity-pr41). Re-checked Rule 5/7 CLEAR; licence 2300/2310 exact UNLICENSED; make test-scorer → 31 passed / 2 xfailed (M1 W PLACEHOLDER); M1_W_KM None; DEM SHA PENDING; draft + m1-sweep-width.md unposted. Same hold list as R39. Points to R39 + this LEDGER entry.
- R40 (2026-11-05 ~08:27 MST) Verity-D PR #41 8c98804 (Bedrock NEW-01/2310 + NEW-03/2320 DEM fixtures, draft → main, branch sensecrew/bedrock/new-01-cleanscorer): Re-review after claimed DEM golden SHA-256 regen. Fresh worktree `/workspace/sensecrew/wt/verity-pr41-dem` at exact head `8c988040e0924be3e5f35da5a2d269f68bee01e1` (did not reuse verity-pr41 / verity-n-41). Diff 8e745c6..8c98804: 16 files +756/−3 — Makefile dem/fixtures-*/test-dem; docs dem-fixture-spec.md + dem_golden_sha256.json + test_dem_fixture_golden.py + bedrock LEDGER; sar/fixtures/{SHA256SUMS, dem_synthetic_1001/1002a/1002b/1003.tif, 1002_truth.json}; registry +2320; sar/sensegame/{dem.py,tiffw.py,tests/dem_golden_*}. No forbidden-path touches; no unrelated risky changes. **DEM SHA-256 independence (CRITICAL):** regenerated via separable path `sensegame.dem.generate(seed, epoch)` + `tiffw.write_geotiff` into fresh temp dirs (NOT by reading committed TIFF bytes into a hasher alone; generator + writer present). Three independent runs, byte-identical across runs and MATCH to committed `dem_golden_sha256.json` / `SHA256SUMS` / on-disk fixtures: 1001=`8f37f39093d46bc6b132a36e978e614b7d9bfe1ea61053cd921f6911257fe731`; 1002a=`6a8e8238fdc7c06ef21622515481e2ec3ed998b24e7ce8fe09b9204534cb3979`; 1002b=`32e882440d7d49d3c56afeb0c31d0912b2a63409803f4d2c3347d6c66b76c781`; 1003=`b76cea2b7ab4db63281d3e2fc308fee1e06b7dfeb3096d32874187499a5f6f6e`; `generator_version`=`0`. Also `make fixtures-verify` OK; truth JSON sha `853dbab889470fb0e760f154074e59cccbbe1e1d94633cd97c409f04b8a5b9d9` matches regen. **Hold #1 DEM SHA CLEARED.** M1_W_KM still `None` / M1_W_SOURCE still `None` (PLACEHOLDER; not invented). `m1-sweep-width.md` still headed "DRAFT — NOT POSTED" (Loam Discussion #28 is a separate Loam→Waveform request, not Bedrock posting that draft). PR remains draft. Licence 2300/2310/2320 = exactly `UNLICENSED (private repo; licence pending Audrey)`. Rule 5/7 re-scan on changed files: synthetic local CRS (ProjectedCSType=32767, citation "not georeferenced"); no real DEM/PII/case/hfmr/evidence; physics LOD stays PLACEHOLDER. Tests: `make test-scorer` → **31 passed, 2 xfailed**; `make test-dem` → **25 passed**; `cd sar && pytest sensegame/tests` → **56 passed, 2 xfailed**. **Verdict: PASS-with-hold (updated) 0.90.** Holds remaining: (2) M1 W PLACEHOLDER — Waveform citation + Verity co-sign before CLEAR; (3) keep draft; (4) do not post m1-sweep-width.md without Audrey. Hold (1) DEM SHA CLEARED. Verity-N pending.
- Verity-N (independent; 2026-11-05 08:28 MST (America/Denver)) PR #41 8c98804: APPROVE-with-hold (updated) 0.90. Fresh worktree /workspace/sensecrew/wt/verity-n-41-dem (not verity-pr41-dem). Independently regenerated DEM goldens 3× via generate+write_geotiff into /tmp/verity-n-41-dem-r{1,2,3}; all MATCH D digests (1001=8f37f390…7fe731; 1002a=6a8e8238…cb3979; 1002b=32e88244…76c781; 1003=b76cea2b…5f6f6e; generator_version=0). Hold #1 DEM SHA CLEARED. Keep #2–4 (M1 W PLACEHOLDER; draft; no m1-sweep-width.md post without Audrey). dem 25 passed; sensegame 56 passed / 2 xfailed. Points to R40 + this LEDGER entry.

- R41 (2026-11-05 ~08:30 MST) Verity-D PR #42 c6d920d (Fusion 2371 provisional combine.py + calibrated anomaly hint layer, draft → main, branch sensecrew/fusion/combine-2371): Independent Verity-D review. Assigned head was `a9c01be1299c5062717a2d982294b032241bf87e`; Fusion had since merged #41 tip `8c98804` → **current tip checked** `c6d920d41b3476a94aad628a5710d9cbbf183e45` (worktree `/workspace/sensecrew/wt/verity-pr42`, detached). Parents: a9c01be + 8c98804. Fusion tree unchanged across merge (Makefile only: Bedrock targets kept, fusion targets appended with `FUSION_SEED` default 1002). **Rule 5/7 CLEAR** on PR fusion modules: synthetic-only path guard (`fixtures/*synthetic*`); geo keys rejected; no TerraTorch/TerraMesh/Ultralytics/ISRID/LUCAS/EDNA/raw realdata/fusion.py imports; `FUSION_EMBEDDINGS=0`; quarantined path parts refused; forbidden paths not opened (case/, hfmr/, dossier.py, evidence/, public_records*, docs/case-files/). **Determinism:** seed 1002 ×3 → byte-identical `fusion_1002.json` sha256 `3b987b05ae2e5c748ad2d7a20a2c5bea99927de229c4a2982b6e94d9600dbfe4` and `uncertainty_map_1002.tif` sha256 `09baac2b2a82a44c14db10c4ccf1da7f9e0bdd5702afaa03b48b6425c3eb411a`; `make fusion-replay` OK. **ECE/Brier:** ECE_GATE=0.05 / ECE_BINS=15 present; observed ece_holdout≈0.01034456, brier_holdout≈0.03388725 (match PR claim 0.0103 / 0.0339); writer refuses unbanded scores. **Deviations** (anomaly.py not combine.py; JSON fixtures not .npz; ECOD only / no HDBSCAN; registry 2370/2371 provisional) match code/docs. **LEDGER+CHANGELOG** same-commit on a9c01be. **Registry:** 2370/2371 ABSENT (HOLD until CLEAR — expected; not prematurely added). 2300/2310/2320 present with UNLICENSED via #41 merge. **Tests @ c6d920d:** `make fusion-test` → **25 passed**; `pytest sensegame/` → **81 passed, 2 xfailed** (M1 W PLACEHOLDER). Draft remains draft. Fusion-N APPROVE recorded on sensecrew/ledger for a9c01be and c6d920d (no GitHub APPROVE event required of Verity). Rebase onto 8c98804: **already done** via merge c6d920d. **Verdict: PASS-with-hold 0.90.** Holds: (1) merge-after-#41 (#41 still open draft); (2) registry 2370/2371 until CLEAR; (3) keep draft; (4) inherit #41 hold — M1 W PLACEHOLDER (Waveform citation + Verity co-sign). Verity-N pending.
- R42 (2026-11-05 ~08:33 MST) Verity-D PR #41 8c98804 (Bedrock NEW-01/2310 + NEW-03/2320, draft → main): **Follow-up CHANGES-REQUIRED** after language-scan failure at the same tip already cleared for DEM under R40. Worktree evidence `/workspace/sensecrew/wt/verity-n-41-dem` @ exact head `8c988040e0924be3e5f35da5a2d269f68bee01e1`. Command: `python3 -m pytest sar/test_language_scan.py -q --tb=line` → **FAILED** `RepositoryHasNoDeferredWorkLanguage::test_no_live_line_carries_the_vocabulary` — **6 hits** in `sensegame/tests/test_scorer_golden.py` carrying PLACEHOLDER vocabulary (lines **4, 27, 186, 189, 194, 203**); **15 passed, 1 failed**. Hits name the intentional M1-W xfail / uncited-W shape (do not invent W), but live lines still trip the anti-scaffolding vocabulary enforcer. **Required fix (either):** (a) reword those lines without inventing a numeric W and without deferred-work vocabulary, **or** (b) add a `language_scan.py` RULE describing the M1-W xfail shape with its reason (same pattern as the two existing rules) — **do not** add an exemption list (there is none; the first would normalize exemptions). **DEM hold #1 stays CLEARED** (R40/Verity-N independent regen). **Holds 2–4 remain** (M1 W PLACEHOLDER — Waveform citation + Verity co-sign; keep draft; do not post m1-sweep-width.md without Audrey). Language-scan failure is an **additional merge blocker** beyond those holds. Confidence 0.90. COMMENT on PR #41 (no APPROVE / REQUEST_CHANGES event). Verity-N not started by Verity-D.

- Verity-N (independent; 2026-11-05 08:33 MST (America/Denver)) PR #42 c6d920d: APPROVE-with-hold 0.90. Fresh worktree /workspace/sensecrew/wt/verity-n-42 (not verity-pr42). Tip confirmed still c6d920d. Rule 5/7 CLEAR; seed 1002 ×3 byte-identical (json 3b987b05…0dbfe4; tif 09baac2b…eb411a); fusion-replay OK; ECE≈0.01034456 / Brier≈0.03388725; registry 2370/2371 ABSENT; fusion-test 25 passed; sensegame 81 passed / 2 xfailed; M1_W_KM None. Same four holds as R41 (merge-after-#41; registry 2370/2371; keep draft; inherit M1 W PLACEHOLDER). Note: GitHub isDraft=false at N time (hold #3 still applies). Points to R41 + this LEDGER entry.

- R43 (2026-11-05 ~08:35 MST) Verity-D PR #41 dafed87 (Bedrock NEW-01/2310 + NEW-03/2320, draft → main, branch sensecrew/bedrock/new-01-cleanscorer): Re-review after R42 language-scan CHANGES-REQUIRED. `gh pr view 41 --json headRefOid` → `dafed8713cb081ee4a8e6be6a4d496318402251c` (matches claim). Fresh worktree `/workspace/sensecrew/wt/verity-pr41-lang` (detached at exact tip). Diff 8c98804..dafed87: 2 files +15/−6 — `sar/sensegame/tests/test_scorer_golden.py` (6 PLACEHOLDER strings reworded to "M1 W unset until citation" / "awaiting cited sweep width from Waveform": module docstring, M1 comment, section header, `_require_m1_w` fail message, 2× xfail reason) + `docs/sensecrew/bedrock/LEDGER.md` (+8 append-only). No surprises; no code/logic/fixture/registry change. `python3 -m pytest sar/test_language_scan.py -q` → **16 passed** (0 deferred-work hits). M1: `M1_W_KM = None` / `M1_W_SOURCE = None` are the only assignments in sar/; no numeric W_km anywhere; both M1 tests still `xfail(strict=True)`; `_require_m1_w` still fails on None. Tests: `cd sar && python3 -m pytest -q test_language_scan.py sensegame/tests` → **72 passed, 2 xfailed** (matches Bedrock claim). DEM goldens: `dem_golden_sha256.json` (sensegame + docs) unchanged vs 8c98804; digests still 1001=8f37f390…fe731, 1002a=6a8e8238…3979, 1002b=32e88244…c781, 1003=b76cea2b…f6e — DEM hold #1 stays CLEAR. Rule 5/7 on delta CLEAR (no imports, no I/O; forbidden names appear only in the LEDGER prohibition note). Draft: GitHub showed isDraft=false (ReadyForReviewEvent 08:30:52 MST by midnghtsapphire); Strata re-drafted; confirmed **isDraft=true** at post time. m1-sweep-width.md unchanged since 8e745c6, still unposted. **Verdict: PASS-with-hold (updated) 0.90.** R42 language-scan blocker **CLEARED**. Holds remaining: (2) M1 W unset / uncited — Waveform citation + Verity co-sign before CLEAR; (3) keep draft; (4) do not post m1-sweep-width.md without Audrey. Hold (1) DEM SHA CLEAR (R40). Verity-N not started.
- Verity-N (independent; 2026-11-05 08:36 MST (America/Denver)) PR #41 dafed87: APPROVE-with-hold (updated) 0.90. Fresh worktree /workspace/sensecrew/wt/verity-n-41-lang (not verity-pr41-lang). language_scan 16 passed; sensegame+scan 72 passed / 2 xfailed; 0 PLACEHOLDER hits in sensegame/tests; M1_W_KM/M1_W_SOURCE still None; DEM digests unchanged vs R40; isDraft=true; m1-sweep-width.md still NOT POSTED. R42 language-scan CLEAR; keep holds 2–4. Points to R43 + this LEDGER entry.
- R44 (2026-11-05 ~08:40 MST) Verity-D PR #42 ad83cba (Fusion 2371 provisional, delta after merge of #41 tip dafed87): `gh pr view 42 --json headRefOid` → `ad83cbab1fa593ec83327273f0c4563175805825` (matches claim; isDraft=true, OPEN). Fresh worktree `/workspace/sensecrew/wt/verity-pr42-delta` (detached at exact tip). Merge commit (not rebase): parents `c6d920d` + `dafed87`. Diff c6d920d..ad83cba: 2 files +15/−6 (`sar/sensegame/tests/test_scorer_golden.py` M1 wording, `docs/sensecrew/bedrock/LEDGER.md` append) — **byte-identical** to `git diff 8c98804 dafed87`; `git merge-tree --write-tree c6d920d dafed87` = `9ed952c7…` = ad83cba tree (clean auto-merge, no hand edits). **Fusion files unchanged** (0 paths under sensegame/fusion, Makefile untouched); Rule 5/7 N/A (no fusion file touched). Tests @ ad83cba: `make fusion-test` → **25 passed**; `pytest sensegame` → **81 passed, 2 xfailed**; `test_language_scan.py` → **16 passed** (0 PLACEHOLDER in sensegame/). Determinism: `make fusion` + `make fusion-replay` ×2 seed 1002 → `replay OK seed=1002`; json `3b987b05…0dbfe4`, tif `09baac2b…eb411a` — identical to R41 @ c6d920d. Registry: 2370/2371 ABSENT (only 2300/2310/2320). Note (pre-existing, not new): `test_registry_coverage.py` fails 1 test because `sensegame/fusion/tests/test_fusion.py` has no registry component — same failure at c6d920d, passes at dafed87; this is the direct consequence of hold (2) and clears when 2370/2371 are registered. M1_W_KM/M1_W_SOURCE still None. Fusion-N re-APPROVE (ad83cba) present on sensecrew/ledger `74b5785`. **Verdict: PASS-with-hold (delta) 0.90.** Holds reaffirmed: (1) merge-after-#41 — #41 still OPEN/draft @ dafed87; merging #41 tip into #42 does NOT clear landing order on main; (2) registry 2370/2371 until CLEAR (still absent; registry-coverage test red until then); (3) keep draft; (4) inherit #41 M1 W unset/uncited (Waveform citation + Verity co-sign). Verity-N not started.

- Verity-N (independent; 2026-11-05 08:42 MST (America/Denver)) PR #42 ad83cba: APPROVE-with-hold (delta) 0.90. Fresh worktree /workspace/sensecrew/wt/verity-n-42-delta (not verity-pr42-delta). Tip confirmed still ad83cba; isDraft=true. Parents c6d920d+dafed87; fusion path diff empty; merge-tree tree 9ed952c7 matches. fusion-test 25; sensegame 81/2 xfail; language_scan 16; seed 1002 replay OK (json 3b987b05…0dbfe4; tif 09baac2b…eb411a). Registry 2370/2371 ABSENT; M1_W_KM None. Same four holds as R44. Points to R44 + this LEDGER entry.

- R45 (2026-11-05 ~11:50 MST America/Denver) Discussion #44 Verity-D+N concurrence (comment, not PR tip): Fusion Option A open questions. COMMENT https://github.com/midnghtsapphire/forensicfinders/discussions/44#discussioncomment-19424711. (1) fusion/synth.py procedural/synth stand-in ACCEPTABLE-with-conditions 0.86 — label stand-in only; no realdata/fusion.py; does not satisfy Quartz 2360; does NOT alone lift Option A to ≥0.80. (2) deprecated dem_path/spectral_path raise-before-I/O Rule-7 CLEAR 0.90; case-judgement LOW residual 0.84 if raise-before-I/O + synthetic=False raises + seed+config happy-path + README leads synthetic. (3) sam.py/nnls_unmix.py YES audit before game-path 0.88 — R10 #19 grep PASS ≠ CLEAN; only consensus.py CLEAN @ f3c8037; out of Option A scope. Net: no Option A rescore; freeze + #37/#41/#42 draft holds unchanged. Forbidden paths not opened.
