"""Decomposition timing (Megyesi ADD, Vass PMI) and soil moisture/permittivity (Topp), all from constants.json."""
import math
from .constants import load, value


def topp_theta(eps, consts=None):
    a = value(consts or load(), "topp_forward")
    return a["a0"] + a["a1"] * eps + a["a2"] * eps ** 2 + a["a3"] * eps ** 3


def topp_eps(theta, consts=None):
    b = value(consts or load(), "topp_inverse")
    if not 0 <= theta <= 0.6:
        raise ValueError("Topp (1980) was fitted for volumetric water content of about 0 to 0.55")
    return b["b0"] + b["b1"] * theta + b["b2"] * theta ** 2 + b["b3"] * theta ** 3


def megyesi_add(tbs, consts=None):
    """Accumulated degree days from Total Body Score (3-35). Returns (add, low, high)."""
    if not 3 <= tbs <= 35:
        raise ValueError("TBS range is 3-35")
    m = value(consts or load(), "megyesi_add")
    add = 10 ** (m["a"] * tbs * tbs + m["b"])
    return add, max(0.0, add - m["se_add"]), add + m["se_add"]


def accumulated_degree_days(daily_mean_c, base_c=0.0):
    return sum(max(0.0, t - base_c) for t in daily_mean_c)


def vass_pmi(decomposition_pct, temp_c, humidity_pct, buried=False, consts=None):
    c = consts or load()
    v = value(c, "vass_aerobic")
    if temp_c <= 0 or humidity_pct <= 0:
        raise ValueError("Vass formula needs temperature > 0 degC and humidity > 0 %")
    pmi = v["k"] * (decomposition_pct / 100.0) / (v["c"] * temp_c * humidity_pct)
    return pmi * value(c, "vass_anaerobic_factor") if buried else pmi


def saponified_fraction(years, consts=None):
    """1 - exp(-k*t). k is user_required (no universal published rate)."""
    k = value(consts or load(), "k_saponification")
    return 1.0 - math.exp(-k * years)
