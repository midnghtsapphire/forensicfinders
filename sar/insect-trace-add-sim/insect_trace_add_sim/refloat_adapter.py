"""Thin adapter reusing ADD helpers from sar/blue-ocean-sar/realdata/refloat_timing.py
(Verity R7: CLEAR to reuse ADD). Imports ONLY refloat_timing via sys.path; never evidence/dossier/
search_theory or any quarantine module. Callers MUST surface LABEL: the river-refloat primary model
rests on a preprint, not peer-reviewed. Licence: UNLICENSED (private repo; licence pending Audrey)."""
import importlib, os, sys
_REALDATA = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "blue-ocean-sar", "realdata"))


def _load():
    if _REALDATA not in sys.path:
        sys.path.insert(0, _REALDATA)
    return importlib.import_module("refloat_timing")


_rt = _load()
LABEL = _rt.LABEL  # "preprint, not peer-reviewed"
SOURCE = "sar/blue-ocean-sar/realdata/refloat_timing.py (daily_contribution, accumulate)"


def daily_contribution(mean_c, base_c):
    return _rt.daily_contribution(mean_c, base_temp_c=base_c)


def accumulate(mean_temps, base_c):
    return _rt.accumulate(mean_temps, base_temp_c=base_c)


def metadata():
    return {"name": "refloat_timing", "source": SOURCE, "label": LABEL,
            "label_note": "River-refloat primary model (Delhez et al. EGUsphere egusphere-2026-5071) is a "
                          "preprint, not peer-reviewed; only its generic ADD arithmetic is reused here.",
            "species_thresholds": "synthetic (fixtures/species_synthetic.json), not from refloat_timing"}
