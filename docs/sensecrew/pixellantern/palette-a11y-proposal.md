# PixelLantern: Palette & HUD Accessibility Proposal (doc only)

Status: Accepted by Strata · 2026-11-04 · Licence: UNLICENSED (private repo; licence pending Audrey) · Scope: GPR B-scans, point clouds, InSAR interferograms, soil moisture / dielectric maps.
Principle: **every pixel on screen must be traceable to a physical quantity, a stated transform, or a labelled game overlay.**

## 1. False-colour palettes

### 1.1 Palette classes (pick by data, not by taste)
| Data | Class | Default | Alternates |
|---|---|---|---|
| GPR B-scan amplitude (signed) | Diverging, centred at 0 | `vik` | `broc`, `berlin` |
| GPR envelope / |amplitude| | Sequential | `grayC` or `batlow` | `viridis`, `cividis` |
| Point cloud elevation / intensity | Sequential | `batlow` | `viridis`, `cividis` |
| InSAR wrapped phase (−π..π) | **Cyclic** (ends must match) | `romaO` | `vikO`, `bamO`, `corkO` |
| InSAR unwrapped displacement (± mm) | Diverging, centred at 0 | `vik` | `roma` |
| Soil moisture (m³/m³) / relative permittivity εr | Sequential | `davos` / `batlow` | `viridis`, `cividis` |
| Categorical labels (target classes) | Categorical | `batlowS` (≤10 classes) | — always paired with shape |

Rules: diverging maps only when the data has a meaningful midpoint (and the midpoint is pinned to it); cyclic maps only for periodic quantities — a sequential map on wrapped phase invents a false discontinuity at ±π.

### 1.2 Banned: rainbow / jet / hsv (non-cyclic use)
- Not perceptually uniform: lightness rises and falls, creating false edges/bands (e.g. at yellow, cyan) that players would learn as "targets".
- Not perceptually ordered: no intuitive "more/less" from hue alone.
- Unreadable under red–green colour-vision deficiency (~8% of men) and in greyscale.
- Enforcement: palette loader rejects any ID not in the approved registry; CI lint greps assets/shaders for `jet`, `rainbow`, `hsv`, `turbo`.

### 1.3 Scientific-honesty rules (on-screen, always)
1. **Colourbar always visible** with quantity, units and numeric range (e.g. `Phase [rad] −π … π`, `εr 1 … 40`, `Amplitude [arb., gain-corrected]`). Clipping shown via end-arrows with the clipped % of pixels.
2. **Label every exaggeration**: `GAIN: AGC 50 ns window`, `SEC gain ×k`, `Vertical exaggeration 5×`, `Phase scaled 1 fringe = 2.8 cm (C-band)`. Badge stays on while the transform is active, including in screenshots/replays.
3. **No impossible sensing**: no rendering of features beyond physical limits (GPR depth set by attenuation/permittivity; resolution ~λ/4; InSAR is line-of-sight only and blind in decorrelated/shadow/layover areas; soil-moisture maps are top few cm at sensor footprint). Masked/no-data areas drawn as a neutral hatch labelled "No data", never interpolated silently.
4. **Game overlays are distinct**: hints, ground truth reveals and scoring markers use outlined shapes in a separate UI layer, labelled "Hint" / "Truth", never blended into data colours.
5. **Units & provenance tooltip**: hover/inspect shows raw value, units, sensor, processing chain.

### 1.4 Citations (verified 2026-11-04 via fabiocrameri.ch/colourmaps and Zenodo)
- Crameri, F. (2018). *Scientific colour maps.* Zenodo. https://doi.org/10.5281/zenodo.1243862 (concept DOI; pin a version, e.g. v8.0.1 = 10.5281/zenodo.8409685).
- Crameri, F., Shephard, G.E., Heron, P.J. (2020). The misuse of colour in science communication. *Nature Communications* 11, 5444. **https://doi.org/10.1038/s41467-020-19160-7**
  - ⚠ The DOI in the brief (10.1038/s41467-019-13739-6) does **not** resolve to this paper (doi.org returned 404); corrected above.
- Nuñez, J.R., Anderton, C.R., Renslow, R.S. (2018). Optimizing colormaps with consideration for color vision deficiency… (cividis). *PLOS ONE* 13(7): e0199239. https://doi.org/10.1371/journal.pone.0199239
- viridis: van der Walt & Smith, matplotlib default colormaps (2015).

### 1.5 Licences (all must be permissive)
| Palette set | Licence | Obligation |
|---|---|---|
| Crameri Scientific Colour Maps (batlow, vik, roma, romaO, davos, grayC, …) | MIT, verified 2026-11-04 from the primary source: Zenodo https://doi.org/10.5281/zenodo.1243862 (v8.0.1 https://doi.org/10.5281/zenodo.8409685, `+LICENCE.pdf`) | Keep copyright + licence notice: `palettes/LICENSES/crameri-LICENSE` and credits screen |
| viridis / magma / inferno / plasma | CC0 (public domain dedication) | None; credit as courtesy |
| cividis | BSD-style (licence-cleared 2026-11-04) | Keep the Battelle copyright notice verbatim: `palettes/LICENSES/cividis-NOTICE` (source https://github.com/pnnl/cmaputil/blob/master/LICENSE) and on the credits screen |
Policy: no palette enters the registry without a licence file and SPDX ID; non-permissive → rejected.

## 2. HUD accessibility

- **Contrast (WCAG 2.2)**: text ≥ 4.5:1 (SC 1.4.3; ≥ 3:1 only for large text ≥ 24 px / 18.7 px bold); UI components, icon strokes, focus rings and graph lines ≥ 3:1 (SC 1.4.11). Focus indicator visible and unobscured (SC 2.4.11). Contrast checked automatically in CI against every theme.
- **White-background high contrast is the DEFAULT theme (accepted by Strata)**: white/near-white background, black text, ≥ 7:1 text contrast target (AAA). Offered at first launch, persisted, toggled in one keypress. Rationale: our primary user cannot read small visuals on dark backgrounds. Data palettes re-checked on light background (e.g. prefer `batlow`/`vik` over dark-ended maps; colourbar framed with a 2 px black border).
- **Icons**: minimum 32 px (default 48 px), stroke ≥ 3 px with a contrasting 2 px outline, simple silhouettes; tested at 200% scale.
- **Redundant encoding**: never colour alone (SC 1.4.1). Targets = shape (◆ metal, ● void, ▲ pipe) + pattern/hatch + text label; good/bad feedback = icon + sound + text. Colourbar ticks carry numbers, not just hue.
- **Captions & audio**: captions for all speech and meaningful sounds (`[ping: strong reflector]`), adjustable size/background; visual flash for audio cues; no information by sound alone.
- **Input**: full remapping (keyboard, mouse, gamepad), one-handed preset, hold-to-toggle options, no time-critical inputs without "relaxed timing" option (SC 2.2.1), target size ≥ 24×24 CSS px (SC 2.5.8).
- **Scalable text**: 100–200% UI scale without loss of content (SC 1.4.4), min body 18 px default, dyslexia-friendly font option, reflow rather than clip.
- **Motion**: reduce-motion toggle (no fringe animation, no camera shake); no flashing > 3/s (SC 2.3.1).

## 3. Deterministic implementation sketch (no code yet)

```
palettes/
  registry.toml              # id, class, source, version, spdx, sha256, cvd_tested
  crameri-8.0.1/batlow.csv   # 256 × sRGB float, exact upstream values
  mpl/viridis.csv
  LICENSES/MIT-Crameri.txt  CC0-viridis.txt ...
  SHA256SUMS
tools/render_test_image   # CLI
goldens/<palette>@<theme>.png + .sha256
```
- **Versioned data**: palettes stored as plain CSV LUTs copied verbatim from a pinned upstream release; `registry.toml` records version, SPDX licence, sha256. Loader verifies checksum at build and refuses mismatches. Changing a palette = new version ID (`batlow@8.0.1`), never in-place edits.
- **Seeded test image**: `make palette-test SEED=42 PALETTE=romaO THEME=light` → CLI generates synthetic fields (linear ramp, sinusoidal phase wrap, signed B-scan hyperbolae, no-data hatch) from a fixed seed with integer/fixed-precision maths, renders with colourbar, units, exaggeration badges, outputs PNG (no timestamps/metadata in file).
- **Golden-image tests**: `make golden-check` re-renders all palette×theme combos and compares byte-exact (sha256), with a perceptual-diff (ΔE2000 ≤ 0.5) fallback report for GPU paths. Extra checks: lightness monotonicity (CAM02-UCS J′) for sequential, symmetry for diverging, end-match for cyclic, CVD simulation (deuteranopia/protanopia/tritanopia) ΔE between adjacent ticks, WCAG contrast for every HUD theme token, banned-name lint.
- `make golden-update` requires a reviewer sign-off note in the PR description.

## 4. Open decisions (scores 1–5, higher better; weights in brackets)

**D1. Default theme at first launch**
| Option | Readability for primary user (×3) | Data fidelity (×2) | Effort (×1) | Total |
|---|---|---|---|---|
| Light high-contrast default | 5 | 4 | 4 | **27** |
| Dark default, light optional | 2 | 4 | 5 | 19 |
| Ask at first launch (light preselected) | 5 | 4 | 3 | 26 |
Decision: Light (white-background) high-contrast DEFAULT — accepted by Strata. First-launch prompt as a fast follow.

**D2. Palette scope**
| Option | Honesty/consistency (×3) | Licence simplicity (×2) | Variety (×1) | Total |
|---|---|---|---|---|
| Crameri only | 5 | 5 | 4 | **29** |
| Crameri + viridis/cividis | 5 | 4 | 5 | 28 |
| Open user-selectable list | 2 | 2 | 5 | 15 |

**D3. Golden-test strictness**
| Option | Determinism (×3) | Cross-GPU robustness (×2) | Maintenance (×1) | Total |
|---|---|---|---|---|
| Byte-exact CPU reference + ΔE for GPU | 5 | 4 | 3 | **26** |
| Byte-exact everywhere | 5 | 1 | 2 | 19 |
| Perceptual diff only | 3 | 5 | 4 | 23 |

**D4. User-adjustable gain/exaggeration?** Options: (a) allowed with always-on badge [recommended], (b) locked presets only, (c) free and unlabelled [rejected — violates §1.3].

## 5. Navigator review — Pixel Lantern-N (2026-11-04)
- cividis: initially marked EXCLUDED pending licence check. **Update 2026-11-04:** licence-cleared as BSD-style; re-added as an alternate (envelope, point cloud, soil moisture), D2 restored, and the Battelle copyright notice must be kept.
- Crameri 2020 DOI verified as 10.1038/s41467-020-19160-7 (already correct in §1.4).
- White-background high contrast stated as the DEFAULT (accepted by Strata) in §2 and D1.
- Document licence field: UNLICENSED (private repo; licence pending Audrey). Palette-asset licences (MIT/CC0) are upstream third-party licences, unchanged.
- Verdict: Pixel Lantern-N APPROVE.
- Licence files added 2026-11-04: `palettes/LICENSES/crameri-LICENSE` (MIT, verified on Zenodo) and `palettes/LICENSES/cividis-NOTICE` (Battelle notice, verbatim from pnnl/cmaputil).
