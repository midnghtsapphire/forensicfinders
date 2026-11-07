# GDD v0.2 — "Ground Truth" (working title): sensing-games training sim
**Authors:** Loam-D / Loam-N (Grok Bot), for Audrey Evans · **Lead:** Strata · **Date:** 2026-11-04 20:25 MST (UTC-7) · **Status:** DRAFT, doc only, local only. Supersedes v0.1; `GDD_v0.md` and `GDD_v0.1.md` are kept unchanged.
**Inputs:** GDD v0.1; Ledger-Play Balance Proposal v0.1 (`/workspace/prompt-hoard/frontier/ledger-play-v0-balance-proposal-2026-11-04.md`, read in full); lead revisions (a)–(d) and steering rulings (a)–(d) dated 2026-11-04. Legend: [READ] · [VERIFIED] (resolved this session) · [UNVERIFIED].

## 0. Changelog vs v0.1
1. **Scorer:** the core loop, M1, M2 and manual run now go through Ledger-Play's `Scorer` protocol (pod/pos/optimal/update). NEW-01 is its clean implementation `CleanScorer`. No `search_theory`, `compare_plans` or `optimal_search` anywhere; the naive baselines become harness policies.
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
3. **Read noisy, honest data:** seeded Bedrock sensor model with cited physics (or PLACEHOLDER).
4. **Update:** `Scorer.update(segments, effort_km) -> segments` (posterior POA after a miss; the ROW segment is never searched).
5. **Search/confirm.**
6. **Score:** `POS = Scorer.pos(segments, effort_km)`, `POS_opt = Scorer.pos(segments, Scorer.optimal(segments, budget_track_km))`, η = POS/POS_opt. The point formula is Ledger-Play v0 §2 (weights PLACEHOLDER). The debrief compares against the `equal` / `poa_proportional` / `greedy` harness policies, which use `Scorer.pos` only.

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
- **Order:** within a tier, follows listing order. Cross-tier prerequisite: a Tier-n node is playable once ≥1 node of tier n−1 is mastered (Loam decision, new in v0.2; Ledger-Play noted none was stated).
- **Ledger-Play flags adopted:** `available: false` for 1b, 2b, 3c (missing components); `detector: false` for 1e (prior), 2c (context), 2e (derived).

The tier tables are as in v0.1 §3 (nodes 1a–1e, 2a–2e, 3a–3d; same principles, owners, LOs and licence notes), with these changes:
- 1a's DEM pairs are `dem_synthetic_<seed>{a,b}.tif`.
- Each row gains `effort_unit` (track_km for Tiers 1–2, samples for Tier 3) and `physics_owner` per Ledger-Play C3. The C3 conflict is in §8.

### 3a. Sweep widths (R5) + `sweep_width.py` adapter (steering a)
- Table NEW-10 `fixtures/sweep_width_cited_synthetic.json` stores `sweep_width_km` (proposal C6). Uncited cells stay `null`, `flag: "UNCITED — not scorable"`.
- **Import check [READ, local copy @a2630989]:** stdlib only (argparse, csv, json, math, os, sys), plus lazy `h5py` and `numpy`/`rasterio` inside the GEDI/raster readers. **No search_theory or other quarantined import** ✔.
- **Lineage finding:** comment lines 77–89 name `docs/case-files/CASE-X/sector_master_sar_database.db_1.txt` as the source of earlier AI-generated values, which were **dropped**. Line 94 also says `ROW_NAMES … same convention as search_theory`. That is a case-file reference in the file's history, even though the values were removed. Under the ruling ("no case-file lineage"), the default is **not reusable until Verity rules**. I did not open the referenced case file.
- **Adapter design (`sensegame/adapters/sweep_width_adapter.py`, NEW-11):** a pure function `to_segments(rows) -> list[Segment]`, mapping `sweep_width_km→w_km`, `speed_kmh`, and `name ∈ {row, rest of world}` → `is_row=True`. It calls only `sweep_width.process`, `canopy_scaled_width` and `table_width`, and it carries `sweep_width_source`/`status` into Segment provenance. Null W stays null. It is behind a feature flag `SWEEP_WIDTH_REUSE=0` until Verity confirms lineage. The fallback is a clean NEW-10 table plus the canopy model W_eff = W_open(1−cover)^k reimplemented from its stated Beer-Lambert basis (citation PLACEHOLDER).

## 4. Missions (seeded; synthetic only; dual budgets)
| Mission | Seed | budget_track_km | budget_credits | Scorer calls | LO |
|---|---|---|---|---|---|
| M1 "Water-filling" | 1001 | 10 | PLACEHOLDER (Ledger-Play) | pos, optimal | ≥90% of POS_opt. Coverage-only fallback (player sets coverage C; POD = 1−e^(−C)) if no cited W exists |
| M2 "Pit or mound" | 1002 | PLACEHOLDER | PLACEHOLDER | update, pos | F1 ≥0.8; posterior matches analytic value to 1e-9 |
| M3 "Screen, survey, confirm" | 1003 | PLACEHOLDER | PLACEHOLDER (samples priced per sample) | all four | within both budgets; correct tier order; no over-claiming |
All terrain comes from `dem_synthetic_<seed>.tif` (Bedrock procedural prior). `seeds.jsonl` plus sha256 give byte-identical replay.

## 5. Two-phase plan and swarms
- **Phase 1:** NEW-03 DEM → NEW-01 CleanScorer (contract tests first) → NEW-02 → missions. Ledger-Play sweeps run manually (`make sweep`) by the pair.
- **Phase 2:** Godot client, art, narrative.
- **Swarms:** none before Strata approves. First swarm ≤10 subagents, small token budget (PLACEHOLDER), stop on first error or hash mismatch, Verity re-runs ≥10% of shards (at least 1). Scaling toward the 100 hard cap needs a fresh Strata brief.

## 6. Manual run (proposed)
```
make dem SEED=1001                 # python -m sensegame.dem --seed 1001 -> fixtures/dem_synthetic_1001.tif (rasterio/GDAL only)
make sim MISSION=M1 SEED=1001      # budget_track_km / budget_credits from missions/M1.yaml
make score RUN=out/M1_1001         # python -m sensegame.score --scorer clean   (Scorer protocol; NEW-01)
make sweep SEED=42 GRID=balance/grids/v0.yaml   # Ledger-Play harness, manual
make determinism SEED=1001 ; make test
```

## 7. Licence, registry, pending audits
- **GeoTIFF writer (NEW-03):** GDAL (MIT/X-style per LICENSE.TXT "GDAL/OGR General" [READ]) or rasterio (BSD-3-Clause per LICENSE.txt header [READ]); GitHub reports NOASSERTION for both, so the files themselves were checked. No GPL linking. Verity audits that the wheel's bundled drivers are permissive [UNVERIFIED].
- **forensicfinders:** private repo; internal use OK; licence choice pending with Audrey.
- **Registry:** NEW-01 CleanScorer · NEW-02 prior · NEW-03 DEM · NEW-04 full-waveform · NEW-05 InSAR · NEW-06 EMI · NEW-07 gamma · NEW-08 LIBS · NEW-09 taphonomy · NEW-10 sweep table · NEW-11 sweep_width adapter. Ledger-Play's `NEW-xx` sweep harness maps to **NEW-12**.
- **Pending audits** (imports + case-file lineage, by the owning pair; all OPEN):
  - `microtopo.py`: Humus/Aquifer (per lead ruling; GDD lists Waveform as the 1a node owner, see §8)
  - `gpr-wave-model/`: Deepscan
  - `qpcr_assay.py`, `qpcr_interpret.py`, `lab_readers.py`: Humus (+Chitin for 3b)
  - `s2_change.py`, `sar-change-detection`: Backscatter
  - `multi_proxy/*`: Humus/Aquifer/Quartz
  - `sweep_width.py`: Verity (lineage found, §3a)

## 8. Conflicts between Ledger-Play v0.1 and the GDD
1. **Physics ownership:** C3 lets only Humus/Deepscan/Isotope fill physics. Lead ruling R5 (v0.1) says "Ledger-Play and the sensor pairs" supply W, and Ledger-Play's own principle is never to tune physics. So nodes 1a–1e and 3d stay PLACEHOLDER under C3. **Needs Strata:** widen C3 or require co-signing. GDD stance: Ledger-Play may *carry* cited values, never *source* them.
2. **microtopo owner:** lead ruling assigns the audit to Humus/Aquifer, while the GDD/C4 node owner for 1a is Waveform. The audit owner and the node owner differ; that's acceptable but should be confirmed.
3. **Units:** the proposal's v0 §1 uses `sweep_width_m` and `coverage_rate` in km²/h or m²/h; C6 switches to `sweep_width_km`. v0.2 adopts km. `coverage_rate` units remain mixed per row; I recommend fixing them to km²/h.
4. **Prior source:** the proposal's v0 §2 used `lost_person_sim` on `synthetic_flat_terrain`, and v0.1 #7 says "Bedrock procedural prior until resolved". The GDD now makes that permanent (lpb blocked; lost_person_sim out of the game path).
5. **Hours mode:** `optimal_search` supported hours; `Scorer` is km-only. Fine for v0.2; flag it for any later helicopter/UAV nodes.
6. **Score weights / credit values:** all PLACEHOLDER in the proposal. The M1–M3 `budget_credits` stay PLACEHOLDER until the sweep runs.
7. **Confirmed matches:** credits = usage, unlocks = LO mastery (proposal mismatch #4) ✔. Dual budgets (#6) ✔. Swarm ≤10 to start (C2) ✔. Scorer replaces repo scoring (C5) ✔. Node ids 1a–3d match (C4) ✔.

## 9. Loam-N review (v0.2)
- **(a) Scorer:** grep of v0.2 finds `search_theory`/`optimal_search`/`compare_plans` only in prohibitions, the changelog, the audit list and conflict notes, never as a call ✔. NEW-01 is reconciled one-to-one to the four methods ✔.
- **(b) Swarms:** ≤10 to start ✔. **(c) Economy:** credits = usage, LO-only unlocks, dual budgets ✔; matches proposal #4/#6 ✔.
- **(d) DEM:** Bedrock procedural prior ✔.
- **Steering (a):** imports checked ✔; lineage found and gated, not hidden ✔. **(b)** audits listed ✔. **(c)** permissive writer ✔. **(d)** Stone (Academic Press, ISBN 0126724504) and Tobler TR 93-1, both "no DOI" ✔.
- **Units:** W km, z km, A km², r km⁻¹ ✔. `coverage_rate` mixed units flagged (§8.3).
- **Hard rules:** R3 ✔ R4 ✔ R5 ✔ R6 ✔. R7: the referenced case file was not opened; sweep_width reuse blocked pending Verity ✔. R8: nothing committed ✔.
- **Residuals:** §8.1 C3 ruling and the §7 audits block implementation, not this doc.

Loam-N APPROVE
