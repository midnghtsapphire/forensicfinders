"""2350 insect-trace-add-sim: seeded analytic ADD insect-development sim (training games only).
ADD = averaging method (daily mean minus base, floored at 0), per the literature:
  Amendt et al. 2007 Int J Legal Med doi:10.1007/s00414-006-0086-x
  Nabity et al. 2006 J Med Entomol 43(6):1276 (full SICI DOI in docs/sensecrew/chitin/SPEC_2350)
Default engine reuses daily_contribution/accumulate from realdata/refloat_timing.py (Verity R7 CLEAR)
via refloat_adapter; output metadata always carries its LABEL "preprint, not peer-reviewed".
Species thresholds stay synthetic. Licence: UNLICENSED (private repo; licence pending Audrey)."""
import json, math, numbers, os, random
LICENCE = "UNLICENSED (private repo; licence pending Audrey)"
SPECIES_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "species_synthetic.json")
VWC_MIN, VWC_MAX = 0.0, 0.5
ENGINES = ("refloat_timing", "clean-room")


def daily_add(tmax_c, tmin_c, base_c):
    return max(0.0, (tmax_c + tmin_c) / 2.0 - base_c)


def validate_soil_moisture(v):
    """None passes through; else must be a finite real number (bool rejected)."""
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, numbers.Real) or not math.isfinite(v):
        raise ValueError(f"soil_moisture_vwc must be a finite number (m3/m3), got {v!r}")
    return float(v)


def clamp_soil_moisture(v):
    return None if v is None else min(VWC_MAX, max(VWC_MIN, v))


def soil_modifier(soil_moisture_vwc=None):
    """Identity: no literature-cited moisture effect on ADD adopted (Humus APPROVE: identity OK)."""
    return 1.0


def load_species():
    with open(SPECIES_FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def run(seed, days=30, mean_c=22.0, swing_c=6.0, soil_moisture_vwc=None, add_engine="refloat_timing"):
    if add_engine in ("refloat", "refloat_timing"):
        add_engine = "refloat_timing"
    if add_engine not in ENGINES:
        raise ValueError(f"add_engine must be one of {ENGINES}")
    vwc_in = validate_soil_moisture(soil_moisture_vwc)
    vwc = clamp_soil_moisture(vwc_in)
    sp = load_species()
    rng = random.Random(seed)
    mod = soil_modifier(vwc)
    temps = []
    for _ in range(days):
        m = mean_c + rng.uniform(-3.0, 3.0)
        temps.append((round(m + swing_c, 2), round(m - swing_c, 2)))
    if add_engine == "refloat_timing":
        from . import refloat_adapter as ra
        contribs = [c for c, _ in ra.accumulate([(a + b) / 2.0 for a, b in temps], sp["base_c"])]
        engine_meta = ra.metadata()
    else:
        contribs = [daily_add(a, b, sp["base_c"]) for a, b in temps]
        engine_meta = {"name": "clean-room", "source": "sim.daily_add (Amendt 2007 averaging method)"}
    add, rows = 0.0, []
    for i, ((tmax, tmin), c) in enumerate(zip(temps, contribs)):
        add = round(add + c * mod, 4)
        stage = [s["name"] for s in sp["stages"] if add >= s["add_threshold"]][-1]
        rows.append({"day": i, "tmax_c": tmax, "tmin_c": tmin,
                     "add_cumulative_degree_days": add, "stage": stage})
    return {"component": "2350", "synthetic": True, "licence": LICENCE, "seed": seed,
            "units": {"temperature": "degC", "add": "degree-days", "soil_moisture": "m3/m3 (VWC)"},
            "add_engine": engine_meta,
            "soil_moisture_vwc_input": vwc_in, "soil_moisture_vwc_clamped": vwc,
            "soil_moisture_vwc_bounds": [VWC_MIN, VWC_MAX],
            "species": sp, "days": rows}


def to_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))
