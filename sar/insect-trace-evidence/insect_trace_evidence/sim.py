"""1050 insect-trace-evidence: seeded analytic ADD insect-development sim (training games only).
Clean-room ADD (averaging method, daily mean minus base, floored at 0) from the literature:
  Amendt et al. 2007 Int J Legal Med doi:10.1007/s00414-006-0086-x
  Nabity et al. 2006 J Med Entomol 43(6):1276 (full SICI DOI in docs/sensecrew/chitin/SPEC_1050)
Does NOT import realdata/refloat_timing.py (Verity gate). Synthetic fixtures only.
Licence: UNLICENSED (private repo; licence pending Audrey)."""
import json, os, random
LICENCE = "UNLICENSED (private repo; licence pending Audrey)"
SPECIES_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "species_synthetic.json")

def daily_add(tmax_c, tmin_c, base_c):
    return max(0.0, (tmax_c + tmin_c) / 2.0 - base_c)

def soil_modifier(soil_moisture_vwc=None):
    """Identity until Humus co-signs a literature-cited moisture effect."""
    return 1.0

def run(seed, days=30, mean_c=22.0, swing_c=6.0, soil_moisture_vwc=None):
    sp = json.load(open(SPECIES_FIXTURE))
    rng = random.Random(seed)
    mod = soil_modifier(soil_moisture_vwc)
    add, rows = 0.0, []
    for i in range(days):
        m = mean_c + rng.uniform(-3.0, 3.0)
        tmax, tmin = round(m + swing_c, 2), round(m - swing_c, 2)
        add = round(add + daily_add(tmax, tmin, sp["base_c"]) * mod, 4)
        stage = [s["name"] for s in sp["stages"] if add >= s["add_threshold"]][-1]
        rows.append({"day": i, "tmax_c": tmax, "tmin_c": tmin,
                     "add_cumulative_degree_days": add, "stage": stage})
    return {"component": "1050", "synthetic": True, "licence": LICENCE, "seed": seed,
            "units": {"temperature": "degC", "add": "degree-days"},
            "species": sp, "days": rows}

def to_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))
