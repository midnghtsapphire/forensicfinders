# Changelog

## 2026-11-20 — Git-Master
- Added `.gitleaks.toml` (`[extend] useDefault = true`) with a per-rule allowlist: rule `generic-api-key` x path `src/lib/auth/preview.ts` only. `preview.ts` is unchanged.
- Why: Secret confirmed the flagged value is the app-builder's stock shared preview client (no rotation needed). Requested by Sense-Strata.
