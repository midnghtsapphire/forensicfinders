# Changelog

## 2026-11-20 — Git-Master
- Added `.gitleaks.toml` (`[extend] useDefault = true`) with a per-rule allowlist: rule `generic-api-key` x path `src/lib/auth/preview.ts` only. `preview.ts` is unchanged.
- Why: Secret confirmed the flagged value is the app-builder's stock shared preview client (no rotation needed). Requested by Sense-Strata.

## 2026-11-20 — Git-Master (false-positive triage, stacked on #68)
- Extended `.gitleaks.toml`: two more `generic-api-key` allowlists, each requiring exact path AND a line pattern: `sar/fixtures/case_view_synthetic_1001.json` (`case_token` = `CT-<12 hex>` placeholders, lines 8 and 30) and `sar/blue-ocean-sar/opendata/fetch.py` (line 382, function signature with a parameter named `secrets`).
- Why: judged false positives (synthetic fixture tokens; a variable name, no literal). Requested by Sense-Strata. No source files changed.
