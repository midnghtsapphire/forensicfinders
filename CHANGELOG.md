# Changelog

## 2026-11-20 — Git-Master
- Added `.gitleaks.toml` (`[extend] useDefault = true`) with a per-rule allowlist: rule `generic-api-key` x path `src/lib/auth/preview.ts` only. `preview.ts` is unchanged.
- Why: Secret confirmed the flagged value is the app-builder's stock shared preview client (no rotation needed). Requested by Sense-Strata.

## 2026-11-20 — Git-Master (false-positive triage, stacked on #68)
- Extended `.gitleaks.toml`: two more `generic-api-key` allowlists, each requiring exact path AND a line pattern: `sar/fixtures/case_view_synthetic_1001.json` (`case_token` = `CT-<12 hex>` placeholders, lines 8 and 30) and `sar/blue-ocean-sar/opendata/fetch.py` (line 382, function signature with a parameter named `secrets`).
- Why: judged false positives (synthetic fixture tokens; a variable name, no literal). Requested by Sense-Strata. No source files changed.

## 2026-11-20 — Git-Master (caveat on #69 allowlist, per Secret)
- Recorded Secret's caveat: if `sar/fixtures/case_view_synthetic_1001.json` is ever confirmed as real data, its `.gitleaks.toml` allowlist entry (the `case_token` block) must be removed. Secret agreed with the #69 false-positive verdicts. Requested by Sense-Strata. Docs only.

## 2026-11-21 — Git-Master
- Merged `daily/2026-11-20` into `git-master/gitleaks-allowlist-preview-ts` (merge commit, no rebase, no force-push) after #69's squash landed #68's allowlist plus the stacked #69 allowlists and Secret's caveat. LEDGER/CHANGELOG kept append-only (base already contained our entries; no entries removed or duplicated). `preview.ts` untouched.
