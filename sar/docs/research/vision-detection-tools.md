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

## Method references (adjacent field, not SAR; checked 2026-10-21)

These come from atomic-resolution electron microscopy, not search and rescue. They are kept only as **method references** for how `sar/vision/template.py` (2110) finds small, low-contrast blobs in noisy frames. None of them is evidence that the methods work on drone or camera footage.

- **Hussaini, Z., Lin, P. A., Natarajan, B., Zhu, W., Sharma, R. (2018).** *Determination of atomic positions from time resolved high resolution transmission electron microscopy images.* Ultramicroscopy 186:139–145. doi:[10.1016/j.ultramic.2017.12.018](https://doi.org/10.1016/j.ultramic.2017.12.018) (PMC11305480). Code: [usnistgov/tem_analysis](https://github.com/usnistgov/tem_analysis) (C++, archived, last push 2017; NIST public-domain notice, 17 USC 105). Its Wiener deconvolution → template matching → connected-component centroids → Delaunay pipeline is the closest published analogue of the template baseline.
- **Hofer, C. et al. (2021).** *Atom-by-atom chemical identification from scanning transmission electron microscopy images in presence of noise and residual aberrations.* Ultramicroscopy 227:113292. doi:[10.1016/j.ultramic.2021.113292](https://doi.org/10.1016/j.ultramic.2021.113292).
- **Lin, R. et al. (2023).** *A Multiscale Deep-Learning Model for Atom Identification from Low-Signal-to-Noise-Ratio Transmission Electron Microscopy Images.* Small Science 3(8):2300031. doi:[10.1002/smsc.202300031](https://doi.org/10.1002/smsc.202300031).
- **Ma et al. (2025).** *Deep learning-based workflow for atomic image denoising and chemical identification.* Chinese Journal of Structural Chemistry 44(5):100572. doi:[10.1016/j.cjsc.2025.100572](https://doi.org/10.1016/j.cjsc.2025.100572).
- **Ayyubi, Sultanov, Buban, Klie (2025).** *Unsupervised Machine Learning for Atomic-Resolution S(TEM) Image Analysis and Management.* Microscopy and Microanalysis 31 (Suppl 1), conference abstract. doi:[10.1093/mam/ozaf048.1072](https://doi.org/10.1093/mam/ozaf048.1072).

- **Guo, Y., Kalinin, S. V., Cai, H. et al. (2021).** *Defect detection in atomic-resolution images via unsupervised learning with translational invariance.* npj Computational Materials 7:180. doi:[10.1038/s41524-021-00642-1](https://doi.org/10.1038/s41524-021-00642-1). **Unsupervised.** CC BY 4.0.
- **Ovchinnikov, O. S. et al. (2020).** *Detection of defects in atomic-resolution images of materials using cycle analysis.* Advanced Structural and Chemical Imaging 6:3. doi:[10.1186/s40679-020-00070-x](https://doi.org/10.1186/s40679-020-00070-x). Rule-based graph theory on found column centres (no training), the same idea as the Delaunay step above. CC BY 4.0.
- **Eliasson, H., Erni, R. (2024).** *Localization and segmentation of atomic columns in supported nanoparticles for fast scanning transmission electron microscopy.* npj Computational Materials 10:168. doi:[10.1038/s41524-024-01360-0](https://doi.org/10.1038/s41524-024-01360-0). Supervised U-Nets trained on simulated images. CC BY 4.0.
- **Li, K. et al. (2023).** *Single-image based deep learning for precise atomic defects identification.* arXiv:[2311.14936](https://arxiv.org/abs/2311.14936) (preprint, arXiv non-exclusive licence).
- **Barah, O. O., David, M., Joseph, M. (2025).** *Atomic-scale characterization: a review of advances in microscopy, spectroscopy, and machine learning.* Journal of Materials Science: Composites 6:6. doi:[10.1186/s42252-025-00073-x](https://doi.org/10.1186/s42252-025-00073-x). Review; proposes a framework that includes unsupervised clustering. CC BY-NC-ND 4.0. The first author's other listed work is in composites, diffusion modelling and probabilistic FEA fatigue (for example doi:[10.1088/2631-8695/ae31cc](https://doi.org/10.1088/2631-8695/ae31cc), 2026). None of it is microscopy or detection work.
- **Chen, Z. et al. (2021).** *Electron ptychography achieves atomic-resolution limits set by lattice vibrations.* Science 372:826–831. doi:[10.1126/science.abg2533](https://doi.org/10.1126/science.abg2533). This is the primary paper behind the Scientific American piece: Blaustein, A. (2021), *See the Highest-Resolution Atomic Image Ever Captured* ([article](https://www.scientificamerican.com/article/see-the-highest-resolution-atomic-image-ever-captured/), doi:[10.1038/scientificamerican082021-3mpgosuegnlfzdu5gldvxu](https://doi.org/10.1038/scientificamerican082021-3mpgosuegnlfzdu5gldvxu)). Magazine piece, background only.
- Background only: [Atomic force microscopy (Wikipedia)](https://en.wikipedia.org/wiki/Atomic_force_microscopy), CC BY-SA 4.0. It is not used for any claim.
- **Lin, R., Zhang, R., Wang, C., Yang, X.-Q., Xin, H. L. (2021).** *TEMImageNet training library and AtomSegNet deep-learning models for high-precision atom segmentation, localization, denoising, and deblurring of atomic-resolution images.* Scientific Reports 11:5386. doi:[10.1038/s41598-021-84499-w](https://doi.org/10.1038/s41598-021-84499-w) (PMC7940611; preprint arXiv:[2012.09093](https://arxiv.org/abs/2012.09093)). CC BY 4.0.
  - **Code:** [xinhuolin/AtomSegNet](https://github.com/xinhuolin/AtomSegNet), MIT licence (UCI DeepEM Lab, last push 2022).
    - It is a PyQt5 desktop app (`Code_Atom_Seg_Ui.py`) that loads pretrained U-Net/NestedUNet weights (`utils/utils.py`) for segmentation, denoising, background removal and super-resolution.
    - It then finds atom centres with skimage watershed and regionprops.
    - It pins old versions: PyTorch 1.3, torchvision 0.4, scikit-image ≤0.18.3.
  - **Data:** [TEMImageNet site](https://sites.google.com/view/temimagenet) (also at `/home`), a synthetic ADF-STEM image library with ground-truth labels for segmentation, Gaussian maps, denoising and super-resolution, plus atom coordinates. The site doesn't state a licence for the data; check the GitHub data release before any reuse.
  - **Third-party test:** [btplan/atomsegnet-edge-stability](https://github.com/btplan/atomsegnet-edge-stability) (no licence file, created 2026-05-05, 0 stars). A small experiment script set that degrades one TEM image and measures whether AtomSegNet misses or drifts more at nanoparticle edges than in the interior. Unreviewed; no results are cited here.
  - **Does it transfer to `sar/vision` (2110)? ADJACENT. Only the methods transfer, not the models or data.**
    - *Synthetic training data with exact labels:* the idea transfers. Rendering staged test items (a bag or jacket) into real background frames would give exact boxes and help bootstrap. The renderer would have to be ours, and synthetic-only training must be validated on real labelled frames (the leak-free site/flight splits in 2110). TEMImageNet images themselves are useless for drone or camera frames.
    - *Segmentation, then centroid:* AtomSegNet's mask → watershed → centroid pipeline matches the template baseline's pattern (score map → connected components → centroids). A small U-Net-style mask model could be a later optional detector behind `--detector`, off by default. Atoms are near-identical blobs on a periodic lattice, while SAR targets vary in shape, scale and occlusion, so expect much weaker results.
    - *Denoising and deblurring:* this applies only as optional preprocessing for low-light or thermal frames. It has to be tested for hallucinated detail, because a denoiser can invent a "target". Keep raw frames as the evidence of record.
    - Pretrained AtomSegNet weights are not reused (wrong domain). The code is MIT, so borrowing small pieces would be licence-compatible with attribution.
- Further atomic-imaging context (adjacent, background only):
  - Schwartz et al. (2022), *Imaging atomic-scale chemistry from fused multi-modal electron microscopy*, npj Comput Mater 8:16, doi:[10.1038/s41524-021-00692-5](https://doi.org/10.1038/s41524-021-00692-5), CC BY 4.0. Fuses modalities to raise SNR, analogous to RGB+thermal fusion.
  - Lee, Jeong, Yang (2021), *Single-atom level determination of 3-dimensional surface atomic structure via neural network-assisted atomic electron tomography*, Nat Commun 12:1962, doi:[10.1038/s41467-021-22204-1](https://doi.org/10.1038/s41467-021-22204-1), CC BY 4.0.
  - Modigunta et al. (2022), *Atomic Force Microscopy: An Advanced Imaging Technique—From Molecules to Morphologies*, in *Microscopic Techniques for the Non-Expert* (Springer), doi:[10.1007/978-3-030-99542-3_5](https://doi.org/10.1007/978-3-030-99542-3_5).
  - Yefsah (2025), *Magnifying Atomic Images*, Physics 18:152 (APS Viewpoint on ultracold-atom wave-function magnification), doi:[10.1103/Physics.18.152](https://doi.org/10.1103/Physics.18.152) ([article](https://physics.aps.org/articles/v18/152)).
  - *Atomic magnetism finally caught on camera* ([Nature Research Custom](https://www.nature.com/articles/d42473-022-00106-0)). **Sponsored content** produced for JEOL about the MARS magnetic-field-free STEM. Vendor material, background only. The `d42473-…` id has no Crossref DOI.
  - Guo et al. 2021 [PDF](https://www.nature.com/articles/s41524-021-00642-1.pdf), the same paper as above.
- More adjacent references from the AtomSegNet/TEMImageNet line (checked 2026-10-21):
  - Xin, H. L. et al. (2020). *AtomSegNet and TomoFillNet—Two Deep Learning Open-Source Apps for Superresolution Processing of Atomic Resolution Images and Missing-wedge Information Inpainting in Electron Tomograms.* Microsc Microanal 26(S2):926. doi:[10.1017/S1431927620016359](https://doi.org/10.1017/S1431927620016359). This is the ResearchGate item 343324549. Conference abstract.
  - [xinhuolin/TomoFillNet](https://github.com/xinhuolin/TomoFillNet): a tomography de-artifact app for WBP/SART reconstructions. **GPL-3.0**, so don't copy code into permissive modules.
  - [xinhuolin/TEM-ImageNet-v1.3](https://github.com/xinhuolin/TEM-ImageNet-v1.3): the TEMImageNet data release (image folders with circularMask, gaussianMask, noNoise and other labels). **No licence file**, and the README states none, so it is all rights reserved by default. Don't redistribute it or train shipped models on it without permission.
  - [minhminhminh0112/AtomSegNet-TEMImageNet-train-on-circularMask](https://github.com/minhminhminh0112/AtomSegNet-TEMImageNet-train-on-circularMask): a student-style retraining attempt (U-Net trained on circular masks, Dice evaluation). No licence. Unreviewed.
  - Liu, J. (2021). *Advances and Applications of Atomic-Resolution Scanning Transmission Electron Microscopy.* Microsc Microanal 27(5):943–995. doi:[10.1017/S1431927621012125](https://doi.org/10.1017/S1431927621012125). Review.
  - Lobato, I., Friedrich, T., Van Aert, S. (2024). *Deep convolutional neural networks to restore single-shot electron microscopy images.* npj Comput Mater 10:10. doi:[10.1038/s41524-023-01188-0](https://doi.org/10.1038/s41524-023-01188-0). CC BY 4.0. Restoration trained on simulated data; the same synthetic-to-real caveat applies.
  - Ruiz et al. (2018). *Optimization of digital image processing to determine quantum dots' height and density from atomic force microscopy.* Ultramicroscopy 184:234–241. doi:[10.1016/j.ultramic.2017.09.004](https://doi.org/10.1016/j.ultramic.2017.09.004) (PII S0304399116302546). A classical (non-learned) segmentation pipeline.
  - Matea et al. (2017). *Quantum dots in imaging, drug delivery and sensor applications.* Int J Nanomedicine 12:5421–5431. doi:[10.2147/IJN.S138624](https://doi.org/10.2147/IJN.S138624). Review, CC BY-NC 3.0. Not related to the SAR detector; recorded because it was requested.
- Picked from the reference list of Liu (2021), M&M 27(5):943–995 (adjacent):
  - Dabov, Foi, Katkovnik & Egiazarian (2007). *Image Denoising by Sparse 3-D Transform-Domain Collaborative Filtering* (BM3D). IEEE Trans Image Process 16:2080–2095. doi:[10.1109/TIP.2007.901238](https://doi.org/10.1109/TIP.2007.901238). This is the classical, non-learned denoiser to compare against before any learned denoiser is considered for low-light or thermal frames.
  - Ziatdinov et al. (2017). *Deep Learning of Atomically Resolved Scanning Transmission Electron Microscopy Images: Chemical Identification and Tracking Local Transformations.* ACS Nano 11:12742–12752. doi:[10.1021/acsnano.7b07504](https://doi.org/10.1021/acsnano.7b07504). Trained on simulated images.
  - Aguiar et al. (2019). *Decoding crystallography from high-resolution electron imaging and diffraction datasets with deep learning.* Sci Adv 5:eaaw1949. doi:[10.1126/sciadv.aaw1949](https://doi.org/10.1126/sciadv.aaw1949).
  - Xu & LeBeau (2018). *A deep convolutional neural network to analyze position averaged convergent beam electron diffraction patterns.* Ultramicroscopy 188:59–69. doi:[10.1016/j.ultramic.2018.03.004](https://doi.org/10.1016/j.ultramic.2018.03.004).
- CNN background (guides, not evidence):
  - [CS231n: Convolutional Neural Networks](https://cs231n.github.io/convolutional-networks/) (Stanford course notes; repo MIT).
  - [georgezoto/Convolutional-Neural-Networks](https://github.com/georgezoto/Convolutional-Neural-Networks): personal coursework notebooks from the Deeplearning.ai CNN course. No licence, and the course material may carry Coursera/deeplearning.ai terms.
  - [Gist by JiaxiangZheng](https://gist.github.com/JiaxiangZheng/a60cc8fe1bf6e20c1a41abc98131d518): a 2017 single-file `CNN.py`, a NumPy/TensorFlow-1 MNIST CNN demo ported from hsmyy/zhihuzhuanlan. No licence. Teaching snippet only.
- **Unverified:** [IEEE Xplore document 10906350](https://ieeexplore.ieee.org/document/10906350). The page needs JavaScript and blocked automated checks. Title, authors and DOI were not confirmed, so nothing here relies on it.

## Wiring (when built)
`cameras/` frames (1911/1912) → optional `detect` step (flag `--detector none|template|yolo`, default `none`)
→ candidate boxes with model id, confidence and frame SHA-256 → 1913 timeline as `kind: "detector_candidate"`.
Nothing is acted on without human review.
