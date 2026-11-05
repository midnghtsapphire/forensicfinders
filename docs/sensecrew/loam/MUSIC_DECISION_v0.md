# Loam — Music stack decision v0 (entertainment skins)
**Date:** 2026-11-04 20:30 MST (UTC-7) · **Owner:** Loam (Loam-D / Loam-N) · **Priority:** below the training sim; skins never change physics. **Licence:** UNLICENSED (private repo; licence pending Audrey)
**Source:** `/workspace/prompt-hoard/frontier/game-genai-stack-vetted-2026-11-04.md` (table rows 26–28; "Prototype-only / don't ship" list, line 67). Model facts are taken from that vetting and were not re-checked here.

## Scale
I could not find RulesSteward's confidence scale in `midnghtsapphire/revvel-standards`: a code search for "RulesSteward" returned nothing. The "confidence" search only found other teams' frameworks (e.g. `fraud-signal-verification-fleet/docs/CONFIDENCE_FRAMEWORK.md`), which I didn't adopt. So this uses a **transparent weighted rubric**: each criterion is scored 0–5, and Score = Σ(weight × score)/5, out of 100.

| Criterion | Weight |
|---|---|
| Licence fit | 25 |
| Commercial use | 20 |
| Determinism / reproducibility | 20 |
| Offline / local | 15 |
| Quality (music) | 10 |
| Cost (VRAM / hardware) | 10 |

## Exclusions (not shippable)
- MusicGen, AudioGen: non-commercial per the guide → prototype-only.
- Stable Audio 3 Small-SFX: **not excluded, but cannot ship** until its revenue-cap licence text is read (it is gated and unverified). It is also an SFX model, not a music model.

## Scores
| Option | Licence | Commercial | Determinism | Offline | Quality | Cost | **Total** |
|---|---|---|---|---|---|---|---|
| **ACE-Step 1.5** (MIT) | 5 | 5 | 4 (seeded generation; bit-exactness across GPUs UNVERIFIED) | 5 | 4 (UNVERIFIED) | 4 (~8 GB+) | **92** |
| Magenta RealTime (Apache code / CC-BY-4.0 weights) | 4 (attribution needed) | 5 | 3 (live streaming is harder to replay) | 4 (TPU/GPU ~16 GB) | 4 | 3 | **78** |
| Stable Audio 3 Small-SFX (Community, cap unverified) | 2 | 2 | 4 | 5 | 3 | 5 | **65** (blocked) |
| MusicGen | — | — | — | — | — | — | excluded (NC) |

## Decision
**ACE-Step 1.5** is the music stack for the entertainment skins.
- **Reproducibility:** tracks are generated offline, with prompt, seed, model hash and settings recorded in `audio/manifest.jsonl`. Rendered audio is committed with a sha256, and the game ships the baked files, never live generation. That makes builds byte-identical, consistent with hard rule 3.
- **Runner-up:** Magenta RealTime, for a later adaptive-music skin only, with the CC-BY-4.0 credit in the in-game credits. Note that v2 (Jun 2026) exists and hasn't been vetted yet.
- **SFX:** Stable Audio stays off until Verity reads the licence.

## Open
- Verity should confirm ACE-Step 1.5's licence on HF (MIT per the vetting).
- Run a seed-repeatability test on our hardware: same seed → same sha256.
- Quality listening test: one track per skin.

Loam-N APPROVE

---
## Addendum A — re-score on the interim confidence scale (2026-11-04 20:34 MST)
**Status: ACE-Step accepted provisionally pending Verity licence check + determinism test**

**Scale (per Strata):** revvel-standards `fraud-signal-verification-fleet/docs/CONFIDENCE_FRAMEWORK.md` with code `src/confidence.py`, read-only at blob sha256 143bfaee… (latest commit touching it: 7fff87e5). The code is pure stdlib and deterministic: two runs produced byte-identical output, sha256 e0de0615…. It was run unmodified from a temp copy, not vendored. The config values were transcribed from the framework doc because its yaml isn't in this repo.

**Mapping (Loam's, transparent):**
- Each option's claim is "licence-clear for commercial shipping". A second claim is "byte-reproducible from a seed".
- Tier 4 = the HF licence field as read in the vetting doc; tier 2 = the guide's claim only.
- Stage: `investigated` = team-vetted but not Verity-confirmed (cap 0.55); `unknowable` = gated or unread licence text (cap 0.20).
- The framework's legal stages are an analogy here. A Verity confirmation would be the next stage up.

Files: `music_confidence/case.json`, `run.py`, `result.tsv`. Run with `CONFIDENCE_PY=<path> python3 docs/sensecrew/loam/music_confidence/run.py`.

| Claim | Confidence | Band |
|---|---|---|
| ACE-Step 1.5 licence-clear | 0.55 | SUPPORTED (stage-capped) |
| Magenta RealTime licence-clear | 0.55 | SUPPORTED (stage-capped) |
| Stable Audio 3 Small-SFX licence-clear | 0.20 | UNSUBSTANTIATED |
| MusicGen licence-clear | 0.00 | UNSUBSTANTIATED (contradicted: NC) |
| ACE-Step deterministic | 0.00 | UNSUBSTANTIATED (no test yet) |
| Magenta RT deterministic | 0.00 | UNSUBSTANTIATED (no test yet) |

**Effect on the decision:** the pick is unchanged. ACE-Step and Magenta tie at SUPPORTED on licence, so the tie is broken by the original rubric (92 vs 78; it is kept above, unedited). Neither option reaches SUBSTANTIATED, and neither has any determinism evidence. That is why the acceptance is **provisional**. Exit criteria: Verity reads the licence (moves to a higher stage), and a same-seed same-sha256 test passes on our hardware.

Loam-N APPROVE (addendum)
