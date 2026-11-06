"""CleanScorer — registry 2310 (NEW-01), clean-room Koopman/Stone search core.

Derived only from published theory (Koopman 1956/57; Charnes & Cooper 1958; Stone 1975).
No quarantined module was opened. Spec: docs/sensecrew/bedrock/specs/scorer-spec.md.

Two paths, kept apart (Decision B; spec section 4b):
- Cited effective sweep width: ``pod`` / ``pos`` / ``optimal`` / ``update``.
  ``w_km is None`` raises ``UncitedSweepWidth``. A geometric swath is not an
  effective width and is never substituted, including any fraction of one.
- Coverage and budget only, plus ``exponential_coverage_model`` on a
  player-supplied dimensionless C. That model is not calibrated detection
  and is not M1 detection scoring. M1 effective W stays null.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

_POA_SUM_TOL = 1e-9
_POSTERIOR_DEN_MIN = 1e-15


class ScorerError(ValueError):
    """Invalid scorer input or undefined posterior."""


class UncitedSweepWidth(ScorerError):
    """Non-ROW segment has w_km is None on the detection path (pos/optimal/update).

    Coverage, budget, and the exponential coverage model do not raise this
    and do not invent a width.
    """


@dataclass(frozen=True)
class Segment:
    name: str
    area_km2: float
    poa: float
    w_km: float | None  # None = uncited -> unscorable
    speed_kmh: float | None = None
    is_row: bool = False


def _finite_nonneg(x: float, label: str) -> None:
    if not isinstance(x, (int, float)) or isinstance(x, bool):
        raise ScorerError(f"{label} must be a real number")
    if not math.isfinite(x) or x < 0.0:
        raise ScorerError(f"{label} must be finite and >= 0, got {x!r}")


def _finite_pos(x: float, label: str) -> None:
    if not isinstance(x, (int, float)) or isinstance(x, bool):
        raise ScorerError(f"{label} must be a real number")
    if not math.isfinite(x) or x <= 0.0:
        raise ScorerError(f"{label} must be finite and > 0, got {x!r}")


class CleanScorer:
    """Stateless, pure, deterministic search scorer.

    Detection (``pod``, ``pos``, ``optimal``, ``update``) needs a cited effective
    sweep width. Geometric coverage and track budget do not. The exponential
    coverage model takes a player-supplied C and is not calibrated detection.
    """

    def pod(self, w_km: float, track_km: float, area_km2: float) -> float:
        """Detection POD for a cited effective sweep width: ``1 - exp(-W·z/A)``.

        ``w_km`` must already be an effective detection sweep width (∫ p(x) dx).
        This method does not accept a geometric swath and does not invent one.
        Implemented as ``-math.expm1(-W·z/A)``.
        """
        _finite_nonneg(w_km, "w_km")
        _finite_nonneg(track_km, "track_km")
        _finite_pos(area_km2, "area_km2")
        if w_km == 0.0 or track_km == 0.0:
            return 0.0
        return -math.expm1(-w_km * track_km / area_km2)

    def exponential_coverage_model(self, coverage: float) -> float:
        """MODEL, not calibrated detection.

        Player-supplied dimensionless coverage C maps to ``1 - exp(-C)``,
        implemented as ``-math.expm1(-C)``. GDD v0.4 section 4 / 4a fallback
        when no cited effective sweep width exists. Proofy: this is a model.

        The result is not a probability of detection, not a probability of
        success, and not a negative-evidence update. This method does not read,
        require, or invent W. Do not pass a geometric swath, or any fraction of
        one, and do not use the result as M1 detection POD/POS.
        """
        _finite_nonneg(coverage, "coverage")
        if coverage == 0.0:
            return 0.0
        return -math.expm1(-coverage)

    def geometric_survey_km2(self, geometric_swath_km: float, track_km: float) -> float:
        """Area the sensor footprint passed over: ``geometric_swath_km * track_km``.

        Surveyed is not detected. ``geometric_swath_km`` is an instrument
        footprint in kilometres. It is never an effective sweep width. This
        method does not write it into ``w_km`` and does not call ``pod``,
        ``pos``, ``optimal``, ``update``, or ``exponential_coverage_model``.
        """
        _finite_nonneg(geometric_swath_km, "geometric_swath_km")
        _finite_nonneg(track_km, "track_km")
        return geometric_swath_km * track_km

    def geometric_coverage(
        self, geometric_swath_km: float, track_km: float, area_km2: float
    ) -> float:
        """Dimensionless geometric coverage ``(swath_km * track_km) / area_km2``.

        May exceed 1 when the track is long relative to the segment. This is
        not detection coverage from an effective sweep width. Surveyed is not
        detected. Do not feed this value to ``exponential_coverage_model`` or
        ``pod`` as if the geometric swath were W.
        """
        _finite_nonneg(geometric_swath_km, "geometric_swath_km")
        _finite_nonneg(track_km, "track_km")
        _finite_pos(area_km2, "area_km2")
        if geometric_swath_km == 0.0 or track_km == 0.0:
            return 0.0
        return geometric_swath_km * track_km / area_km2

    def track_budget_spent_km(self, effort_km: dict[str, float]) -> float:
        """Sum of allocated track kilometres. Budget accounting only.

        Does not score detection and does not read sweep width.
        """
        parts: list[float] = []
        for key, track_km in effort_km.items():
            _finite_nonneg(track_km, f"effort_km[{key}]")
            parts.append(float(track_km))
        return math.fsum(parts)

    def pos(self, segments: list[Segment], effort_km: dict[str, float]) -> float:
        segs = self._validate_segments(segments, require_w=True)
        effort = self._validate_effort(segs, effort_km)
        return self._pos_from_validated(segs, effort)

    def optimal(self, segments: list[Segment], budget_km: float) -> dict[str, float]:
        _finite_nonneg(budget_km, "budget_km")
        segs = self._validate_segments(segments, require_w=True)
        plan = {g.name: 0.0 for g in segs}
        if budget_km == 0.0:
            return dict(sorted(plan.items()))

        # Searchable: non-ROW with p>0 and r=W/A>0. Sort by p*r desc, tie-break name.
        cand: list[tuple[float, str, float, float]] = []  # (pr, name, p, r)
        for g in segs:
            if g.is_row:
                continue
            assert g.w_km is not None
            r = g.w_km / g.area_km2
            if g.poa == 0.0 or r == 0.0:
                continue
            cand.append((g.poa * r, g.name, g.poa, r))
        cand.sort(key=lambda t: (-t[0], t[1]))
        if not cand:
            # All unsearchable → all-zero; budget unspent (v0.2 metadata flag; see note).
            return dict(sorted(plan.items()))

        n = len(cand)
        best_k = 0
        best_ln_lam = 0.0
        for k in range(1, n + 1):
            S = cand[:k]
            sum_ln_over_r = math.fsum(math.log(pr) / r for pr, _name, _p, r in S)
            sum_inv_r = math.fsum(1.0 / r for _pr, _name, _p, r in S)
            ln_lam = (sum_ln_over_r - budget_km) / sum_inv_r
            lam = math.exp(ln_lam)
            pr_k = S[-1][0]
            if pr_k > lam:
                best_k = k
                best_ln_lam = ln_lam

        if best_k == 0:
            return dict(sorted(plan.items()))

        for pr, name, _p, r in cand[:best_k]:
            z = (math.log(pr) - best_ln_lam) / r
            plan[name] = z if z > 0.0 else 0.0

        return dict(sorted(plan.items()))

    def update(self, segments: list[Segment], effort_km: dict[str, float]) -> list[Segment]:
        segs = self._validate_segments(segments, require_w=True)
        effort = self._validate_effort(segs, effort_km)
        pos = self._pos_from_validated(segs, effort)
        den = 1.0 - pos
        if den < _POSTERIOR_DEN_MIN:
            raise ScorerError("posterior undefined: 1 - POS too small")
        out: list[Segment] = []
        for g in segs:  # already name-sorted
            if g.is_row:
                new_poa = g.poa / den
            else:
                assert g.w_km is not None
                z = effort.get(g.name, 0.0)
                pod_i = self.pod(g.w_km, z, g.area_km2)
                new_poa = g.poa * (1.0 - pod_i) / den
            out.append(
                Segment(
                    name=g.name,
                    area_km2=g.area_km2,
                    poa=new_poa,
                    w_km=g.w_km,
                    speed_kmh=g.speed_kmh,
                    is_row=g.is_row,
                )
            )
        return out

    def _pos_from_validated(
        self, segs: list[Segment], effort: dict[str, float]
    ) -> float:
        parts: list[float] = []
        for g in segs:
            if g.is_row:
                continue
            assert g.w_km is not None
            z = effort.get(g.name, 0.0)
            parts.append(g.poa * self.pod(g.w_km, z, g.area_km2))
        return math.fsum(parts)

    def _validate_segments(
        self, segments: Iterable[Segment], *, require_w: bool
    ) -> list[Segment]:
        segs = list(segments)
        names = [g.name for g in segs]
        if len(names) != len(set(names)):
            raise ScorerError("duplicate segment names")
        rows = [g for g in segs if g.is_row]
        if len(rows) > 1:
            raise ScorerError("more than one ROW segment")
        poa_sum = math.fsum(g.poa for g in segs)
        if abs(poa_sum - 1.0) > _POA_SUM_TOL:
            raise ScorerError(f"POA must sum to 1 within {_POA_SUM_TOL}, got {poa_sum!r}")
        for g in segs:
            if not math.isfinite(g.poa) or g.poa < 0.0:
                raise ScorerError(f"POA must be finite and >= 0 for {g.name!r}")
            if g.is_row:
                continue
            if not math.isfinite(g.area_km2) or g.area_km2 <= 0.0:
                raise ScorerError(f"area_km2 must be > 0 for non-ROW {g.name!r}")
            if require_w:
                if g.w_km is None:
                    raise UncitedSweepWidth(
                        f"uncited sweep width for scorable segment {g.name!r}"
                    )
                _finite_nonneg(g.w_km, f"w_km[{g.name}]")
        return sorted(segs, key=lambda g: g.name)

    def _validate_effort(
        self, segs: list[Segment], effort_km: dict[str, float]
    ) -> dict[str, float]:
        known = {g.name for g in segs}
        row_names = {g.name for g in segs if g.is_row}
        out: dict[str, float] = {}
        for k, z in effort_km.items():
            if k not in known:
                raise ScorerError(f"unknown segment key {k!r}")
            _finite_nonneg(z, f"effort_km[{k}]")
            if k in row_names and z > 0.0:
                raise ScorerError("ROW gets no effort")
            out[k] = float(z)
        return out
