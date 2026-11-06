#!/usr/bin/env bash
# Humus: manual Topp/Mironov cross-check (same as `make sim-dielectric`).
# Usage: ./run_sim_dielectric.sh [SEED] [N_THETA] [N_CLAY] [FREQ_HZ]
set -euo pipefail
SEED="${1:-20261104}"
N_THETA="${2:-8}"
N_CLAY="${3:-6}"
FREQ_HZ="${4:-1400000000}"
cd "$(dirname "$0")/.."
exec python3 -m multi_proxy.dielectric --seed "$SEED" --n-theta "$N_THETA" --n-clay "$N_CLAY" --freq-hz "$FREQ_HZ"
