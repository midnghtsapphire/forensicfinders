"""
multi_proxy: private forensic multi-scale proxy pipeline

Engines that take real arrays (or load them) and return ranked proxy footprints.
This is the next concrete step. Not a finished detector.
"""

from .engines import (
    calculate_twi,
    calculate_spectral_angle,
    nnls_unmix_with_rms,
    topp_dielectric,
    multiplicative_consensus,
)

__all__ = [
    "calculate_twi",
    "calculate_spectral_angle",
    "nnls_unmix_with_rms",
    "topp_dielectric",
    "multiplicative_consensus",
]
