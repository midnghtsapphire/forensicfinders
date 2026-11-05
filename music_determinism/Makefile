SEED ?= 1001
DUR ?= 12
VENV := $(CURDIR)/.venv
.PHONY: music-determinism venv
venv:
	test -d $(VENV) || (python3.12 -m venv $(VENV) && git clone https://github.com/ace-step/ACE-Step-1.5 $(VENV)/src && cd $(VENV)/src && git checkout ca1e85fe9430179831e6bc6be790c332190a3866 && $(VENV)/bin/pip install -e . soundfile huggingface_hub)
music-determinism:
	@python3 run_determinism.py --seed $(SEED) --duration $(DUR) --out out/preflight || { rc=$$?; [ $$rc -eq 3 ] && echo "BLOCKED (see out/preflight/result.json)"; exit $$rc; }
	$(MAKE) venv && $(VENV)/bin/python run_determinism.py --seed $(SEED) --duration $(DUR)
