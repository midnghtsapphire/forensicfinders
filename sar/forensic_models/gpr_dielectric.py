"""Dielectric mixing and GPR velocity, exactly as specified:
   eps_eff = (1-theta)*[eps_fat*(1-f_sap) + eps_soap*f_sap] + theta*eps_soil
   v = 0.3/sqrt(eps_eff)   (m/ns; 0.3 m/ns = c)
eps_soil defaults to Topp(1980) at the given theta; eps_soap and f_sap must be supplied."""
import math
from .constants import load, value
from .taphonomy import topp_eps


def eps_eff(theta, f_sap, eps_fat=None, eps_soap=None, eps_soil=None, consts=None):
    c = consts or load()
    if not (0 <= theta <= 1 and 0 <= f_sap <= 1):
        raise ValueError("theta and f_sap must be fractions 0..1")
    eps_fat = value(c, "eps_fat") if eps_fat is None else eps_fat
    eps_soap = value(c, "eps_soap") if eps_soap is None else eps_soap
    eps_soil = topp_eps(theta, c) if eps_soil is None else eps_soil
    return (1 - theta) * (eps_fat * (1 - f_sap) + eps_soap * f_sap) + theta * eps_soil


def gpr_velocity(eps):
    if eps <= 0:
        raise ValueError("permittivity must be > 0")
    return 0.3 / math.sqrt(eps)


def reflection_coefficient(eps1, eps2):
    """Normal-incidence amplitude reflection between media 1 -> 2 (low-loss)."""
    a, b = math.sqrt(eps1), math.sqrt(eps2)
    return (a - b) / (a + b)


def depth_from_twt(twt_ns, eps):
    return gpr_velocity(eps) * twt_ns / 2.0
