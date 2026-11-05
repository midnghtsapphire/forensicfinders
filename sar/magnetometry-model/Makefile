SEED ?= 42
.PHONY: sim test clean
sim:
	python3 -m magnetometry_model --kind sphere --depth 5 --radius 1 --kappa 0.1 \
		--B0 50000 --inc 65 --dec 10 --profile=-20:20:0.5 --seed $(SEED) \
		--out results_seed$(SEED).json --no-table
test:
	python3 -m unittest discover -p 'test_*.py' -v
clean:
	rm -f results_seed*.json
