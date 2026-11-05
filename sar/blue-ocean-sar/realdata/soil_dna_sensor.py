#!/usr/bin/env python3
"""soil_dna_sensor — SenseCrew / Humus canonical name for the Tier-3 qPCR node (GDD 3a).

This module is a thin alias of qpcr_assay. Prefer importing soil_dna_sensor in new
code. The qpcr_assay module is kept (Humus hard rule: delete nothing); treat it as
the implementation detail behind this name.

Rule 7: synthetic curves / lab exports only; no case/, hfmr/, dossier, evidence/,
or public_records imports.
"""
from __future__ import annotations

# Re-export the assay API under the soil_dna_sensor name.
from qpcr_assay import *  # noqa: F401,F403
import qpcr_assay as _impl

__all__ = [n for n in dir(_impl) if not n.startswith("_")]
