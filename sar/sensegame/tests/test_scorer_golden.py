"""Golden tests for the clean Scorer (2310 (NEW-01)). Spec: ../scorer-spec.md.
Drafted by Bedrock-D before any implementation exists; hand values independently recomputed by
the Bedrock-N review of 2026-11-04 (math + decimal, 40 digits; see LEDGER). Math goldens cover
the cited-W Koopman path. M1 goldens are coverage and budget only: M1_W_KM is None until a cited W exists
(Decision B, Discussion #28 comment 19445708). Reference values come from the closed forms
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

# M1 (seed 1001, 10 km track budget). Decision B: M1_W_KM is None until a
# cited W exists. M1_W_SOURCE cites Discussion #28 comment 19445708. The stated 1.456 km
# swath is geometric coverage only (table inputs: H=2000 m AGL, FOV=40 deg).
# The report name is in scorer-spec section 4b. Do not write the swath, or any
# fraction of it, into M1_W_KM.
M1_W_KM = None
M1_W_SOURCE = (
    "https://github.com/midnghtsapphire/forensicfinders/discussions/28"
    "#discussioncomment-19445708"
)
M1_GEOMETRIC_SWATH_KM = 1.456
M1_GEOMETRIC_H_M = 2000.0
M1_GEOMETRIC_FOV_DEG = 40.0
M1_BUDGET_KM = 10.0
# Synthetic player plan, kilometres of track. Equal split. Not a detection optimum.
M1_PLAN_KM = {"S1": 2.5, "S2": 2.5, "S3": 2.5, "S4": 2.5, "ROW": 0.0}


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


# ---- exponential coverage model (not M1 detection) ----------------------------
def test_exponential_coverage_model_closed_form(s):
    """Player-supplied C. MODEL: 1 - exp(-C) via -expm1(-C). Not M1 detection."""
    assert s.exponential_coverage_model(0.0) == 0.0
    assert s.exponential_coverage_model(1.0) == pytest.approx(0.6321205588285577, abs=TOL_UNIT)
    assert s.exponential_coverage_model(0.5) == pytest.approx(0.3934693402873666, abs=TOL_UNIT)

def test_exponential_coverage_model_is_labelled_a_model(s):
    doc = s.exponential_coverage_model.__doc__ or ""
    lowered = doc.lower()
    assert "model" in lowered
    assert "not calibrated detection" in lowered

@pytest.mark.parametrize("bad", [-0.1, float("nan"), float("inf")])
def test_exponential_coverage_model_rejects_bad_coverage(s, bad):
    with pytest.raises(ScorerError):
        s.exponential_coverage_model(bad)


def test_geometric_coverage_rejects_bad_inputs(s):
    with pytest.raises(ScorerError):
        s.geometric_survey_km2(-1.0, 1.0)
    with pytest.raises(ScorerError):
        s.geometric_coverage(1.456, 1.0, 0.0)
    with pytest.raises(ScorerError):
        s.track_budget_spent_km({"S1": -1.0})


# ---- M1 coverage and budget (Decision B; M1_W_KM is None until a cited W exists) --
_DECISION_B = (
    "https://github.com/midnghtsapphire/forensicfinders/discussions/28"
    "#discussioncomment-19445708"
)

def test_m1_effective_w_stays_null():
    """Decision B: no numeric effective W. Source cites the discussion comment."""
    import inspect
    import sensegame.search_core as core

    assert M1_W_KM is None
    assert M1_W_SOURCE == _DECISION_B
    assert M1_GEOMETRIC_SWATH_KM == 1.456
    assert M1_GEOMETRIC_H_M == 2000.0
    assert M1_GEOMETRIC_FOV_DEG == 40.0
    assert M1_GEOMETRIC_SWATH_KM != M1_W_KM
    # A geometric fraction is still not an effective sweep width.
    assert (0.9 * M1_GEOMETRIC_SWATH_KM) != M1_W_KM
    library = inspect.getsource(core.CleanScorer)
    assert "1.456" not in library
    assert "0.9" not in library

def test_m1_budget_spend_and_geometric_coverage(s):
    """Equal 2.5 km split of the 10 km budget. Surveyed area is not detection.

    Hand values (decimal): 1.456 * 2.5 = 3.64 km²; 1.456 * 10 = 14.56 km²;
    coverage on areas 1, 2, 1.5, 0.5 km² is 3.64, 1.82, 182/75, 7.28.
    """
    doc = s.geometric_survey_km2.__doc__ or ""
    assert "surveyed is not detected" in doc.lower()
    assert s.track_budget_spent_km(M1_PLAN_KM) == pytest.approx(10.0, abs=TOL_UNIT)
    assert s.geometric_survey_km2(M1_GEOMETRIC_SWATH_KM, 0.0) == 0.0
    expected_coverage = {
        "S1": 3.64,
        "S2": 1.82,
        "S3": 2.4266666666666667,  # 182/75
        "S4": 7.28,
    }
    areas = {"S1": 1.0, "S2": 2.0, "S3": 1.5, "S4": 0.5}
    surveyed_parts = []
    for name, area in areas.items():
        surveyed = s.geometric_survey_km2(M1_GEOMETRIC_SWATH_KM, M1_PLAN_KM[name])
        assert surveyed == pytest.approx(3.64, abs=TOL_UNIT)
        assert s.geometric_coverage(
            M1_GEOMETRIC_SWATH_KM, M1_PLAN_KM[name], area
        ) == pytest.approx(expected_coverage[name], abs=TOL_UNIT)
        surveyed_parts.append(surveyed)
    assert math.fsum(surveyed_parts) == pytest.approx(14.56, abs=TOL_UNIT)
    assert s.geometric_survey_km2(M1_GEOMETRIC_SWATH_KM, M1_BUDGET_KM) == pytest.approx(
        14.56, abs=TOL_UNIT
    )

def test_m1_coverage_path_does_not_produce_detection(s, monkeypatch):
    """Budget and geometric coverage must not call detection or the coverage model."""
    def boom(*_args, **_kwargs):
        raise AssertionError("coverage path called a detection or model method")

    for name in ("pod", "pos", "optimal", "update", "exponential_coverage_model"):
        monkeypatch.setattr(CleanScorer, name, boom)
    assert s.track_budget_spent_km(M1_PLAN_KM) == pytest.approx(10.0, abs=TOL_UNIT)
    assert s.geometric_survey_km2(M1_GEOMETRIC_SWATH_KM, 2.5) == pytest.approx(3.64, abs=TOL_UNIT)
    assert s.geometric_coverage(M1_GEOMETRIC_SWATH_KM, 2.5, 1.0) == pytest.approx(3.64, abs=TOL_UNIT)

def test_m1_null_w_detection_path_raises(s):
    """pos/optimal/update still refuse null W. They are not the M1 score."""
    segs = [
        seg("S1", 1.0, 0.4, None),
        seg("S2", 2.0, 0.25, None),
        seg("S3", 1.5, 0.15, None),
        seg("S4", 0.5, 0.1, None),
        seg("ROW", 0.0, 0.1, 0.0, is_row=True),
    ]
    assert all(g.w_km is None for g in segs if not g.is_row)
    assert all(g.w_km != M1_GEOMETRIC_SWATH_KM for g in segs)
    assert issubclass(UncitedSweepWidth, ScorerError)
    with pytest.raises(UncitedSweepWidth):
        s.pos(segs, M1_PLAN_KM)
    with pytest.raises(UncitedSweepWidth):
        s.optimal(segs, M1_BUDGET_KM)
    with pytest.raises(UncitedSweepWidth):
        s.update(segs, M1_PLAN_KM)
