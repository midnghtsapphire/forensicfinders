# PYTHONPATH: package dir + sar/ (parent of forensic_models) for live 1010 import
SAR := $(abspath $(CURDIR)/..)
export PYTHONPATH := $(CURDIR):$(SAR)$(if $(PYTHONPATH),:$(PYTHONPATH),)

test:
	python3 -m unittest discover -p "test_*.py"
run:
	python3 -m insect_trace_add_sim --seed 7
