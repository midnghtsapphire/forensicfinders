import argparse, sys
from . import sim
p = argparse.ArgumentParser(prog="insect_trace_add_sim", description="Synthetic ADD training sim (2350)")
p.add_argument("--seed", type=int, required=True); p.add_argument("--days", type=int, default=30)
p.add_argument("--soil-moisture-vwc", default=None, help="volumetric water content m3/m3; clamped to 0.0-0.5")
p.add_argument("--add-engine", choices=sim.ENGINES, default="refloat_timing")
a = p.parse_args()
vwc = None
if a.soil_moisture_vwc is not None:
    try:
        vwc = sim.validate_soil_moisture(float(a.soil_moisture_vwc))
    except ValueError:
        p.error(f"soil_moisture_vwc must be a finite number, got {a.soil_moisture_vwc!r}")
out = sim.run(seed=a.seed, days=a.days, soil_moisture_vwc=vwc, add_engine=a.add_engine)
if "label" in out["add_engine"]:
    print(f"LABEL: ADD helpers reused from refloat_timing; its primary model is a {out['add_engine']['label']}.",
          file=sys.stderr)
print(sim.to_json(out))
