# SenseCrew Bedrock / CleanScorer targets. Run from repo root.
.PHONY: test-scorer

# Registry 2310 golden suite (math green; M1 W tests xfail PLACEHOLDER).
test-scorer:
	cd sar && python3 -m pytest -q -p no:warnings sensegame/tests

# SenseCrew Fusion (registry 2371, provisional). Synthetic fixtures only.
.PHONY: fusion fusion-replay fusion-test
SEED ?= 1002
CONFIG ?= sensegame/fusion/fixtures/fusion_config_synthetic.json
PY ?= python3
FUSION_ENV = OMP_NUM_THREADS=1 PYTHONHASHSEED=0

fusion:
	cd sar && $(FUSION_ENV) $(PY) -m sensegame.fusion --seed $(SEED) --config $(CONFIG) --out ../out/fusion/$(SEED)/

fusion-replay:
	cd sar && $(FUSION_ENV) $(PY) -m sensegame.fusion --replay --seed $(SEED) --config $(CONFIG) --out ../out/fusion/$(SEED)/

fusion-test:
	cd sar && $(FUSION_ENV) $(PY) -m pytest -q -p no:warnings sensegame/fusion/tests
