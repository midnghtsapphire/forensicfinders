"""FAILING-FIRST golden tests for the clean Scorer (2310 (NEW-01)). Spec: ../scorer-spec.md.
Drafted by Bedrock-D before any implementation exists; hand values independently recomputed by
the Bedrock-N review of 2026-11-04 (math + decimal, 40 digits; see LEDGER). Math goldens are green once CleanScorer (2310) is present. M1 tests are xfail while M1_W_KM
is unset until citation (awaiting cited sweep width from Waveform; owning sensor pair + Verity co-sign required; do not invent W). Reference values come from the closed forms
in the spec (Koopman 1956/57; Charnes & Cooper 1958; Stone 1975), NOT from any repo module.

Tolerances (lead ruling 2026-11-04):
  TOL_UNIT     = 1e-12  closed-form unit goldens (this file's hand values)
  TOL_CONTRACT = 1e-9   cross-language / Loam GDD contract (sum POA; M2 posterior)
"""
import math
import pytest

try:
    from sensegame.search_core import CleanScorer, Segment, ScorerError, UncitedSweepWidth  # does not exist yet
    _IMPORT_ERROR = None
except ImportError as exc:  # expected until 2310 (NEW-01) is implemented
    _IMPORT_ERROR = exc
    CleanScorer = Segment = None
    ScorerError = UncitedSweepWidth = Exception

TOL_UNIT = 1e-12
TOL_CONTRACT = 1e-9
E1 = -math.expm1(-1.0)  # 1 - e^-1 = 0.6321205588285577

# M1 "Water-filling" (Loam GDD v0.1-v0.3 M1, seed 1001, 10 km budget).
# M1 W unset until citation: W must come from the owning sensor pair with a citation + Verity co-sign (GDD L1/R5).
# Request drafted in specs/discussion-drafts/m1-sweep-width.md. Do NOT fill in a guessed number.
M1_W_KM = None
M1_W_SOURCE = None
M1_BUDGET_KM = 10.0


def seg(name, area_km2, poa, w_km, is_row=False, speed_kmh=None):
    return Segment(name=name, area_km2=area_km2, poa=poa, w_km=w_km,
                   speed_kmh=speed_kmh, is_row=is_row)


@pytest.fixture
def s():
    if _IMPORT_ERROR is not None:
        raise _IMPORT_ERROR
    return CleanScorer()


@pytest.fixture
def three(s):
    return [seg("A", 1.0, 0.5, 0.5), seg("B", 2.0, 0.3, 0.5), seg("ROW", 0.0, 0.2, 0.0, is_row=True)]


# ---- pod -------------------------------------------------------------------
def test_pod_exponential_law(s):
    assert s.pod(w_km=0.5, track_km=2.0, area_km2=1.0) == pytest.approx(0.6321205588285577, abs=TOL_UNIT)

def test_pod_zero_effort_is_zero(s):
    assert s.pod(0.5, 0.0, 1.0) == 0.0

def test_pod_zero_width_is_zero(s):
    assert s.pod(0.0, 5.0, 1.0) == 0.0

def test_pod_large_coverage_saturates_at_most_one(s):  # 1-e^-50 rounds to 1.0 in binary64
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


# ---- optimal (Koopman/Charnes-Cooper water-filling) -------------------------
@pytest.fixture
def two(s):
    # r_i = W/A = 1 km^-1 both; POA .6/.3, ROW .1
    return [seg("A", 1.0, 0.6, 1.0), seg("B", 1.0, 0.3, 1.0), seg("ROW", 0.0, 0.1, 0.0, is_row=True)]

def test_optimal_two_segment_closed_form(s, two):
    z = s.optimal(two, budget_km=1.0)
    assert z["A"] == pytest.approx(0.8465735902799727, abs=TOL_UNIT)   # (1+ln2)/2
    assert z["B"] == pytest.approx(0.15342640972002736, abs=TOL_UNIT)  # (1-ln2)/2
    assert z.get("ROW", 0.0) == 0.0
    assert s.pos(two, z) == pytest.approx(0.3853416690235759, abs=TOL_UNIT)  # 0.9 - 2*lambda

def test_optimal_kkt_equal_marginal(s, two):
    z = s.optimal(two, budget_km=1.0)
    m = [p * 1.0 * math.exp(-1.0 * z[n]) for n, p in (("A", 0.6), ("B", 0.3))]
    # lambda = 0.6*exp(-(1+ln2)/2) = 0.6/sqrt(2e)
    assert m[0] == pytest.approx(m[1], abs=TOL_UNIT) and m[0] == pytest.approx(0.25732916548821205, abs=TOL_UNIT)

def test_optimal_small_budget_all_to_best(s, two):
    z = s.optimal(two, budget_km=0.5)  # 0.5 < ln 2 -> B unfunded
    assert z["A"] == pytest.approx(0.5, abs=TOL_UNIT) and z.get("B", 0.0) == 0.0
    assert s.pos(two, z) == pytest.approx(0.23608160417241994, abs=TOL_UNIT)

def test_optimal_spends_exact_budget(s, three):
    z = s.optimal(three, budget_km=7.0)
    assert math.fsum(z.values()) == pytest.approx(7.0, abs=TOL_UNIT)

def test_optimal_beats_brute_force_grid(s, two):
    best = max(s.pos(two, {"A": a / 1000, "B": 1 - a / 1000}) for a in range(1001))
    assert s.pos(two, s.optimal(two, 1.0)) >= best - TOL_UNIT

def test_optimal_monotone_in_budget(s, three):
    vals = [s.pos(three, s.optimal(three, b)) for b in (0, 1, 2, 4, 8, 16)]
    assert all(b >= a - TOL_UNIT for a, b in zip(vals, vals[1:]))

def test_optimal_zero_budget(s, three):
    assert all(v == 0.0 for v in s.optimal(three, 0.0).values())


# ---- update (Bayes after unsuccessful search) --------------------------------
def test_update_posterior_after_miss(s, three):
    post = {g.name: g.poa for g in s.update(three, {"A": 2.0, "B": 4.0})}
    assert post["A"] == pytest.approx(0.372118953005194, abs=TOL_UNIT)
    assert post["B"] == pytest.approx(0.22327137180311638, abs=TOL_UNIT)
    assert post["ROW"] == pytest.approx(0.40460967519168967, abs=TOL_UNIT)
    assert math.fsum(post.values()) == pytest.approx(1.0, abs=TOL_UNIT)

def test_update_is_pure(s, three):
    before = [g.poa for g in three]
    s.update(three, {"A": 1.0})
    assert [g.poa for g in three] == before

def test_update_zero_effort_is_identity(s, three):
    assert [g.poa for g in s.update(three, {})] == [g.poa for g in three]

def test_update_certain_detection_everywhere_raises(s):
    segs = [seg("A", 1.0, 1.0, 1.0)]  # POA 1, no ROW; POS -> 1 in the limit
    with pytest.raises(ScorerError):
        s.update(segs, {"A": 1e6})


# ---- determinism -------------------------------------------------------------
def test_deterministic_repr(s, three):
    a = repr(sorted(s.optimal(three, 5.0).items()))
    b = repr(sorted(CleanScorer().optimal(list(reversed(three)), 5.0).items()))
    assert a == b


# ---- Loam GDD contract (1e-9, cross-language) ----------------------------------
def test_contract_poa_sum_within_1e_9_accepted(s):
    segs = [seg("A", 1.0, 0.5, 1.0), seg("B", 1.0, 0.5 + 5e-10, 1.0)]
    assert s.pos(segs, {}) == 0.0

def test_contract_poa_sum_beyond_1e_9_rejected(s):
    with pytest.raises(ScorerError):
        s.pos([seg("A", 1.0, 0.5, 1.0), seg("B", 1.0, 0.5 + 2e-9, 1.0)], {})

def test_contract_m2_posterior_matches_analytic(s, three):
    """GDD M2 LO: 'posterior matches analytic value to 1e-9'. Analytic: p_i e^-C_i / (1 - POS)."""
    post = {g.name: g.poa for g in s.update(three, {"A": 2.0, "B": 4.0})}
    den = 1.0 - 0.8 * E1
    for name, want in (("A", 0.5 * math.exp(-1.0) / den), ("B", 0.3 * math.exp(-1.0) / den), ("ROW", 0.2 / den)):
        assert post[name] == pytest.approx(want, abs=TOL_CONTRACT)

def test_uncited_sweep_width_is_unscorable(s):
    """GDD v0.2/v0.3 invariant: w_km = null -> UncitedSweepWidth (subclass of ScorerError); never substituted."""
    segs = [seg("A", 1.0, 0.6, None), seg("B", 1.0, 0.4, 1.0)]
    with pytest.raises(UncitedSweepWidth):
        s.pos(segs, {"A": 1.0})
    with pytest.raises(UncitedSweepWidth):
        s.optimal(segs, 1.0)


# ---- M1 water-filling (M1 W unset until citation; xfail on purpose) -------------
def _require_m1_w():
    if M1_W_KM is None or M1_W_SOURCE is None:
        pytest.fail("M1 W unset until citation: awaiting cited sweep width from Waveform. "
                    "Owning sensor pair must supply W_km with a "
                    "citation and Verity co-sign (GDD L1/R5); see specs/discussion-drafts/m1-sweep-width.md. "
                    "Expected failure; do not insert a guessed value.", pytrace=False)

@pytest.mark.xfail(
    reason="M1 W unset until citation; awaiting cited sweep width from Waveform (GDD L1/R5); see "
           "docs/sensecrew/bedrock/specs/discussion-drafts/m1-sweep-width.md",
    strict=True,
)
def test_m1_sweep_width_is_cited():
    _require_m1_w()
    assert M1_W_KM > 0 and math.isfinite(M1_W_KM)

@pytest.mark.xfail(
    reason="M1 W unset until citation; awaiting cited sweep width from Waveform (GDD L1/R5); see "
           "docs/sensecrew/bedrock/specs/discussion-drafts/m1-sweep-width.md",
    strict=True,
)
def test_m1_optimal_spends_budget_and_beats_naive(request):
    _require_m1_w()
    s = request.getfixturevalue("s")
    segs = [seg("S1", 1.0, 0.4, M1_W_KM), seg("S2", 2.0, 0.25, M1_W_KM), seg("S3", 1.5, 0.15, M1_W_KM),
            seg("S4", 0.5, 0.1, M1_W_KM), seg("ROW", 0.0, 0.1, 0.0, is_row=True)]  # synthetic POA/areas
    z = s.optimal(segs, M1_BUDGET_KM)
    assert math.fsum(z.values()) == pytest.approx(M1_BUDGET_KM, abs=TOL_UNIT)
    even = {n: M1_BUDGET_KM / 4 for n in ("S1", "S2", "S3", "S4")}
    assert s.pos(segs, z) >= s.pos(segs, even) - TOL_UNIT
