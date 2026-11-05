# Humus SenseCrew — dielectric Topp/Mironov manual runner
# Usage (Humus hard rule 4): make sim SEED=20261104
# Or:    cd sar/blue-ocean-sar && python3 -m multi_proxy.dielectric --seed 20261104
# Or:    ./run_sim_dielectric.sh 20261104

SEED ?= 20261104
N_THETA ?= 8
N_CLAY ?= 6
FREQ_HZ ?= 1400000000

.PHONY: sim sim-dielectric test-dielectric

# Canonical manual entry (SenseCrew rule 4 / Humus follow-up 0)
sim: sim-dielectric

sim-dielectric:
	cd .. && python3 -m multi_proxy.dielectric --seed $(SEED) --n-theta $(N_THETA) --n-clay $(N_CLAY) --freq-hz $(FREQ_HZ)

test-dielectric:
	cd .. && python3 -m unittest multi_proxy.test_dielectric_topp_mironov -v
