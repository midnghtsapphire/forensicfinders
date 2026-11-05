"""Scorer surface Fusion / Ledger-Play expect (protocol consumer side).

Re-exports Bedrock CleanScorer (2310) as the default Scorer. QuarantinedRepoScorer is
disabled; no import of search_theory / optimal_search / sweep_width.
"""
from __future__ import annotations

from sensegame.search_core import (
    CleanScorer,
    ScorerError,
    Segment,
    UncitedSweepWidth,
)

Scorer = CleanScorer  # default drop-in for the Ledger-Play Scorer Protocol

__all__ = [
    "CleanScorer",
    "Scorer",
    "ScorerError",
    "Segment",
    "UncitedSweepWidth",
]
