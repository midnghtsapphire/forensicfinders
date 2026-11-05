# Ledger-Play Balance Proposal — v0.2 (2026-11-04, DOC ONLY)
Status: draft, following Strata's v0.2 rulings. Repo/branch for code and the LEDGER location are pending except where noted. v0.1 and v0 are kept below; **v0.2 overrides them where they conflict.**

## v0.2 changes
**D1. Physics provenance (replaces C3).** Every physics value, **including sweep widths**, comes only from the node's **owning science pair** in GDD v0: Waveform (1a, 1b), Fringe (1c), Backscatter (1d), Aquifer (1e), Deepscan (2a, 2b), Humus (2a εr, 2d, 3a, 3b), Isotope (2c, 3c), Chitin (3b, 3d). Each value needs a URL/DOI citation **and a Verity co-sign**. A value missing either stays `PLACEHOLDER`. Columns: `physics_owner` = GDD owner; added `verity_cosign` (LEDGER ref or `PLACEHOLDER`). The validator rejects a physics value without `citation` + owner match + `verity_cosign`. The C4 table's "owner not in C3 set" notes are void, and `physics_owner` = `gdd_owner` for every node. 2e Fusion has no physics fields of its own; it inherits them from its inputs.

**D2. Ledger-Play scope.** Ledger-Play tunes **only** `cost_credits` and `deploy_time_min`. Budgets, time limits and level parameters in v0 §3 are proposals that Loam must approve; they are not Ledger-Play-owned physics.

**D3. Units.** `sweep_width_km` (km) and `coverage_rate` in **km²/h** for every row. The per-row `coverage_units` field from v0 is dropped. Tier 3 per-sample nodes use `effort_unit: samples` and leave `coverage_rate` null.

**D4. Blocked modules (case-file lineage).** `search_theory.py`, `optimal_search.py` **and `sweep_width.py`** are BLOCKED. They were not opened for v0.1 or v0.2. Their v0 signature notes (from read-only research done before the ruling) are history only, **not interfaces**. Consequences:
- Sweep width fallback: **Loam NEW-10 clean table**. GDD v0.2 (`/workspace/sensecrew/loam/GDD_v0.2.md`, line 64) names it as `fixtures/sweep_width_cited_synthetic.json` with `sweep_width_km`; uncited cells are `null`, flagged "UNCITED — not scorable". **The file does not exist yet (path proposed, TBD).** Note: GDD v0.2's NEW-11 adapter calls `sweep_width.py` functions; under D4 Ledger-Play does not depend on NEW-11.
- `test_no_forbidden_imports` must fail on importing **any** of `search_theory`, `optimal_search`, `sweep_width` (static AST scan + `sys.modules` check after a harness run). The v0 policies `equal/poa_proportional/greedy_psr/optimal/sequential` are reimplemented on the clean `Scorer`; they do not reuse `NAIVE_PLANS`.

**D5. Scorer ownership.** **Bedrock writes the clean `Scorer` spec** (Loam's GDD v0.2 registry list calls it NEW-01 CleanScorer). The C5 Protocol is Ledger-Play's *consumer requirements* only (pod, pos, optimal, update; km, km², km/h; [0,1]). Bedrock's spec takes precedence.

**D6. Registry.** The sweep harness is **NEW-12** (Strata ruling, v0.2 follow-up; supersedes `NEW-xx`, which also matches GDD v0.2 line 94). **NEW-11 (sweep_width adapter) stays disabled while `sweep_width.py` is blocked.**

**D8. Repo licence.** Every repo/output licence field reads: `UNLICENSED (private repo; licence pending Audrey)`. The per-sensor `licence_note` column still records third-party tool licences (e.g. GPL offline-only).

**D7. Swarm.** Unchanged from C2: none started; ≤10 subagents with small token budgets once approved.

---
## v0.1 (kept for history; superseded where v0.2 says so)
Status: v0 accepted by Strata as **draft**; this is v0.1. No code, commits, branches or GitHub writes. Repo/branch and LEDGER location: **still pending**. The v0 text is kept below; where it conflicts with v0.1, **v0.1 wins**.

## v0.1 changes
**C1. Registry number.** *(Superseded by D6: now NEW-12.)* The sweep harness uses the placeholder **`NEW-xx`** until Strata assigns a real `sar/registry.json` id. No existing number is reused.

**C2. Swarm: none yet.** No swarm runs before Strata approves. Once approved, the first swarm is capped at **≤10 subagents**, each with a **small token budget** (exact figure PLACEHOLDER, set by Strata). The ≤100 rule-2 cap is not used in v0.1. Revised brief:
```yaml
swarm_id: ledger-play-sweep-NEW-12-<seq>
status: NOT STARTED (awaiting Strata approval)
objective: "Run sweep cells <a..b> of grid <grid_hash> at SEED=<n>"
output_schema: "swarm/<id>/shard_<k>/{runs.csv, sha256sums.txt} (columns as in v0 §4)"
tools_allowed: [make sweep, python -m ledgerplay.sweep]   # offline; no network; forbidden paths and quarantined modules blocked
stop_condition: "assigned cells written, OR first error/hash mismatch -> stop and report, OR token budget hit"
token_budget_per_subagent: PLACEHOLDER (small; Strata sets)
max_subagents: 10
verity_sampling: ">=10% of shards (at least 1) re-run; byte-identical hashes required"
```
Until then the sweep runs manually (`make sweep SEED=… GRID=…`) by the pair, per rule 4.

**C3. Physics provenance.** *(SUPERSEDED by v0.2 D1.)* Physics columns (`coverage_rate`, `sweep_width_m`, `noise_params`, `weather_mod`, `soil_mod`, depth limits) can only be filled by **Humus, Deepscan or Isotope**, each with a URL/DOI citation and a LEDGER entry. Anything else stays `PLACEHOLDER`. That includes values from other pairs, values from v0, and the `sweep_width_tables.json` sources unless one of those three pairs adopts and cites them. Schema adds `physics_owner` ∈ {humus, deepscan, isotope, PLACEHOLDER} and `physics_ledger_ref`. Validator: a physics value without `citation` **and** an allowed `physics_owner` is rejected.

**C4. Tier/unlock alignment to Loam GDD v0** (`/workspace/sensecrew/loam/GDD_v0.md`, 14 nodes, 3 tiers). Schema change: `unlock_level` (int) is **replaced by** `node_id` (GDD id) + `unlock_rule` (the GDD rule: "LO passes on 3 consecutive seeds") + `gdd_owner`. Order within a tier follows GDD order; Loam owns any cross-tier prerequisites (none are stated in the GDD).

| node_id | name (GDD) | tier | gdd_owner | physics_owner (C3) | cost_credits / deploy_time_min | physics fields | note |
|---|---|---|---|---|---|---|---|
| 1a | LiDAR DEM differencing (M-TMAT) | 1 | Waveform | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | owner not in C3 set |
| 1b | Full-waveform lidar | 1 | Waveform | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | KNOWN GAP: `available: false` |
| 1c | InSAR | 1 | Fringe | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | owner not in C3 set |
| 1d | SAR/NDVI change | 1 | Backscatter | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | owner not in C3 set |
| 1e | Hydrology prior (TWI) | 1 | Aquifer | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | a prior layer, not a detector |
| 2a | GPR | 2 | Deepscan + Humus (εr) | deepscan / humus | PLACEHOLDER | PLACEHOLDER until cited | |
| 2b | Magnetic induction / EMI (metal only) | 2 | Deepscan | deepscan | PLACEHOLDER | PLACEHOLDER (dipole source unverified in GDD) | missing component |
| 2c | Ground gamma (context only) | 2 | Isotope | isotope | PLACEHOLDER | PLACEHOLDER (depth unverified) | `detector: false` |
| 2d | Soil dielectric/moisture | 2 | Humus | humus | PLACEHOLDER | PLACEHOLDER | |
| 2e | Fusion | 2 | Fusion | n/a (derived) | PLACEHOLDER | none: inherits inputs | not a sensor |
| 3a | soil_dna_sensor qPCR | 3 | Humus | humus | PLACEHOLDER | PLACEHOLDER (LOD95/LOQ) | per-sample, not area |
| 3b | GC-MS / 16S | 3 | Humus + Chitin | humus | PLACEHOLDER | PLACEHOLDER | per-sample |
| 3c | LIBS | 3 | Isotope | isotope | PLACEHOLDER | PLACEHOLDER (line DB unverified) | missing component; per-sample |
| 3d | Insect trace / taphonomy | 3 | Chitin | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | owner not in C3 set |

More schema additions: `available` (bool), `detector` (bool), and `effort_unit` ∈ {track_km, hours, samples}, because Tier 3 nodes are priced per sample, not per area.

**C5. Quarantined scoring module.** `search_theory.py` is QUARANTINED under rule 7. It was not opened for this revision, and no interface, import or CLI of it is referenced. **Transitive issue:** v0 verified that `optimal_search.py` imports it, so `optimal_search.py` cannot be called directly either. Scoring now sits behind a small interface; a clean reimplementation (Bedrock/Verity, from published Koopman/Stone theory only) can drop in:
```python
class Scorer(Protocol):              # ledgerplay/scoring.py (proposed)
    def pod(self, w_km: float, track_km: float, area_km2: float) -> float: ...
    def pos(self, segments: list[Segment], effort_km: dict[str, float]) -> float: ...
    def optimal(self, segments: list[Segment], budget_km: float) -> dict[str, float]: ...  # effort per segment
    def update(self, segments: list[Segment], effort_km: dict[str, float]) -> list[Segment]: ...  # posterior POA after a miss
# Segment = {name, area_km2, poa, w_km, speed_kmh|None, is_row: bool}; units: km, km2, km/h; POA/POD/POS in [0,1]
```
- Contract (math only, from the published model and not from any repo file): POD = 1 − exp(−W·z/A); POS = Σ POA·POD; the ROW segment gets no effort; Σ POA = 1. **Citation for the model: PLACEHOLDER** (Stone, *Theory of Optimal Search*, edition/DOI to be confirmed by Verity).
- Adapter `QuarantinedRepoScorer` is **disabled**. Default `CleanScorer` is TBD (owner: Bedrock). Policies `optimal`/`sequential` call `Scorer.optimal`/`Scorer.update`, not repo functions.
- Golden tests are rewritten as contract tests on `Scorer`: KKT conditions, brute force on 2 segments, ROW gets 0, monotone in budget, determinism. `test_no_forbidden_imports` now also fails on `search_theory` and on importing `optimal_search` while it depends on it.
- The v0 score formula is unchanged except that `POS`/`POS_opt` come from `Scorer`. The `compare_plans` baselines become `equal`/`poa_proportional`/`greedy` policies in the harness.

**C6. Units alignment.** GDD units contract uses W in **km**. The table therefore stores `sweep_width_km` (v0 had `sweep_width_m`); the `coverage_rate` units remain explicit per row.

## GDD v0 mismatches / issues to resolve
1. **Physics owners.** Nodes 1a–1e (Waveform, Fringe, Backscatter, Aquifer) and 3d (Chitin) have owners outside C3's allowed set (Humus/Deepscan/Isotope), so they stay PLACEHOLDER. Strata should decide whether to widen C3 or have the three pairs co-sign.
2. **Scoring dependency.** GDD §2 step 4/6, M1, M2 and §6 depend on `search_theory` (bayes_update, coverage_pod) and `optimal_search.compare_plans`. Both are blocked by the quarantine (GDD B2 flags this). Loam's GDD needs a v0.1 that switches to the `Scorer` interface.
3. **Swarm cap.** GDD §5 says "≤100 agents"; Strata's instruction is now ≤10 to start.
4. **Unlock model.** The GDD unlocks by learning-objective mastery, not level/credits, so there is no numeric unlock order beyond tier and listing order. `cost_credits` then prices use, not unlock, unless Loam says otherwise.
5. **Not real sensors / not available.** 1b is a known gap. 1e is a prior, 2e is derived, 2c is context only, and 2b/3c are missing components. These need the `available`/`detector` flags; balancing them now would be premature.
6. **Budget unit.** The GDD mission budget is track km (M1: 10 km). v0 budget is credits. Proposal: two budgets, `budget_track_km` (search effort) and `budget_credits` (sensor use). Loam to confirm.
7. **Prior source.** GDD B1 (`lost_person_sim` needs a real DEM) blocks seeded POA priors for the harness. The sweep uses the Bedrock procedural prior only until that is resolved.

## Still pending (Strata)
Repo/branch; LEDGER path; real registry id for NEW-xx [resolved in v0.2: NEW-12]; per-subagent token budget; clean `Scorer` owner/timeline; ruling on mismatch 1.

---
## v0 (original text, kept for history; superseded where v0.1 says so)

Owner: Ledger-Play pair (Ledger-Play-D / Ledger-Play-N). Status: **proposal, not approved**. No code, branches, commits or GitHub writes were made.
Governing rules: `sensing-games-team-LOCKED-2026-11-04.md` §3 (all 12). Synthetic data only; only `fixtures/*synthetic*` seed scenes; forbidden paths (case/, hfmr/, dossier.py, evidence/, public_records_engine.py, any PII) were not opened and are not referenced by any interface below. Naming: `soil_dna_sensor`. GPL tools offline only; no Ultralytics.
**Core principle: tune cost and time, never physics.** Physics values (sweep width, noise, detection rates) come only from cited sources or are `PLACEHOLDER`; balance knobs are price, deploy time, budget and time limit.

> **DEPRECATED — quarantined module, history only.** The `sweep_width.py` / `optimal_search.py` signatures below were recorded before these modules were blocked (v0.2 D4). They are not interfaces and must not be used.

## 0. Repo research (read-only, gh CLI authenticated as midnghtsapphire, 2026-11-04) — DEPRECATED — quarantined module, history only
Files live in `sar/blue-ocean-sar/realdata/` (not directly under `sar/`). Registry id **130** = `blue-ocean-sar/realdata` (parent 100, tests `python3 -m unittest discover -p test_*.py` in `blue-ocean-sar`).

**VERIFIED — `optimal_search.py`** (Koopman/Stone exponential model; docstring): `z_i` effort (km track or hours), `r_i = W_i/A_i` (per km) or `W_i v_i/A_i` (per h), `POD_i = 1 - exp(-r_i z_i)`, `POS = Σ POA_i·POD_i`; ROW segment never funded; POA must sum to 1. Segments CSV: `name, area_km2, poa, sweep_width_km[, speed_kmh]`. `UNITS = ("km","hours")`.
- `detection_rates(segments, unit="km")`, `solve_lambda(poa, rates, budget)`, `evaluate_plan(segments, effort, unit="km") -> (rows, total)`, `optimal_allocation(segments, budget, unit="km")`, `equal_plan / poa_proportional_plan / greedy_psr_plan(segments, budget, unit)`, `NAIVE_PLANS`, `compare_plans(segments, budget, unit="km")`, `uniformly_optimal_plan(segments, budget, increments, unit)`, `sequential_replan(segments, budget, increments, unit="km")`, `run(segments, budget, increments=1, unit="km")`, `main(argv)`. CLI: `--effort-km`, `--effort-hours`, `--increments`, `--out`. Imports a quarantined module (see v0.1 §C5; not an interface).

**VERIFIED — `sweep_width.py`** + `sweep_width_tables.json` (schema `sweep_width_tables/1`, units `w_m` metres, `speed_kmh`). Every `w_m` is null ("needs field calibration") or keyed to a source; `leads` are never read. Resources include `ground_searcher, hasty_team, airscent_dog, trailing_dog, uav_visual, uav_thermal, …`.
- `load_tables(path)`, `validate_tables(doc)`, `table_width(doc, resource, target, vegetation, visibility)`, `range_factor(doc, visibility)`, `sweep_width_from_range(range_m, visibility=None, factor=None, doc=None)` (W = factor × range), `canopy_factor(cover, k=1.0)`, `canopy_scaled_width(w_open, cover, k=1.0)`, `k_from_view_zenith(deg)`, `resolve_segment(...)`, `process(rows, doc, cal=None, defaults=None, canopy=None, k=1.0, speed_default=None)`, `sourced_summary(doc)`, `main(argv)`. CLI flags: `segments --out --tables --calibration --polygons --name-field --gedi-csv --gedi-h5 --canopy-raster --raster-percent --canopy-k --view-zenith-deg --speed-kmh --allow-missing --list-sourced`.
- Table sources keys: `koester2004, koester2014, chiacchia2015, chiacchia2023, dumencic2025, hakimipanah2025, gedi_l2b` (full citations in the JSON).

**VERIFIED — tests**: `test_sweep_width.py` (TableProvenance incl. `test_no_invented_values_for_dogs_and_aircraft`, `test_validator_rejects_unsourced_value`, RangeTrial, CanopyModel, GediAggregation, RasterCover, SegmentResolution); `test_optimal_search.py` (Optimal: KKT, brute force, beats naive plans, hours mode; Sequential; Cli). Also present: `lost_person_sim.py` (+test; `STRATEGIES = random_walk, route_following, direction_sampling, downhill, stay_put`, `SimParams`, `synthetic_flat_terrain(...)`), `sar/test_registry_coverage.py`, `sar/docs/SOIL_SENSING_TIERS.md` (Tier 1 Screening / 2 Ground survey / 3 Sample analysis).
**ASSUMED (not verified):** exact return dict keys of `optimal_allocation`/`run` beyond `unit, budget, lambda, effort`; [withdrawn in v0.1: quarantined module]; whether any seed-based CLI exists for sweeps; the LEDGER file location.

## 1. v0 sensor balance table schema (`balance/sensors_v0.yaml`, mirrored CSV)
| column | type / units | rule |
|---|---|---|
| `id` | str, snake_case (`gpr_250mhz`, `soil_dna_sensor`, `uav_thermal`) | stable; match sweep_width resource names where they exist |
| `tier` | int 1–3 | = `SOIL_SENSING_TIERS.md` tier; `unlock_level` int separate (Loam owns order) |
| `cost_credits` | int, game credits | **balance knob** |
| `deploy_time_min` | float, minutes | **balance knob** (setup/teardown) |
| `coverage_rate` | float, km²/h or m²/h (`coverage_units`) | **physics**: derive from W (m) × speed (km/h) via sweep_width.py, else cite, else PLACEHOLDER |
| `sweep_width_m` | float or null | from `table_width`/calibration; null ⇒ "needs field calibration" |
| `noise_model` | enum `gaussian`/`poisson`/`exp_detection` | physics |
| `noise_params` | map with units (e.g. `sigma_ns`, `false_alarm_per_km2`) | cited or PLACEHOLDER |
| `weather_mod` | map {clear, rain, fog, night: multiplier on coverage_rate} | physics → cited (e.g. koester2014 range factors) or PLACEHOLDER |
| `soil_mod` | map {sand, loam, clay, wet_clay: multiplier} | physics → cited (Humus/Deepscan) or PLACEHOLDER |
| `citation` | URL/DOI or table source key | required for every non-PLACEHOLDER physics field |
| `licence_note` | str | e.g. "gprMax data generated offline (GPL), not shipped" |
| `units_version` | str | `si_v0` |

Example row (all physics PLACEHOLDER — no values invented):
```yaml
- id: gpr_250mhz
  tier: 2
  unlock_level: PLACEHOLDER   # from Loam
  cost_credits: PLACEHOLDER   # balance knob
  deploy_time_min: PLACEHOLDER
  coverage_rate: PLACEHOLDER  # m2/h, needs citation
  noise_model: gaussian
  noise_params: {sigma: PLACEHOLDER}
  weather_mod: {clear: 1.0, rain: PLACEHOLDER}
  soil_mod: {sand: PLACEHOLDER, wet_clay: PLACEHOLDER}
  citation: PLACEHOLDER
```
Validator (mirrors `validate_tables`): reject any physics value without `citation`; reject a citation on null; `test_no_physics_change_in_balance_diff` fails if a balance PR touches physics columns.

## 2. Scoring
Per mission, from the player's effort allocation `z_i` (km or h), segments built from the synthetic scene (POA from `lost_person_sim` on `synthetic_flat_terrain`, W from `sweep_width.py`):
- `POS = evaluate_plan(segments, effort, unit)` total (dimensionless, 0–1).
- `POS_opt = optimal_allocation(segments, budget, unit)` → efficiency `η = POS / POS_opt` (dimensionless; teaches optimal search).
- Score (points):
  `S = 1000 · [ w_pos·POS + w_eff·η − w_t·max(0, t_used − t_limit)/t_limit − w_b·max(0, spent − budget)/budget ] + bonus_found`
  t in minutes, spend in credits; all weights dimensionless, **PLACEHOLDER** (proposed to be fixed by the §4 sweep, Σ w_pos+w_eff = 1). Overruns are penalised, not hard-failed, so trade-offs stay visible.
- Report naive-plan baselines via `compare_plans` in the debrief (equal / poa_proportional / greedy_psr).

## 3. Difficulty curve (`balance/levels_v0.csv`)
Columns: `level, tier_unlocked, budget_credits, time_limit_min, weather, soil, target_count, target_depth_m, area_km2, segments, seed`.
- Shape: target **POS_opt(level)** declines on a smooth logistic from easy to hard (PLACEHOLDER endpoints); knobs move one or two at a time (budget↓, time↓, area↑, weather worsens, depth↑ only within cited sensor depth ranges).
- Acceptance bands (checked by sweep, values PLACEHOLDER until first sweep): median bot-policy `optimal` reaches POS within band B_L; `random` policy stays clearly below `optimal`; monotone: median S for `optimal` non-increasing with level; no level where cheapest strategy dominates all others (dominance check).

## 4. Seeded sweep harness spec
- CLI: `make sweep SEED=42 GRID=balance/grids/v0.yaml OUT=swarm/<id>/` → `python -m ledgerplay.sweep --seed 42 --grid ... --out ...`. Also `make sweep-verify ID=<id>` (rerun, `sha256sum` compare).
- Determinism: one master `numpy.random.SeedSequence(SEED)`; child seed per (cell, policy, rep) via `spawn` in sorted grid order; no wall-clock, no set/dict-order dependence; JSON with `sort_keys=True`, fixed float format `%.9g`, LF; CSV sorted by key. Same seed ⇒ byte-identical files (golden hash test).
- Grid: cartesian over `cost_scale, deploy_time_scale, budget, time_limit, weather, soil, level` (balance knobs only; physics fixed from table).
- Playtest-bot policies: `random`, `equal`, `poa_proportional`, `greedy_psr` (reuse `NAIVE_PLANS`), `optimal` (`optimal_allocation`), `sequential` (`sequential_replan`), `cheapest_sensor`, `best_coverage_per_credit`.
- Output `swarm/<id>/`: `manifest.json` {seed, grid_hash, git_sha, table_hash, created_by}, `seed_log.csv`, `runs.csv` (`cell_id, policy, rep, seed, POS, POS_opt, eta, t_used_min, spent_credits, score, found`), `summary.json` (per cell: median/IQR score, band pass/fail, dominance flags), `sha256sums.txt`.
- Metrics: POS, η, score distribution, policy rank stability, dominance, band pass rate, variance across reps.
- Swarm brief template (Strata approval required, ≤100 subagents):
```yaml
objective: "Run sweep cells <a..b> of grid <hash> at SEED=<n>"
output_schema: "swarm/<id>/shard_<k>/runs.csv as above + sha256sums.txt"
tools_allowed: [python -m ledgerplay.sweep, make sweep]   # no network, no forbidden paths
stop_condition: "all assigned cells written OR 1 failure -> stop and report"
token_budget: PLACEHOLDER per subagent (Strata sets)
max_subagents: 100
verity_sampling: ">=10% of shards re-run; hashes must match"
```
- Golden tests: (1) existing `test_sweep_width.py`, `test_optimal_search.py` stay green; (2) `test_sweep_deterministic` (two runs, identical bytes); (3) `test_optimal_policy_matches_optimal_allocation`; (4) `test_balance_table_citations`; (5) `test_only_synthetic_fixtures` (scene paths match `fixtures/*synthetic*`); (6) `test_no_forbidden_imports` (greps for forbidden modules).

## 5. XP-pair workflow
- Navigator (Ledger-Play-N) writes the failing test first; Driver implements; Navigator checks units/citations live; seats swap per task.
- No commit without `Ledger-Play-N APPROVE` in LEDGER; Verity green before merge; branch only, never main; never delete—deprecate.
- LEDGER entry template (append-only):
```
2026-11-04T20:xx-07:00 | Ledger-Play-D/N | action: <skill|API|MCP|CLI call or decision> | why: <...>
 | sources: <URL/DOI> | licence: UNLICENSED (private repo; licence pending Audrey) | seed: <n> | artefact: swarm/<id>/sha256sums.txt
 | Ledger-Play-N APPROVE | Verity: <pending|green>
```
- Open questions for Strata: (1) target repo + branch name for `balance/` and `ledgerplay/` (forensicfinders `sar/` vs a new game repo)? (2) LEDGER path? (3) registry.json number for the sweep harness? (4) token budget per sweep subagent? (5) who supplies cited physics values per sensor (Humus/Deepscan/Isotope) and Loam's unlock order? (6) [withdrawn in v0.1: module quarantined]
