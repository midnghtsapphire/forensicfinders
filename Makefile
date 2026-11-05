# SenseCrew Bedrock / CleanScorer targets. Run from repo root.
.PHONY: test-scorer

# Registry 2310 golden suite (math green; M1 W tests xfail PLACEHOLDER).
test-scorer:
	cd sar && python3 -m pytest -q -p no:warnings sensegame/tests
