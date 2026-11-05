# Scorer spec — 2310 (NEW-01, child of 2300 sensegame) clean search core (DESIGN DOC, 2026-11-04)
Owner: Bedrock pair (Bedrock-D / Bedrock-N). Status: **draft, not approved**. No code, commits or pushes.
Clean-room: derived only from the published papers below. No quarantined module (rule 7 list, nor the
quarantined scoring module or the module that imports it) was opened, grepped or referenced.

## 1. Interface (matches ledger-play v0.1 §C5 `Scorer` Protocol)
Module: `sensegame/search_core.py` (GDD v0.1 2310 (NEW-01)); `ledgerplay/scoring.py` re-exports `CleanScorer` as the default `Scorer`.
```python
@dataclass(frozen=True)
class Segment:
    name: str; area_km2: float; poa: float; w_km: float | None   # None = uncited -> unscorable
    speed_kmh: float | None = None; is_row: bool = False

class ScorerError(ValueError): ...
class UncitedSweepWidth(ScorerError): ...   # w_km is None (GDD v0.2/v0.3 invariant)

class CleanScorer:                      # stateless, pure, deterministic
    def pod(self, w_km: float, track_km: float, area_km2: float) -> float
    def pos(self, segments: list[Segment], effort_km: dict[str, float]) -> float
    def optimal(self, segments: list[Segment], budget_km: float) -> dict[str, float]
    def update(self, segments: list[Segment], effort_km: dict[str, float]) -> list[Segment]
```
Hours mode (optional, v0.2): effort in h is converted by `z_km = z_h * speed_kmh` before any call; the core only ever sees km.

## 2. Units
A km² · W km · z (track length) km · r = W/A km⁻¹ · coverage C = W·z/A (dimensionless) · POA, POD, POS ∈ [0,1].

## 3. Math (published model)
- **POD (exponential / random-search detection law)**, Koopman 1956 II: `POD = 1 − exp(−W·z/A)`. Implement as `-math.expm1(-W*z/A)` for accuracy at small coverage.
- **POS**: `POS = Σ_i POA_i · POD_i` (ROW contributes 0; ROW is never searched).
- **Optimal allocation** (Koopman 1957 III; Charnes & Cooper 1958; Stone 1975 ch. 2): maximise Σ p_i(1−e^{−r_i z_i}) s.t. Σ z_i = B, z_i ≥ 0. Concave ⇒ KKT is sufficient:
  `z_i = max(0, ln(p_i r_i / λ) / r_i)`, λ chosen so Σ z_i = B ("water-filling").
  Algorithm (deterministic, no iterative tolerance drift): sort searchable segments by `p_i r_i` desc (tie-break by `name`); for k = 1..n take the top-k set S, solve `ln λ = (Σ_S ln(p_i r_i)/r_i − B) / Σ_S 1/r_i`; accept the largest k with `p_k r_k > λ`. Closed form, O(n log n). Segments with r_i = 0 or p_i = 0 get 0.
- **Bayesian update after unsuccessful search** (Stone 1975; Koopman 1956 II): `POA_i' = POA_i (1 − POD_i) / (1 − POS)`; ROW `' = POA_row / (1 − POS)`. Returns new `Segment`s; inputs untouched.

## 4. Validation & edge cases (raise `ScorerError`)
- non-finite or negative W, z, B; `area_km2 <= 0` on a non-ROW segment; ROW with effort > 0; unknown segment key;
  duplicate names; more than one ROW; `|Σ POA − 1| > 1e-9` (no silent renormalising).
- W = 0 or z = 0 ⇒ POD = 0 exactly. B = 0 ⇒ all-zero plan. All segments unsearchable ⇒ all-zero plan (budget unspent, flagged in result metadata in v0.2).
- `update` when `1 − POS < 1e-15` ⇒ `ScorerError` (posterior undefined).
- Missing keys in `effort_km` mean 0 effort.
- A non-ROW segment with `w_km is None` (uncited, GDD R5/L1) ⇒ `UncitedSweepWidth` from `pos`/`optimal`/`update`; never substituted.

## 4a. Tolerances (lead ruling 2026-11-04)
- **1e-12** (`TOL_UNIT`): closed-form unit goldens in this spec.
- **1e-9** (`TOL_CONTRACT`): cross-language / Loam GDD contract — Σ POA check and the M2 posterior (GDD v0.1–v0.3 M2 LO).
- DEM fixtures: SHA-256 exact (see dem-fixture-spec). No other tolerance level is used.

## 4b. M1 sweep width
M1 (seed 1001, 10 km budget) needs a cited W. **W is a PLACEHOLDER** until the owning sensor pair supplies a value with citation + Verity co-sign (GDD L1). The M1 tests fail on purpose with a PLACEHOLDER message. Request draft: `specs/discussion-drafts/m1-sweep-width.md`.

## 5. Determinism
Pure functions; no RNG; no globals; iterate segments in a canonical sort (by `name`) so input order cannot change floats; use `math.fsum` for sums; stdlib `math` only (no numpy) so results are identical across platforms with IEEE-754 doubles; output dict keys sorted. Floats serialised as `repr` (shortest round-trip) or `%.17g`.

## 6. Golden tests (failing first) — `specs/tests/test_scorer_golden.py`
Hand-computed references (all from closed forms):
| case | inputs | expected |
|---|---|---|
| pod | W 0.5, z 2, A 1 → C=1 | 1−e⁻¹ = 0.6321205588285577 |
| pos | A(1 km², .5, W .5) z 2; B(2 km², .3, W .5) z 4; ROW .2 | 0.8(1−e⁻¹) = 0.5056964470628461 |
| optimal | A,B r=1 km⁻¹, POA .6/.3, ROW .1, B=1 km | z_A=(1+ln2)/2=0.8465735902799727 km, z_B=(1−ln2)/2=0.15342640972002736 km, POS = 0.9−2λ = 0.3853416690235759, λ=0.6/√(2e)=0.25732916548821205 km⁻¹ |
| optimal small budget | same, B=0.5 (< ln 2) | z_A=0.5, z_B=0, POS 0.6(1−e^−0.5)=0.23608160417241994 |
| update | pos case; p_i e^{−C_i}/(1−POS) | A 0.372118953005194, B 0.22327137180311638, ROW 0.40460967519168967 |
Plus: GDD 1e-9 contract tests (Σ POA accept/reject, M2 posterior), uncited-W rejection, M1 tests (fail on PLACEHOLDER W), KKT equal-marginal check, brute force on a 1001-point grid, monotone in budget, exact budget spend, purity, input-order invariance, error cases.
Run: `make test-scorer` → `python -m pytest specs/tests/test_scorer_golden.py` (every test fails with the ImportError today, by design; M1 tests fail with the PLACEHOLDER-W message first).

```python
# ---- pod -------------------------------------------------------------------
def test_pod_exponential_law(s):
    assert s.pod(w_km=0.5, track_km=2.0, area_km2=1.0) == pytest.approx(0.6321205588285577, abs=TOL_UNIT)

def test_pod_zero_effort_is_zero(s):
    assert s.pod(0.5, 0.0, 1.0) == 0.0

def test_pod_zero_width_is_zero(s):
    assert s.pod(0.0, 5.0, 1.0) == 0.0

def test_pod_large_coverage_saturates_at_most_one(s):
    p = s.pod(1.0, 50.0, 1.0)
    assert 0.0 < p <= 1.0 and p == pytest.approx(1.0 - math.exp(-50.0), abs=TOL_UNIT)

@pytest.mark.parametrize("args", [(0.5, 1.0, 0.0), (0.5, 1.0, -1.0), (-0.1, 1.0, 1.0),
                                  (0.5, -1.0, 1.0), (float("nan"), 1.0, 1.0), (0.5, float("inf"), 1.0)])
def test_pod_rejects_bad_inputs(s, args):
    with pytest.raises(ScorerError):
        s.pod(*args)


# ---- pos -------------------------------------------------------------------
def test_pos_sum_poa_pod(s, three):
    assert s.pos(three, {"A": 2.0, "B": 4.0}) == pytest.approx(0.5056964470628461, abs=TOL_UNIT)

def test_pos_missing_segment_means_zero_effort(s, three):
    assert s.pos(three, {"A": 2.0}) == pytest.approx(0.5 * E1, abs=TOL_UNIT)

def test_pos_effort_on_row_rejected(s, three):
    with pytest.raises(ScorerError):
        s.pos(three, {"ROW": 1.0})

def test_pos_unknown_segment_rejected(s, three):
    with pytest.raises(ScorerError):
        s.pos(three, {"Z": 1.0})

def test_poa_must_sum_to_one(s):
    with pytest.raises(ScorerError):
        s.pos([seg("A", 1, 0.5, 1), seg("B", 1, 0.4, 1)], {})

# ... full file: specs/tests/test_scorer_golden.py
```

## 7. Citations
| ref | id | status |
|---|---|---|
| Koopman, B.O. (1956) The Theory of Search. I. Kinematic Bases. *Operations Research* 4(3):324–346 | doi:10.1287/opre.4.3.324 | VERIFIED (Crossref, 2026-11-04) |
| Koopman, B.O. (1956) The Theory of Search. II. Target Detection. *Operations Research* 4(5):503–531 | doi:10.1287/opre.4.5.503 | VERIFIED (Crossref) |
| Koopman, B.O. (1957) The Theory of Search. III. The Optimum Distribution of Searching Effort. *Operations Research* 5(5):613–626 | doi:10.1287/opre.5.5.613 | VERIFIED (Crossref; Crossref title field reads only "The Theory of Search") |
| Charnes, A. & Cooper, W.W. (1958) The Theory of Search: Optimum Distribution of Search Effort. *Management Science* 5(1):44–50 | doi:10.1287/mnsc.5.1.44 | VERIFIED (Crossref) |
| Stone, L.D. (1975) *Theory of Optimal Search*. Academic Press, Mathematics in Science and Engineering 118 | ISBN 0-12-672450-4 (978-0-12-672450-9) | PARTLY VERIFIED: ISBN listed by Open Library for this title; edition-to-ISBN mapping not checked. Book-level DOI: none found (Crossref only has chapter 10.1016/s0076-5392(08)60541-x "Preface") — UNVERIFIED, do not cite as a DOI |
| Stone, L.D. (1989, 2nd ed.) *Theory of Optimal Search*. ORSA/MAS | ISBN 1-877640-00-X | PARTLY VERIFIED (Open Library listing) |
Chapter/page numbers for Stone are not cited (not checked).
