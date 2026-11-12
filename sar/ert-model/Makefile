SEED ?= 42
.PHONY: sim test clean
sim:
	python3 -m ert_model --array wenner --a 2 --rho-layers 100 500 --thickness 5 \
		--profile 0 2 4 6 8 --seed $(SEED) --out results_seed$(SEED).json --no-table
test:
	python3 -m unittest discover -p 'test_*.py' -v
clean:
	rm -f results_seed*.json
