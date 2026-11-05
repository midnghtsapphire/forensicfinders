import argparse
from . import sim
p = argparse.ArgumentParser(prog="insect_trace_evidence", description="Synthetic ADD training sim (1050)")
p.add_argument("--seed", type=int, required=True); p.add_argument("--days", type=int, default=30)
a = p.parse_args(); print(sim.to_json(sim.run(seed=a.seed, days=a.days)))
