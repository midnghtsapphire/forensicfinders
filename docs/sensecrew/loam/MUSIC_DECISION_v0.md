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
