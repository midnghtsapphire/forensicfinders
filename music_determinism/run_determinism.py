#!/usr/bin/env python3
"""ACE-Step 1.5 determinism test (Loam). DiT-only (no 5Hz LM: that is Qwen3-based and still disallowed), no LoRA.
Runs A(seed), B(seed), C(seed+1); writes WAV; compares sha256 of raw PCM; records max |diff|.
Pre-flight refuses to run (exit 3 = BLOCKED) when gates fail. Never fakes output.

Verity R26 (2026-11-05): Qwen3-Embedding-0.6B is Apache-2.0 / ungated / SUPPORTED 0.80.
ALLOW_QWEN3_EMBED=1 is authorized for a real run when hardware allows (opt-in gate retained).
Still forbidden: Chinese New Year LoRA; 1.7B LM; unverified Qwen3 base/LM planner models.
"""
import argparse, hashlib, json, os, platform, shutil, subprocess, sys
REPO_COMMIT = "ca1e85fe9430179831e6bc6be790c332190a3866"   # ace-step/ACE-Step-1.5 main, MIT
ALLOWED_FILES = ["acestep-v15-turbo/*", "vae/*", "config.json"]  # never acestep-5Hz-lm-1.7B, never LoRA
QWEN3_EMBED = "Qwen3-Embedding-0.6B/*"   # required text encoder; R26 clears Apache-2.0 licence (opt-in via ALLOW_QWEN3_EMBED)

def preflight(a):
    reasons = []
    # R26 cleared the embedding licence; keep explicit opt-in so a run is intentional.
    if os.environ.get("ALLOW_QWEN3_EMBED") != "1":
        reasons.append(
            "OPT-IN: Qwen3-Embedding-0.6B licence CLEARED by Verity R26 (Apache-2.0, ungated, SUPPORTED 0.80). "
            "Set ALLOW_QWEN3_EMBED=1 to proceed when hardware allows. Still forbidden: CNY LoRA; 1.7B LM; unverified Qwen3 base/LM planner."
        )
    gpu = shutil.which("nvidia-smi") is not None
    mem_avail_gb = int(open("/proc/meminfo").read().split("MemAvailable:")[1].split()[0]) / 1e6
    disk_free_gb = shutil.disk_usage(a.out).free / 1e9
    if not gpu and mem_avail_gb < 12:
        reasons.append(f"HARDWARE: no CUDA GPU and MemAvailable {mem_avail_gb:.1f} GB < 12 GB needed for CPU (DiT 4.8 GB + encoder 1.2 GB + VAE 0.3 GB, fp32 working set).")
    if disk_free_gb < 15:
        reasons.append(f"DISK: {disk_free_gb:.1f} GB free < 15 GB (weights ~6.3 GB + torch/venv).")
    return reasons, {"gpu": gpu, "mem_avail_gb": round(mem_avail_gb, 1), "disk_free_gb": round(disk_free_gb, 1), "cpu_count": os.cpu_count(), "platform": platform.platform(), "python": platform.python_version()}

def pcm_sha(path):
    import soundfile as sf, numpy as np
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    return hashlib.sha256(x.tobytes()).hexdigest(), x, sr

def main():
    p = argparse.ArgumentParser(); p.add_argument("--seed", type=int, default=1001); p.add_argument("--duration", type=float, default=12)
    p.add_argument("--device", default="auto"); p.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
    p.add_argument("--ckpt", default=os.path.expanduser("~/.cache/loam_acestep/checkpoints")); a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    reasons, hw = preflight(a)
    res = {"status": None, "seed": a.seed, "duration_s": a.duration, "repo_commit": REPO_COMMIT, "hardware": hw,
           "policy": {"qwen3_embedding": "CLEARED by Verity R26 (Apache-2.0). ALLOW_QWEN3_EMBED=1 authorized when hardware ready."}}
    if reasons:
        res.update(status="BLOCKED", reasons=reasons)
        json.dump(res, open(os.path.join(a.out, "result.json"), "w"), indent=2); print(json.dumps(res, indent=2)); sys.exit(3)
    import torch, numpy as np
    from huggingface_hub import snapshot_download
    snapshot_download("ACE-Step/Ace-Step1.5", local_dir=a.ckpt, allow_patterns=ALLOWED_FILES + [QWEN3_EMBED])
    torch.use_deterministic_algorithms(True); torch.backends.cudnn.benchmark = False
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    dev = ("cuda" if torch.cuda.is_available() else "cpu") if a.device == "auto" else a.device
    from acestep.handler import AceStepHandler
    from acestep.inference import GenerationParams, GenerationConfig, generate_music
    h = AceStepHandler(); h.initialize_service(project_root=os.path.dirname(a.ckpt), config_path="acestep-v15-turbo", device=dev)
    runs = {}
    for tag, seed in (("A", a.seed), ("B", a.seed), ("C", a.seed + 1)):
        prm = GenerationParams(caption="calm ambient synth pad, slow, minimal", duration=a.duration, seed=seed, thinking=False, use_cot_metas=False)
        cfg = GenerationConfig(batch_size=1, use_random_seed=False, seeds=[seed], audio_format="wav")
        r = generate_music(h, None, prm, cfg, save_dir=os.path.join(a.out, tag))
        if not r.success: res.update(status="ERROR", error=str(r.error)); break
        sha, x, sr = pcm_sha(r.audios[0]["path"]); runs[tag] = {"seed": seed, "pcm_sha256": sha, "path": r.audios[0]["path"], "sr": sr}; runs[tag]["_x"] = x
    if res["status"] is None:
        d = float(np.max(np.abs(runs["A"]["_x"] - runs["B"]["_x"]))) if runs["A"]["_x"].shape == runs["B"]["_x"].shape else None
        res["status"] = "PASS" if runs["A"]["pcm_sha256"] == runs["B"]["pcm_sha256"] and runs["A"]["pcm_sha256"] != runs["C"]["pcm_sha256"] else "FAIL"
        res["max_abs_diff_A_B"] = d
    for v in runs.values(): v.pop("_x", None)
    res.update(runs=runs, device=dev, torch=torch.__version__, deterministic_algorithms=True,
               model_sha256={f: hashlib.sha256(open(os.path.join(a.ckpt, f), "rb").read()).hexdigest() for f in ["acestep-v15-turbo/model.safetensors", "vae/diffusion_pytorch_model.safetensors", "Qwen3-Embedding-0.6B/model.safetensors"]},
               pip_freeze=subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout.splitlines())
    json.dump(res, open(os.path.join(a.out, "result.json"), "w"), indent=2); print(res["status"]); sys.exit(0 if res["status"] == "PASS" else 1)
if __name__ == "__main__": main()
