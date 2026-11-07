# GDD v0.5 — "Ground Truth" (working title): sensing-games training sim
**Authors:** Loam-D / Loam-N (Grok Bot), for Audrey Evans · **Lead:** Strata · **Date:** 2026-11-06 10:48 MST (UTC-7) · **Status:** draft PR, not merged (Audrey authorized publication 2026-11-06 10:55 MST). **Verity PASS on rev2 reported by Strata @ confidence 0.90** (not independently re-read here); this rev3 applies Strata-relayed nits only. Supersedes contradictory M1/coverage/W wording in v0.4; historical `GDD_v0`…`GDD_v0.4.md` stay unchanged. **Licence:** UNLICENSED (private repo; licence pending Audrey). **Publication path:** `docs/sensecrew/loam/GDD_v0.5.md` via a new draft PR targeting `daily/2026-11-06` (live base verified @ `2ef0d0afcfd98e604bfaae5d6655a8dccd8bae23`); do not reopen merged PR #10; do not merge.
**Inputs:** GDD v0.1; Ledger-Play Balance Proposal v0.1 (`/workspace/prompt-hoard/frontier/ledger-play-v0-balance-proposal-2026-11-04.md`, read in full); lead revisions (a)–(d) and steering rulings (a)–(d) dated 2026-11-04. Legend: [READ] · [VERIFIED] (resolved this session) · [UNVERIFIED].

## 0c. Changelog vs v0.4 (M1 Option B coverage-only + Verity CHANGES targets; LOCAL DRAFT 2026-11-06)
1. **Production M1 = Option B while W is null:** `sweep_width_km` / Bedrock `M1_W_KM` stay null; score coverage planning + budget use only. No POD/POS/optimal/η and no Bayesian negative-evidence update from coverage alone.
2. **§2 steps 4 & 6:** explicit null-W production-M1 exception (coverage ≠ detection miss).
3. **§4 / §4a:** LO and Scorer-calls cells rewritten; W defined as detection integral \(W=\int p(x)\,dx\) [km], distinct from geometric swath; Option A cookie-cutter toy defaults **OFF** and firewalled (§4b).
4. **§6:** `make score --scorer clean` excluded for null-W M1 runs.
5. **§0a.1 / §9(g):** reconciled — blanket “M1 goes through Scorer” and “coverage-only fallback retained” no longer contradict Option B.
6. **Isolation:** Toy A must not feed `M1_W_KM`, NEW-10 production cells, CleanScorer, M1 LOs/unlocks, or Bedrock/Fusion paths described in open draft PRs #41 / #42 / tile orchestration (see §4b; no invented definitions).
7. **Gates:** Verity PASS on rev2 **as reported by Strata** @ 0.90 (five contradictions); this rev3 is nits-only before any publish. Independent Verity review body not re-fetched in this pack.

## 0d. Changelog rev2 → rev3 (Verity nits via Strata; LOCAL DRAFT 2026-11-06)
1. **M1 title:** renamed from "Water-filling" to **"Coverage planning"** while W=null; "Water-filling" kept as historical alias for the post-cited-W CleanScorer.optimal path (avoids implying water-filling/η scoring under Option B).
2. **Checklist / Bedrock xfail:** production posture is Option B coverage harness, **not** “xfail until W” as the M1 LO. PR #41 historical M1 CleanScorer xfails are Bedrock test debt to realign — not the GDD mission definition (see NITS checklist).
3. **§8.7:** qualify “Scorer replaces repo scoring (C5) ✔” — holds for cited-W missions; null-W production M1 is the Option B exception.
4. **Out of scope:** no cold-case mode; no avatar work (unapproved / conflicts with synthetic-only; avatar needs direct user ask).

## 0. Changelog vs v0.3 (lead updates a–g, 2026-11-04)
1. **(a) Final registry numbers (source: Verity, Discussion #25; I have not read that Discussion):** 2300 sensegame · 2310 NEW-01 CleanScorer · 2320 NEW-03 DEM · 2330 NEW-10 sweep table · 2331 NEW-11 sweep_width adapter · 2340 NEW-12 Ledger-Play harness · 2350 insect-trace-add-sim · 2360 NEW-22 · 2370 NEW-13. NEW-02 and NEW-04..09 have no final number yet.
2. **(b)** `sweep_width.py` is **CLEAR for reference/adapter use only, through NEW-11 (2331)**. Nothing imports it except the adapter, and it is never copied into sensegame.
3. **(c)** `lpb_mpb2003.json` stays **BLOCKED** (copyrighted UK handbook).
4. **(d)** `make dem` uses Bedrock's **pure-Python GeoTIFF writer** for byte-identical output. rasterio/GDAL are used only for read-back checks in tests.
5. **(e)** Licence fields read `UNLICENSED (private repo; licence pending Audrey)`.
6. **(f)** `cross_tier_min_mastered`: integer, range 1–5, default 1, tuned by Ledger-Play.
7. **(g)** M1 primary sensor: **1a LiDAR DEM differencing (airborne lidar swath), owned by Waveform** (scored in §4a).

## 0b. Changelog v0.2 → v0.3 (kept; lead rulings L1–L4)
1. **L1 physics provenance:** every physics value, sweep widths included, comes only from the node's owning science pair, with a citation and a Verity co-sign. This supersedes proposal C3. Ledger-Play tunes only `cost_credits` and `deploy_time_min` (plus the cross-tier parameter, see L4). §8.1 is resolved.
2. **L2 microtopo audit:** Waveform owns the audit; Aquifer co-checks the hydrology parts. §8.2 is resolved.
3. **L3 units:** `sweep_width_km` [km], `coverage_rate_km2_h` [km²/h]. Every schema column states its unit (§3b). §8.3 is resolved.
4. **L4 cross-tier rule:** confirmed; Ledger-Play may tune it via sweeps as `cross_tier_min_mastered` (default 1).
5. `sweep_width.py` stays BLOCKED: NEW-11 is OFF by default (`SWEEP_WIDTH_REUSE=0`) and NEW-10 is the fallback.

## 0a. Changelog v0.1 → v0.2 (kept)
1. **Scorer:** the core loop for missions with a cited, Verity-co-signed W (and M2/M3 when their W cells are set) goes through Ledger-Play's `Scorer` protocol (pod/pos/optimal/update). NEW-01 is its clean implementation `CleanScorer`. **Exception (v0.5 / Option B):** production M1 while `w_km`/`M1_W_KM` is null does **not** call Scorer for detection scoring or posterior update — see §2 steps 4/6 and §4. No `search_theory`, `compare_plans` or `optimal_search` anywhere; the naive baselines become harness policies.
2. **Swarms:** none run before Strata approves; the first swarm is ≤10 subagents with a small per-subagent token budget (PLACEHOLDER). 100 is only the rule-2 hard cap.
3. **Economy:** credits buy usage, not unlocks; unlocks come only from learning-objective mastery. Every mission has two budgets, `budget_track_km` and `budget_credits`.
4. **DEM:** the DEM is a Bedrock procedural synthetic prior, materialised as the seeded fixture `fixtures/dem_synthetic_<seed>.tif` (NEW-03).
5. **sweep_width.py:** imports checked and clean, but the file has **case-file lineage**, so reuse is gated on Verity. A thin adapter is designed (§3a).
6. **Pending module audits** by the owning pairs (§7).
7. **GeoTIFF writer:** permissive only (GDAL MIT-style, rasterio BSD-3); no GPL linking.
8. **Citations:** Stone 1975 with publisher and ISBN; Tobler 1993 NCGIA TR 93-1. Both marked "no DOI".

## 1. Vision (unchanged)
An honest ground-detection training sim. The player learns screen → survey → confirm and POA/POD/POS reasoning. The skin never changes physics, and confirmation tools are never shown as locators (SOIL_SENSING_TIERS.md [READ]).

## 2. Core loop
1. **Brief:** seeded scenario. Terrain is the Bedrock procedural prior `dem_synthetic_<seed>.tif` (NEW-03); the POA prior comes from NEW-02 (SYNTHETIC placeholder distributions, labelled in outputs and the HUD).
2. **Deploy sensor:** spends `budget_credits` (`cost_credits` per deploy, plus `deploy_time_min`) and `budget_track_km` (effort z, in km; Tier-3 nodes use `effort_unit: samples`).
3. **Read noisy, honest data:** seeded Bedrock sensor model. Physics comes only from the owning science pair, cited and Verity co-signed (L1); otherwise it shows PLACEHOLDER and is not scorable.
4. **Update:** `Scorer.update(segments, effort_km) -> segments` (posterior POA after a **detection** miss; the ROW segment is never searched). **Null-W production M1 exception (Option B):** coverage alone is **not** a detection miss. Do **not** call `Scorer.update` from coverage; do **not** perform a Bayesian negative-evidence / POA update from coverage alone. POA stays at the NEW-02 prior until a cited-W path or a later mission provides an honest detection outcome.
5. **Search/confirm.**
6. **Score:** When every scored segment has a cited `w_km`: `POS = Scorer.pos(segments, effort_km)`, `POS_opt = Scorer.pos(segments, Scorer.optimal(segments, budget_track_km))`, η = POS/POS_opt. The point formula is Ledger-Play v0 §2 (weights PLACEHOLDER). The debrief compares against the `equal` / `poa_proportional` / `greedy` harness policies, which use `Scorer.pos` only. **Null-W production M1 exception (Option B):** do **not** compute POD, POS, POS_opt, or η. Score **coverage-planning and budget-use** metrics only (weights PLACEHOLDER — Ledger-Play). Coverage is not detection and is not evidence of target absence.

### 2a. Scorer ↔ NEW-01 reconciliation
```python
class Scorer(Protocol):   # ledgerplay/scoring.py (Ledger-Play proposal v0.1 §C5)
    def pod(self, w_km: float, track_km: float, area_km2: float) -> float: ...
    def pos(self, segments: list[Segment], effort_km: dict[str, float]) -> float: ...
    def optimal(self, segments: list[Segment], budget_km: float) -> dict[str, float]: ...
    def update(self, segments: list[Segment], effort_km: dict[str, float]) -> list[Segment]: ...
# Segment = {name, area_km2, poa, w_km, speed_kmh|None, is_row: bool}
```
- **NEW-01 = `CleanScorer`** (owner Bedrock, Verity co-review), clean-room from the published theory:
  - `pod` = 1 − exp(−W·z/A) (Koopman 1956b)
  - `pos` = Σ POA·POD
  - `optimal`: KKT water-filling, z_i = max(0, ln(POA_i r_i/λ)/r_i) with r_i = W_i/A_i (Koopman 1957; Stone 1975)
  - `update`: POA_i' = POA_i(1−POD_i)/(1−Σ POA_j·POD_j) (Stone 1975)
- **Invariants:** ROW gets 0 effort; Σ POA = 1 (tolerance 1e-9); any segment with `w_km = null` is **unscorable**. `pos` and `optimal` raise `UncitedSweepWidth` and never substitute a value.
- `QuarantinedRepoScorer` stays disabled. Hours mode (z = v·t) is out of v0.2 scope; the Scorer is km-only, matching the proposal.
- **M1 coverage-only (W=null / Option B):** does not call `pod`/`pos`/`optimal`/`update` with a substituted C or toy W. Coverage metrics and budgets are separate from CleanScorer. Teaching displays of f(C)=1−exp(−C), if any, must be labelled an illustrative idealized random-overlap coverage *model* (dimensionless planning C), never POD/POS, never mapped coverage, never evidence of absence.
- **W definition (CleanScorer / NEW-10):** `sweep_width_km` is the search-theory effective detection width \(W=\int_{-\infty}^{\infty} p(x)\,dx\) in km, where p(x) is the lateral-range detection probability at cross-track distance x (Koopman 1956b). It is **not** geometric swath width 2 H tan(FOV/2) and not a cookie-cutter usable-fraction of that swath unless a primary citation supplies that mapping for the stated target/conditions (none for production M1 1a as of Discussion #28 Waveform v2).
- **Contract tests (Navigator writes them first):** KKT conditions, brute force on 2 segments, ROW = 0, POS monotone in budget, Bayes posterior sums to 1, determinism, and `test_no_forbidden_imports` (fails on `search_theory`, `optimal_search`, `lost_person_behavior`).

### 2b. Citations
| Ref | DOI | Status |
|---|---|---|
| Koopman, B.O. (1956a) The Theory of Search. I. Kinematic Bases. *Operations Research* 4(3) | 10.1287/opre.4.3.324 | VERIFIED (Crossref) |
| Koopman (1956b) …II. Target Detection. *Oper. Res.* 4(5) | 10.1287/opre.4.5.503 | VERIFIED |
| Koopman (1957) The Theory of Search [III. Optimum Distribution of Searching Effort]. *Oper. Res.* 5(5) | 10.1287/opre.5.5.613 | DOI VERIFIED; subtitle UNVERIFIED |
| Stone, L.D. (1975) *Theory of Optimal Search*. New York: Academic Press, Mathematics in Science and Engineering vol. 118. ISBN 0-12-672450-4 / 978-0-12-672450-9 | **no DOI** | publisher and ISBN VERIFIED via Open Library; series/volume from Crossref chapter metadata. 2nd ed. (ORSA, 1989) ISBN 1-877640-00-X, not used. |
| Tobler, W. (1993) *Three Presentations on Geographical Analysis and Modeling*. NCGIA Technical Report 93-1, UC Santa Barbara | **no DOI** | report number as cited in lost_person_sim.py docstring [READ]; not independently verified |

## 3. Progression / tech tree
- **Unlocks:** by learning-objective (LO) mastery only. A node unlocks when its LO passes on 3 consecutive seeds (= Ledger-Play `unlock_rule`, keyed by `node_id`; `unlock_level` removed). Credits never unlock anything.
- **Credits:** in-mission currency for usage (deploys, samples, re-flights). Running short of credits limits a plan; it never gates progression.
- **Order:** within a tier, follows listing order. **Cross-tier prerequisite (CONFIRMED, L4):** a Tier-n node is playable once ≥ `cross_tier_min_mastered` nodes of tier n−1 are mastered (default 1, integer, range 1–5, **final per (f)**). Ledger-Play tunes it via sweeps.
- **Ledger-Play flags adopted:** `available: false` for 1b, 2b, 3c (missing components); `detector: false` for 1e (prior), 2c (context), 2e (derived).

The tier tables are as in v0.1 §3 (nodes 1a–1e, 2a–2e, 3a–3d; same principles, owners, LOs and licence notes), with these changes:
- 1a's DEM pairs are `dem_synthetic_<seed>{a,b}.tif`.
- Each row gains `effort_unit` (track_km for Tiers 1–2, samples for Tier 3) `physics_owner` (the node's owning science pair, per L1) and `physics_cosign: Verity`.

### 3b. Schema units (L3)
| Column | Unit | Who may set it |
|---|---|---|
| sweep_width_km | km | owning science pair + Verity co-sign |
| coverage_rate_km2_h | km²/h | owning science pair + Verity co-sign |
| speed_kmh | km/h | owning science pair + Verity co-sign |
| area_km2 | km² | scenario (NEW-02/03) |
| poa, pod, pos, eta | dimensionless (0–1) | prior / Scorer |
| track_km, budget_track_km | km | mission / player |
| effort_samples | samples (count) | mission / player (Tier 3) |
| cost_credits, budget_credits | credits | Ledger-Play |
| deploy_time_min | min | Ledger-Play |
| cross_tier_min_mastered | nodes (count) | Ledger-Play (sweep-tunable) |
| DEM cell size | m | NEW-03 |
`sweep_width_m` and the unsuffixed `coverage_rate` are retired.

### 3a. Sweep widths (R5) + `sweep_width.py` adapter (steering a)
- Table NEW-10 `fixtures/sweep_width_cited_synthetic.json` stores `sweep_width_km` (proposal C6). Uncited cells stay `null`, `flag: "UNCITED — not scorable"`. Each cell needs `physics_owner` (the owning science pair), a citation and `verity_cosign` (L1); Ledger-Play cannot write to it.
- **Import check [READ, local copy @a2630989]:** stdlib only (argparse, csv, json, math, os, sys), plus lazy `h5py` and `numpy`/`rasterio` inside the GEDI/raster readers. **No search_theory or other quarantined import** ✔.
- **Lineage finding:** comment lines 77–89 name `docs/case-files/CASE-X/sector_master_sar_database.db_1.txt` as the source of earlier AI-generated values, which were **dropped**. Line 94 also says `ROW_NAMES … same convention as search_theory`. That is a case-file reference in the file's history, even though the values were removed. v0.3 status was BLOCKED. **v0.4: CLEAR for reference/adapter use only through NEW-11 (2331)**, per lead ruling (b). I did not open the referenced case file.
- **Adapter design (`sensegame/adapters/sweep_width_adapter.py`, NEW-11):** a pure function `to_segments(rows) -> list[Segment]`, mapping `sweep_width_km→w_km`, `speed_kmh`, and `name ∈ {row, rest of world}` → `is_row=True`. It calls only `sweep_width.process`, `canopy_scaled_width` and `table_width`, and it carries `sweep_width_source`/`status` into Segment provenance. Null W stays null. It is behind feature flag `SWEEP_WIDTH_REUSE=0`, **still OFF by default**; the default build uses NEW-10 (2330). The adapter is the only permitted import site; `test_no_forbidden_imports` allows `sweep_width` only under `sensegame/adapters/`. The fallback is a clean NEW-10 table plus the canopy model W_eff = W_open(1−cover)^k reimplemented from its stated Beer-Lambert basis (citation PLACEHOLDER).

## 4. Missions (seeded; synthetic only; dual budgets)
| Mission | Seed | budget_track_km | budget_credits | Scorer calls | LO |
|---|---|---|---|---|---|
| M1 "Coverage planning" (sensor 1a airborne lidar, Waveform; historical alias "Water-filling" reserved for post-cited-W / CleanScorer.optimal path) | 1001 | 10 | PLACEHOLDER (Ledger-Play) | none while W=null (coverage/budget metrics only); pos, optimal only after cited Verity-co-signed W | **Option B (production, W=null):** coverage-planning + budget-use LO (weights PLACEHOLDER — Ledger-Play). No Scorer.pod/pos/optimal/update; no Bayesian negative-evidence from coverage; no η. Optional HUD f(C)=1−exp(−C) = illustrative idealized random-overlap *model* only (not POD/POS, not W, not mapped coverage). **After cited W:** LO upgrades to ≥90% of POS_opt under CleanScorer. Toy Option A (§4b) does not satisfy this LO |
| M2 "Pit or mound" | 1002 | PLACEHOLDER | PLACEHOLDER | update, pos | F1 ≥0.8; posterior matches analytic value to 1e-9 |
| M3 "Screen, survey, confirm" | 1003 | PLACEHOLDER | PLACEHOLDER (samples priced per sample) | all four | within both budgets; correct tier order; no over-claiming |
All terrain comes from `dem_synthetic_<seed>.tif` (Bedrock procedural prior). `seeds.jsonl` plus sha256 give byte-identical replay.

## 4a. M1 primary sensor (lead update g)
M1 needs a Tier-1, `available`, `detector` node whose effort is in track km and whose W is a lateral detection width. Scores are 0–2 per criterion:
| Node (owner) | Tier-1 & available | Detector | Track-km / W meaningful | Repo support | Total |
|---|---|---|---|---|---|
| **1a LiDAR DEM differencing (Waveform)** | 2 | 2 | 2 (needs cited detection W=∫p(x)dx [km]; geometric swath at altitude/scan angle is context only, not W) | 1 (`microtopo.py`, audit pending) | **7** |
| 1d SAR/NDVI change (Backscatter) | 2 | 2 | 1 (satellite scene, not track-driven) | 2 | 7 → loses tie on track-km fit |
| 1c InSAR (Fringe) | 1 (NEW-05 gap) | 2 | 0 (scene-based) | 1 | 4 |
| 1b Full-waveform (Waveform) | 0 (`available:false`) | 2 | 2 | 0 | 4 |
| 1e TWI (Aquifer) | 2 | 0 (prior) | 0 | 1 | 3 |
**Pick: 1a, owner Waveform.** Requested W conditions: open ground / low vegetation (canopy cover stated), target = synthetic pit/mound ≥ stated diameter, stated AGL altitude, scan angle and point density. Required production value: `sweep_width_km` = effective **detection** width \(W=\int p(x)\,dx\) in km (lateral-range integral), cited, Verity co-sign (L1). Geometric swath (e.g. Discussion #28 OH Statewide 2019 Table 2-4 stated 1.456 km) is **not** that W. Until a cited detection W exists, production M1 is **Option B coverage-only**: NEW-10 cell and Bedrock `M1_W_KM` stay null; score coverage planning and budget use only; coverage ≠ detection miss and ≠ target absence. See §4b for firewalled Toy A (defaults OFF).


## 4b. Toy Option A — firewalled, defaults OFF (not production M1)
**Status:** design isolation rule for any future toy lesson that might use a cookie-cutter / definite-range proxy (Discussion #28 Option A; e.g. usable-fraction × geometric swath ≈ 0.9 × 1.456 km ≈ 1.31 km as a *labelled game parameter*). **No calibration invented here**; the numeric example is Discussion context only.

**Default: OFF.** Must not enable in production M1, CI goldens, or unlock paths without a separate Strata brief + Verity co-sign of the *toy* labelling.

**Hard isolation (do not wire):**
- Must **not** set or read Bedrock `M1_W_KM` (PR #41 CleanScorer / golden path; remains `None` until a cited detection W).
- Must **not** write production NEW-10 (`fixtures/sweep_width_cited_synthetic.json` / registry 2330) cells used by M1 scoring.
- Must **not** call or subclass production `CleanScorer` / NEW-01 (2310) as if the toy width were a cited W.
- Must **not** satisfy or unlock M1 learning objectives / mastery unlocks (§3); Toy A play cannot grant M1 LO credit.
- Must **not** feed open Bedrock/Fusion draft surfaces described in PR #41 (CleanScorer/DEM goldens), PR #42 (Fusion `combine.py` hint layer; never changes POA — only CleanScorer.update does), or tile orchestration such as `sensegame.tile.run_one_tile` (called out as out-of-scope in Bedrock DEM→layer docs / PR #47 until separate gates). Definitions are those PRs’ own; this GDD does not redefine them.

**Label required if ever shown:** “toy game parameter — not empirically calibrated detection W; not production M1.”

## 5. Two-phase plan and swarms
- **Phase 1:** NEW-03 DEM → NEW-01 CleanScorer (contract tests first) → NEW-02 → missions. Ledger-Play sweeps run manually (`make sweep`) by the pair.
- **Phase 2:** Godot client, art, narrative.
- **Swarms:** none before Strata approves. First swarm ≤10 subagents, small token budget (PLACEHOLDER), stop on first error or hash mismatch, Verity re-runs ≥10% of shards (at least 1). Scaling toward the 100 hard cap needs a fresh Strata brief.

## 6. Manual run (proposed)
```
make dem SEED=1001                 # python -m sensegame.dem --seed 1001 -> fixtures/dem_synthetic_1001.tif (Bedrock pure-Python GeoTIFF writer; byte-identical; rasterio/GDAL read-back check only)
make sim MISSION=M1 SEED=1001      # budget_track_km / budget_credits from missions/M1.yaml
make score RUN=out/M1_1001         # NULL-W M1: do NOT use --scorer clean / CleanScorer. Use coverage+budget metrics only (PLACEHOLDER harness). After cited W: python -m sensegame.score --scorer clean (NEW-01)
make score RUN=out/M2_1002         # python -m sensegame.score --scorer clean   (Scorer protocol; NEW-01) — when M2 W cells are set
make sweep SEED=42 GRID=balance/grids/v0.yaml   # Ledger-Play harness, manual
make determinism SEED=1001 ; make test
```

## 7. Licence, registry, pending audits
- **GeoTIFF writer (NEW-03, 2320):** Bedrock's pure-Python writer (no compiled deps; byte-identical by sha256). Read-back verification only, never writing, uses GDAL (MIT/X-style per LICENSE.TXT "GDAL/OGR General" [READ]) or rasterio (BSD-3-Clause per LICENSE.txt header [READ]); GitHub reports NOASSERTION for both, so the files themselves were checked. No GPL linking. Verity audits that the wheel's bundled drivers are permissive [UNVERIFIED].
- **Licence field (all manifests and docs):** `UNLICENSED (private repo; licence pending Audrey)`. Internal use OK.
- **Blocked data:** `lpb_mpb2003.json` BLOCKED (copyrighted UK handbook); never read, imported or shipped.
- **Registry (final, v0.4):** 2300 sensegame · 2310 NEW-01 · 2320 NEW-03 · 2330 NEW-10 · 2331 NEW-11 · 2340 NEW-12 · 2350 insect-trace-add-sim · 2360 NEW-22 · 2370 NEW-13 (Verity, Discussion #25).
- **Registry (v0.3 working names, kept):** NEW-01 CleanScorer · NEW-02 prior · NEW-03 DEM · NEW-04 full-waveform · NEW-05 InSAR · NEW-06 EMI · NEW-07 gamma · NEW-08 LIBS · NEW-09 taphonomy · NEW-10 sweep table · NEW-11 sweep_width adapter. Ledger-Play's `NEW-xx` sweep harness maps to **NEW-12**.
- **Pending audits** (imports + case-file lineage, by the owning pair; all OPEN):
  - `microtopo.py`: **Waveform** (owner, L2); Aquifer co-checks the hydrology parts
  - `gpr-wave-model/`: Deepscan
  - `qpcr_assay.py`, `qpcr_interpret.py`, `lab_readers.py`: Humus (+Chitin for 3b)
  - `s2_change.py`, `sar-change-detection`: Backscatter
  - `multi_proxy/*`: Humus/Aquifer/Quartz
  - `sweep_width.py`: Verity (lineage found, §3a)

## 8. Conflicts between Ledger-Play v0.1 and the GDD
1. **[RESOLVED by L1]** Physics ownership: C3 lets only Humus/Deepscan/Isotope fill physics. Lead ruling R5 (v0.1) says "Ledger-Play and the sensor pairs" supply W, and Ledger-Play's own principle is never to tune physics. So nodes 1a–1e and 3d stay PLACEHOLDER under C3. **Needs Strata:** widen C3 or require co-signing. GDD stance: Ledger-Play may *carry* cited values, never *source* them.
2. **[RESOLVED by L2]** microtopo owner: lead ruling assigns the audit to Humus/Aquifer, while the GDD/C4 node owner for 1a is Waveform. The audit owner and the node owner differ; that's acceptable but should be confirmed.
3. **[RESOLVED by L3]** Units: the proposal's v0 §1 uses `sweep_width_m` and `coverage_rate` in km²/h or m²/h; C6 switches to `sweep_width_km`. v0.2 adopts km. `coverage_rate` units remain mixed per row; I recommend fixing them to km²/h.
4. **Prior source:** the proposal's v0 §2 used `lost_person_sim` on `synthetic_flat_terrain`, and v0.1 #7 says "Bedrock procedural prior until resolved". The GDD now makes that permanent (lpb blocked; lost_person_sim out of the game path).
5. **Hours mode:** `optimal_search` supported hours; `Scorer` is km-only. Fine for v0.2; flag it for any later helicopter/UAV nodes.
6. **Score weights / credit values:** all PLACEHOLDER in the proposal. The M1–M3 `budget_credits` stay PLACEHOLDER until the sweep runs.
7. **Confirmed matches:** credits = usage, unlocks = LO mastery (proposal mismatch #4) ✔. Dual budgets (#6) ✔. Swarm ≤10 to start (C2) ✔. Scorer replaces repo scoring (C5) for **cited-W** missions ✔; **null-W production M1 (Option B) is the documented exception** — coverage/budget metrics only, not CleanScorer. Node ids 1a–3d match (C4) ✔.

## 9. Loam-N review (v0.4)
- **(a)** final registry numbers recorded; source attributed to Verity, Discussion #25, which I have not read [UNVERIFIED] ✔.
- **(b)** sweep_width CLEAR only through NEW-11, still off by default, import-scoped by test ✔. **(c)** lpb_mpb2003 BLOCKED ✔.
- **(d)** pure-Python writer for output; GDAL/rasterio read-back only, so permissive-only holds ✔. **(e)** licence string applied ✔. **(f)** 1–5, default 1, Ledger-Play tunes ✔.
- **(g)** M1 = 1a / Waveform. **v0.5 supersession:** the v0.4 phrase “coverage-only fallback retained” referred to the old POD=1−e^(−C) wording and is **withdrawn**. Production M1 is Option B coverage-only (no Scorer POD/POS/η/update while W=null); W request means detection ∫p(x)dx, not geometric swath. Units in km ✔.
- **Residual:** Discussion #28 — Waveform recommends null detection W; geometric swath ≠ W. Production M1 stays coverage-only until cited ∫p(x)dx lands in NEW-10 with Verity co-sign. **Rev2 Verity PASS reported by Strata @ 0.90**; rev3 applies title / §8.7 / xfail-checklist nits only. Microtopo audit still open. Toy A (§4b) OFF. Bedrock PR #41 may still show historical M1 CleanScorer xfails until that PR is realigned to Option B coverage scoring — GDD LO is coverage planning, not xfail-gated water-filling.

Loam-N APPROVE  *(v0.4 historical; does not approve v0.5 draft)*

## 9c. Loam-N review (v0.5)
- Rev2 addressed Verity CHANGES (1)–(5); **Verity PASS on rev2 reported by Strata @ 0.90** (not independently re-read in this pack).
- Rev3 applies three Strata-relayed nits (§0d). Independent read-only Loam-N review of the pre-publication body (SHA256 `a4e1d7d2a7ab59b2da74616c604a73973845c27ec60a3bce7e1c6d38bcbae078`): **Loam-N APPROVE**. Passed null-W consistency, units, toy fences, and nits. Reason: Option B consistency holds throughout; no coverage-derived detection probability or negative Bayesian evidence; toy A OFF and isolated from production M1; prior GDD history retained. That APPROVE is of those reviewed bytes. This section and the header status/publication path are the only post-review metadata refresh; they are not a new approval.
- Strata reports Verity rev3 PASS @ 0.92 (not independently verified here).
- Publication: Audrey directly authorized this draft on 2026-11-06 10:55 MST. New draft PR adding `docs/sensecrew/loam/GDD_v0.5.md` targeting `daily/2026-11-06` @ `2ef0d0afcfd98e604bfaae5d6655a8dccd8bae23`; not PR #10; not merged.
- Out of scope for this draft: cold-case mode; avatar work.

## 9b. Loam-N review (v0.3, kept)
- **L1:** applied in §2, §3, §3a and §3b; Ledger-Play's write scope is cost_credits, deploy_time_min and cross_tier_min_mastered only ✔.
- **L2:** microtopo audit is Waveform + Aquifer (hydrology) ✔.
- **L3:** every column has a unit; dimensional check z[km]·W[km]/A[km²] is dimensionless ✔.
- **L4:** cross-tier rule confirmed and parameterised ✔.
- NEW-11 OFF, NEW-10 fallback ✔. Hard rules unchanged ✔.
- **Residuals:** confirm the 1–5 range; module audits still open; credits and weights PLACEHOLDER.

Loam-N APPROVE

## 9a. Loam-N review (v0.2, kept)
- **(a) Scorer:** grep of v0.2 finds `search_theory`/`optimal_search`/`compare_plans` only in prohibitions, the changelog, the audit list and conflict notes, never as a call ✔. NEW-01 is reconciled one-to-one to the four methods ✔.
- **(b) Swarms:** ≤10 to start ✔. **(c) Economy:** credits = usage, LO-only unlocks, dual budgets ✔; matches proposal #4/#6 ✔.
- **(d) DEM:** Bedrock procedural prior ✔.
- **Steering (a):** imports checked ✔; lineage found and gated, not hidden ✔. **(b)** audits listed ✔. **(c)** permissive writer ✔. **(d)** Stone (Academic Press, ISBN 0126724504) and Tobler TR 93-1, both "no DOI" ✔.
- **Units:** W km, z km, A km², r km⁻¹ ✔. `coverage_rate` mixed units flagged (§8.3).
- **Hard rules:** R3 ✔ R4 ✔ R5 ✔ R6 ✔. R7: the referenced case file was not opened; sweep_width reuse blocked pending Verity ✔. R8: nothing committed ✔.
- **Residuals:** §8.1 C3 ruling and the §7 audits block implementation, not this doc.

Loam-N APPROVE
