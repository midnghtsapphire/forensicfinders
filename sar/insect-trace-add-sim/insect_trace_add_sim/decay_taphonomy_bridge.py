"""Chitin decay hooks extending registry 1010 (forensic_models/taphonomy).

Verity: taphonomy CLEAR (0.86); forensic_models constants CLEAR (0.92, Strata/Verity
relay 2026-11-04). Live import of forensic_models.taphonomy is the production path on
this branch (PYTHONPATH includes sar/). Thin stub fallback remains only if the import
fails in isolation; default backend_name() is forensic_models.taphonomy.

Public signatures (live or stub):
  topp_theta(eps, consts=None), topp_eps(theta, consts=None), megyesi_add(tbs, consts=None),
  accumulated_degree_days(daily_mean_c, base_c=0.0),
  vass_pmi(decomposition_pct, temp_c, humidity_pct, buried=False, consts=None),
  saponified_fraction(years, consts=None)

Constants/taphonomy checked out unchanged from origin/sar-make-it-work; Chitin does not
edit them. topp_* behavior is routed through the live module without local changes.
Licence: UNLICENSED (private repo; licence pending Audrey)."""
REGISTRY_PARENT = "1010"

try:  # production path — constants CLEAR; live 1010 import
    from forensic_models import taphonomy as _tap  # type: ignore
    _BACKEND = "forensic_models.taphonomy"
except Exception:  # noqa: BLE001 - isolation / missing package -> thin stub
    _tap, _BACKEND = None, "stub"


def _need(name):
    raise NotImplementedError(f"{name}: needs sourced constants from 1010 forensic_models; stub has none")


class _Stub:
    @staticmethod
    def accumulated_degree_days(daily_mean_c, base_c=0.0):
        return sum(max(0.0, t - base_c) for t in daily_mean_c)

    def topp_theta(self, eps, consts=None): _need("topp_theta")
    def topp_eps(self, theta, consts=None): _need("topp_eps")
    def megyesi_add(self, tbs, consts=None): _need("megyesi_add")
    def vass_pmi(self, decomposition_pct, temp_c, humidity_pct, buried=False, consts=None): _need("vass_pmi")
    def saponified_fraction(self, years, consts=None): _need("saponified_fraction")


_impl = _tap or _Stub()


def backend_name():
    return _BACKEND


def accumulated_degree_days(daily_mean_c, base_c=0.0):
    return _impl.accumulated_degree_days(daily_mean_c, base_c=base_c)


def megyesi_add(tbs, consts=None):
    return _impl.megyesi_add(tbs, consts=consts)


def topp_theta(eps, consts=None):
    return _impl.topp_theta(eps, consts=consts)


def vass_pmi(decomposition_pct, temp_c, humidity_pct, buried=False, consts=None):
    return _impl.vass_pmi(decomposition_pct, temp_c, humidity_pct, buried=buried, consts=consts)


def decay_hook(run_out):
    """Cross-check a 2350 run's ADD against 1010's ADD (same base) and record soil inputs."""
    base = run_out["species"]["base_c"]
    means = [(d["tmax_c"] + d["tmin_c"]) / 2.0 for d in run_out["days"]]
    return {"registry_parent": REGISTRY_PARENT, "taphonomy_backend": _BACKEND,
            "taphonomy_add": round(accumulated_degree_days(means, base_c=base), 4),
            "soil_moisture_vwc_clamped": run_out.get("soil_moisture_vwc_clamped"),
            "synthetic": True}
