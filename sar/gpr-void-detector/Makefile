SEED ?= 42
.PHONY: sim test clean
sim:
	python3 -m gpr_void_detector \
		--bscan fixtures/synthetic_air_void_bscan.json \
		--soil-er 9 --dx 0.05 --dt 0.1 --seed $(SEED) \
		--out results_seed$(SEED).json --no-table
test:
	python3 -m unittest discover -p 'test_*.py' -v
clean:
	rm -f results_seed*.json
