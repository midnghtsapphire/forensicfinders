# ACE-Step 1.5 determinism test — status: BLOCKED (2026-11-04 20:38 MST)
Run: `make music-determinism SEED=1001` (or `python3 run_determinism.py --seed 1001`). Exit 3 = BLOCKED, 0 = PASS, 1 = FAIL.
Plan: checkpoint `acestep-v15-turbo` (HF ACE-Step/Ace-Step1.5) + `vae`, DiT-only (thinking=False, no 5Hz LM), no LoRA, repo pinned at ace-step/ACE-Step-1.5@ca1e85fe. Runs A,B (same seed) and C (seed+1), 12 s WAV. PASS = sha256(PCM A)==sha256(PCM B) and !=C. Records max |A−B|, model sha256s, pip freeze, device, deterministic flags.
## Why BLOCKED (not faked; no weights downloaded, nothing generated)
1. **Policy:** the HF repo file list (read this session) shows the pipeline's text encoder is `Qwen3-Embedding-0.6B/model.safetensors` (1.19 GB). That is a Qwen3-based model, which Verity's ruling disallows as unverified. Without it there's no text conditioning. This needs a Verity ruling, after which `ALLOW_QWEN3_EMBED=1` lifts the gate.
2. **Hardware:** no CUDA GPU; MemAvailable 4.6 GB; disk 16.3 GB free; Python 3.13.5 (repo needs 3.11–3.12). The 12 GB RAM threshold for CPU is my own estimate (unverified).
3. `make` isn't installed on this box, so the target was verified via its underlying `python3 run_determinism.py` call only.
See RESULT_BLOCKED.json.
