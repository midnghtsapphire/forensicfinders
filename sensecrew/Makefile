# SenseCrew golden target. Run from repo root: make -f sensecrew/Makefile sensecrew-test
# Gate is --strict by default once a 2300-block component exists (auto-detected by the gate).
ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
.PHONY: sensecrew-test sensecrew-suites sensecrew-gate
sensecrew-test: sensecrew-suites sensecrew-gate
sensecrew-suites:
	cd $(ROOT) && python3 sensecrew/run_golden.py
sensecrew-gate:
	cd $(ROOT) && python3 -m unittest sensecrew/test_forbidden_imports_gate.py && python3 sensecrew/forbidden_imports_gate.py
