# DRAFT note — NVIDIA PhysicsNeMo as a later ONNX surrogate candidate (NOT POSTED)
Status: proposal only, no dependency added. Author: Bedrock. Date: 2026-11-04.

| claim | confidence | evidence (checked 2026-11-04) |
|---|---|---|
| PhysicsNeMo is licensed **Apache-2.0** | **0.97** | GitHub API `NVIDIA/physicsnemo` → `spdx_id: Apache-2.0`; `LICENSE.txt` on `main` is Apache License 2.0; `pyproject.toml` `license = "Apache-2.0"`; NVIDIA developer page says Apache 2.0. (Remaining doubt: third-party deps and any pretrained weights/datasets carry their own licences — check each before use.) |
| It can export models to ONNX (`physicsnemo.deploy.onnx.export_to_onnx_stream`) | 0.85 | NVIDIA docs, PhysicsNeMo 25.11 "Deploy" page. API may change between releases; re-check at adoption time. |
| A surrogate would be useful for M1–M3 now | 0.3 | Current 2310 (NEW-01) maths is closed form and cheap; 2320 (NEW-03) is integer and deterministic. A surrogate only pays off for later heavy forward models (e.g. GPR/wave physics owned by science pairs). |

**Position**
- The **deterministic solver stays authoritative**. 2310 (NEW-01) CleanScorer (closed-form, stdlib `math`) and 2320 (NEW-03) fixtures (SHA-256 exact) are the source of truth. A surrogate may only *preview* or speed up a result, and the game must label it as a surrogate. Scoring, LO checks and goldens never use surrogate output.
- A surrogate needs: its own Verity validation against the solver on seeded cases; a stated error budget (it is never held to the 1e-12/1e-9 solver tolerances); a fallback to the solver; and pinned ONNX opset/runtime versions.
- Licence hygiene: Apache-2.0 needs the LICENSE and NOTICE kept with redistribution. Torch, ONNX Runtime and any weights or datasets must be checked one by one. Nothing GPL goes in the game path.

**Ask:** none now. Revisit when a science pair has a forward model that is too slow for the headless sim.
Sources: https://github.com/NVIDIA/physicsnemo/blob/main/LICENSE.txt · https://docs.nvidia.com/physicsnemo/25.11/physicsnemo/api/physicsnemo.deploy.html · https://developer.nvidia.com/PhysicsNeMo
