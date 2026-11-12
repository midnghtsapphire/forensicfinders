# SenseCrew Bedrock / CleanScorer + synthetic DEM targets. Run from repo root.
.PHONY: test-scorer test-dem dem fixtures-all fixtures-verify

# Registry 2310 golden suite (math green; M1 W tests xfail PLACEHOLDER).
# Registry 2310 golden suite (math green; M1 scores coverage and budget only; M1_W_KM is None until a cited W exists).
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

# SenseCrew Fusion (registry 2371, provisional). Synthetic fixtures only.
# FUSION_SEED defaults to 1002 (Bedrock's SEED default is 1001 for dem); `make fusion SEED=N` still works.
.PHONY: fusion fusion-replay fusion-test
FUSION_SEED ?= $(if $(filter command line environment,$(origin SEED)),$(SEED),1002)
CONFIG ?= sensegame/fusion/fixtures/fusion_config_synthetic.json
PY ?= python3
FUSION_ENV = OMP_NUM_THREADS=1 PYTHONHASHSEED=0

fusion:
	cd sar && $(FUSION_ENV) $(PY) -m sensegame.fusion --seed $(FUSION_SEED) --config $(CONFIG) --out ../out/fusion/$(FUSION_SEED)/

fusion-replay:
	cd sar && $(FUSION_ENV) $(PY) -m sensegame.fusion --replay --seed $(FUSION_SEED) --config $(CONFIG) --out ../out/fusion/$(FUSION_SEED)/

fusion-test:
	cd sar && $(FUSION_ENV) $(PY) -m pytest -q -p no:warnings sensegame/fusion/tests
