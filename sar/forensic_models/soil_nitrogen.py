"""Grave-soil nitrogen pathway (organic N -> NH4+ -> NO3-), forward Euler.
Structure from the notebook's ozark_grave_kinetic_model.py, but every rate now comes from constants.json:
Q10 temperature factor and the WFPS optimum are sourced; the ammonification and nitrification rates are
user_required (site specific) and must be supplied with a source. No pH feedback: the notebook's
pH = 5.2 + 0.05*NH4 rule had no source."""
from .constants import load, value


def wfps_factor(wfps, opt):
    if wfps <= opt:
        return wfps / opt
    return max(0.0, (1.0 - wfps) / (1.0 - opt))


def simulate(days, temp_c, wfps, n_org0, nh4_0=0.0, no3_0=0.0, leach_per_day=0.0, dt=0.1, consts=None, t_ref=20.0):
    c = consts or load()
    f_t = value(c, "q10_soil") ** ((temp_c - t_ref) / 10.0)
    k_am = value(c, "k_ammonification") * f_t
    k_ni = value(c, "k_nitrification") * f_t * wfps_factor(wfps, value(c, "wfps_nitrification_optimum"))
    steps = int(round(days / dt))
    n, a, o = float(n_org0), float(nh4_0), float(no3_0)
    rows = [(0.0, n, a, o)]
    for i in range(steps):
        dn, da, do = -k_am * n, k_am * n - k_ni * a, k_ni * a - leach_per_day * o
        n, a, o = n + dn * dt, a + da * dt, o + do * dt
        rows.append(((i + 1) * dt, n, a, o))
    return rows
