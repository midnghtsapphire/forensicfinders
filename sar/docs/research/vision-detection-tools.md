# Optional vision detection for camera and drone frames

**Registry ID: 2100** · **Status: PROTOTYPE / RESEARCH** · No code yet. No claimed results.

**Rule:** the core stays rule-based (timestamps, SHA-256, timeline merge in 1911–1913). Any detector is an
**optional add-on, off by default**. Prefer a small model that runs locally. Its output is a *candidate for a
human to review*, logged with model name and version, never an identification.

Audrey's pasted text was game-development content. The only part that transfers is the general idea of
retraining a stock detector on domain imagery (MDPI paper below). Game-specific material is not used.

## Tools (checked 2026-10-21)
| Tool | License | Activity | Use here |
|---|---|---|---|
| OpenCV template matching (`cv2.matchTemplate`) — <https://github.com/opencv/opencv> | Apache-2.0 | pushed 2026-10-21 | Rule-like first step: match a known item photo (a backpack, a jacket colour patch) in frames from 1911/1912/1913. No training |
| Ultralytics YOLO — <https://github.com/ultralytics/ultralytics> | **AGPL-3.0** | pushed 2026-10-21 | Small models (e.g. "n"/"s" sizes) run on CPU. **AGPL note:** using it in a networked service obliges releasing that service's source under AGPL unless an Ultralytics Enterprise licence is bought. That conflicts with keeping this repo private and proprietary (1400). Keep it a separate, optional process, or license it |
| OpenTrafficCam — <https://github.com/OpenTrafficCam>: **OTVision** ("Detect and track objects (road users) in videos") and **OTAnalytics** ("traffic analysis on trajectories of road users") | GPL-3.0 (both) | both pushed 2026-10-21; 37 and 24 stars | Tracking vehicles and people on *public* traffic-camera video (1911) to build sighting timelines for 1913. It is built for road users and has nothing SAR-specific. GPL-3.0 means: run it as a separate tool and pass files, rather than linking it into proprietary code |
| `viaverde-traffic` 0.1.1 — <https://pypi.org/project/viaverde-traffic/> (repo `mpoboas/viaverde-traffic-api`) | MIT | 2 releases, last 2026-08-09; 1 star | Real but tiny: a Python wrapper for Via Verde (Portugal) traffic-camera images. It could be one more public source in `cameras/sources.json` for Portuguese cases. Single maintainer; treat as unmaintained-risk |

Transferable reference: Jung M, Yang H, Min K (2021). *Improving Deep Object Detection Algorithms for Game Scenes.*
Electronics 10(20):2527. doi:[10.3390/electronics10202527](https://doi.org/10.3390/electronics10202527).
It concerns game scenes, not SAR. The transferable point is domain-adapting a stock detector with domain-specific
training images.

## Public SAR drone datasets (verified papers)
- **HERIDAL** — Božić-Štulić D, Marušić Ž, Gotovac S (2019). *Deep Learning Approach in Aerial Imagery for Supporting
  Land Search and Rescue Missions.* Int J Comput Vis 127:1256–1278. doi:[10.1007/s11263-019-01177-1](https://doi.org/10.1007/s11263-019-01177-1).
  It is a dataset of aerial images of people in wilderness terrain, from the University of Split. The project
  download page (ipsar.fesb.unist.hr) did not respond on 2026-10-21. Check the licence terms there before use.
- **SARD** — Sambolek S, Ivasic-Kos M (2021). *Automatic Person Detection in Search and Rescue Operations Using Deep
  CNN Detectors.* IEEE Access. doi:[10.1109/ACCESS.2021.3063681](https://doi.org/10.1109/ACCESS.2021.3063681).
  It introduces the SARD drone dataset of people in SAR-like poses and settings. Check the dataset's licence before training.

Both datasets are about *people*. Personal *items* (2070) have no public set we found, which is why a labelling workflow is needed.

## Labelling workflow for a custom item detector
1. **Tool:** CVAT (<https://github.com/cvat-ai/cvat>, MIT) or Label Studio (<https://github.com/HumanSignal/label-studio>,
   Apache-2.0), self-hosted on the box so frames never leave it.
2. **Data:** our own staged test-strip photos and drone passes (2070 roadmap), not case imagery. Classes:
   backpack, jacket/clothing, shoe, bag, bright fabric. Two labellers on a 10% overlap to measure agreement.
3. **Splits** by *site and flight*, not by frame, so neighbouring frames don't leak (the same issue fixed in 1410).
4. **Export** in YOLO or COCO format and store only labels plus file hashes in the repo; images stay out of git.
5. **Train** a small model offline. Report precision/recall on held-out sites only. Keep a "no detector" baseline.

## Wiring (when built)
`cameras/` frames (1911/1912) → optional `detect` step (flag `--detector none|template|yolo`, default `none`)
→ candidate boxes with model id, confidence and frame SHA-256 → 1913 timeline as `kind: "detector_candidate"`.
Nothing is acted on without human review.
