# Humus rule-7 read-only audit — qpcr / lab_readers / eDNA naming

**Pair:** Humus-D · **Date:** 2026-11-04 (America/Denver) · **Branch:** sensecrew/humus/soil-dna-rename  
**Scope:** `qpcr_*`, `lab_readers.py`, and any eDNA/EDNA-named code in forensicfinders.  
**Method:** path listing via git tree; content `rg` on the listed files only. Did **not** open `case/`, `hfmr/`, `evidence/`, or `public_records/`.

## Files audited

| File | EDNA / eDNA naming | Forbidden imports (`case/`, `hfmr/`, `dossier.py`, `evidence/`, `public_records`) | PII |
|---|---|---|---|
| `sar/blue-ocean-sar/realdata/qpcr_assay.py` | Journal citation only: “Klymus et al. 2020, *Environmental DNA* 2:271-282” (not a code identifier). No `eDNA` / `EDNA` symbol. | None (stdlib + `qpcr_interpret`) | None found |
| `sar/blue-ocean-sar/realdata/qpcr_interpret.py` | None. Domain text is “human-mtDNA assay” (lab call), not eDNA naming. | None (stdlib only) | None found |
| `sar/blue-ocean-sar/realdata/lab_readers.py` | None | **No imports.** Docstring lineage note: “Replaces … `docs/case-files` …” — flagged as **lineage mention**, not an import. Path was not opened. | None found |
| `sar/blue-ocean-sar/realdata/test_qpcr_assay.py` | None | None (`qpcr_assay` + stdlib) | None found |
| `sar/blue-ocean-sar/realdata/test_lab_readers.py` | None | None (`lab_readers` + stdlib/numpy) | None found |
| `sar/docs/SOIL_SENSING_TIERS.md` | Had `qPCR/eDNA` and `eDNA preservation` (docs) | n/a (markdown) | n/a |
| `sar/docs/DECODE_INJECTION_DESIGN.md` | Had `eDNA decay clock` (docs) | n/a | n/a |

## Repo-wide filename search

No path containing `edna` / `eDNA` / `EDNA` in the tree (git recursive tree of `main`).

## Rename actions on this branch (delete nothing)

1. Docs: `eDNA` → `soil_dna_sensor` in `SOIL_SENSING_TIERS.md` and `DECODE_INJECTION_DESIGN.md`.
2. New shims (additive): `soil_dna_sensor.py` → re-exports `qpcr_assay`; `soil_dna_sensor_interpret.py` → re-exports `qpcr_interpret`.
3. Journal title “*Environmental DNA*” in the Klymus citation left unchanged (bibliographic, not a SenseCrew symbol).

## Verdict

Rule-7 **PASS** for imports/PII on the audited Python files. Lineage string in `lab_readers.py` docstring noted for Verity; no quarantine import present. eDNA **code/docs identifiers** renamed or shimmed to `soil_dna_sensor`.
