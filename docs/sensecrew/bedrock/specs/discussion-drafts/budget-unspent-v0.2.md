# Scorer v0.2 draft note — `budget_unspent` flag (2026-11-05)

Owner: Bedrock. Status: **follow-up draft**, not a contract change for 2310 v0.1.

## Gap
`CleanScorer.optimal` (scorer-spec §3–§4) returns an all-zero plan when every segment is
unsearchable (ROW-only, `p_i = 0`, or `r_i = W/A = 0`). The numeric budget `B` is then
**unspent**. v0.1 returns only `dict[str, float]` effort; callers cannot tell "B = 0" from
"B > 0 but nothing searchable" without re-deriving eligibility.

## v0.2 proposal
Extend the optimal result (or add a parallel metadata channel) with:

```text
budget_unspent: bool   # True iff budget_km > 0 and Σ z_i == 0 because no searchable segment
budget_km: float       # echoed input
spent_km: float        # math.fsum(z.values())
```

No change to POD/POS/update math, water-filling, or tolerances. Fusion / Ledger-Play can
branch on the flag for debrief copy without inventing physics. Default remains the bare
effort dict until Ledger-Play and Loam accept the shape.

## Out of scope here
Hours mode (`z_km = z_h * speed_kmh`), return-type packaging (dataclass vs tuple), and any
cited M1 `W` (still PLACEHOLDER).
