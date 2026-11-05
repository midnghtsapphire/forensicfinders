# SenseCrew Bedrock / CleanScorer + synthetic DEM targets. Run from repo root.
.PHONY: test-scorer test-dem dem fixtures-all fixtures-verify

# Registry 2310 golden suite (math green; M1 W tests xfail PLACEHOLDER).
test-scorer:
	cd sar && python3 -m pytest -q -p no:warnings sensegame/tests/test_scorer_golden.py

# Registry 2320 DEM fixture goldens (SHA-256 exact).
test-dem:
	cd sar && python3 -m pytest -q -p no:warnings sensegame/tests/test_dem_fixture_golden.py

SEED ?= 1001
EPOCH ?=
dem:               ## make dem SEED=1001 | make dem SEED=1002 EPOCH=a
	cd sar && python3 -m sensegame.dem --seed $(SEED) $(if $(EPOCH),--epoch $(EPOCH)) --out fixtures/dem_synthetic_$(SEED)$(EPOCH).tif

fixtures-all:
	cd sar && python3 -m sensegame.dem --seed 1001 --out fixtures/dem_synthetic_1001.tif
	cd sar && python3 -m sensegame.dem --seed 1002 --epoch a --out fixtures/dem_synthetic_1002a.tif
	cd sar && python3 -m sensegame.dem --seed 1002 --epoch b --out fixtures/dem_synthetic_1002b.tif
	cd sar && python3 -m sensegame.dem --seed 1003 --out fixtures/dem_synthetic_1003.tif
	cd sar && python3 -m sensegame.dem --write-truth fixtures/dem_synthetic_1002_truth.json

fixtures-verify:
	cd sar && python3 -m sensegame.dem --verify fixtures/SHA256SUMS
