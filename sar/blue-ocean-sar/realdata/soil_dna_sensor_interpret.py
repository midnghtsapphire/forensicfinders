#!/usr/bin/env python3
"""soil_dna_sensor_interpret — SenseCrew / Humus alias for qpcr_interpret (GDD 3a).

Prefer this name in new code. qpcr_interpret is retained (delete nothing).
"""
from __future__ import annotations

from qpcr_interpret import *  # noqa: F401,F403
import qpcr_interpret as _impl

__all__ = [n for n in dir(_impl) if not n.startswith("_")]
