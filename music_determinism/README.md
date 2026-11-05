# ACE-Step 1.5 determinism test — status: BLOCKED (hardware only; 2026-11-05 07:30 MST)
Run: `make music-determinism SEED=1001` (or `python3 run_determinism.py --seed 1001`). Exit 3 = BLOCKED, 0 = PASS, 1 = FAIL.
Plan: checkpoint `acestep-v15-turbo` (HF ACE-Step/Ace-Step1.5) + `vae`, DiT-only (thinking=False, no 5Hz LM), no LoRA, repo pinned at ace-step/ACE-Step-1.5@ca1e85fe. Runs A,B (same seed) and C (seed+1), 12 s WAV. PASS = sha256(PCM A)==sha256(PCM B) and !=C. Records max |A−B|, model sha256s, pip freeze, device, deterministic flags.
## Why BLOCKED (not faked; no weights downloaded, nothing generated)
1. **Policy / licence (CLEARED by Verity R26):** Qwen3-Embedding-0.6B text encoder is Apache-2.0, ungated, SUPPORTED 0.80 (model-card metadata). R26 authorizes `ALLOW_QWEN3_EMBED=1` for a real run when hardware is ready. Still forbidden: Chinese New Year LoRA; 1.7B LM; unverified Qwen3 base/LM planner models. Gate kept as explicit opt-in.
2. **Hardware (active block):** no CUDA GPU; MemAvailable ~4.6 GB (< 12 GB CPU estimate); disk ~16.3 GB free; Python 3.13.5 (repo needs 3.11–3.12). The 12 GB RAM threshold for CPU is my own estimate (unverified).
3. `make` isn't installed on this box, so the target was verified via its underlying `python3 run_determinism.py` call only.
See RESULT_BLOCKED.json. Music remains PARKED on hardware.
