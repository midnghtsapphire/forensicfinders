# WR #61 seeded-output evidence (seeds 1002 and 1003)

Produced 2026-11-12 in a scratch copy. `out/` is not committed. Canonical revisions are on `main`:

- before (clamp present): `6176bc18` — merge of PR #58
- after (raw percentiles): `8bcce8ed` — merge of PR #59 (closes #52; same change as #56 on `daily/2026-11-06`)

Environment (chosen to match CircleCI `python:3.12-bookworm` language version and the #53 pins):

- CPython 3.12.16
- `OMP_NUM_THREADS=1` `PYTHONHASHSEED=0`
- `numpy==2.2.6` `scikit-learn==1.6.1` `pyod==3.6.7` `rasterio==1.4.3` `scipy==1.18.1` `pytest==9.2.0`
- Command, from `sar/`: `python -m sensegame.fusion --seed <seed> --config sensegame/fusion/fixtures/fusion_config_synthetic.json --out <scratch>`

`daily/2026-11-12` did not exist on origin when this was written. `main` (the #59 merge) is the canonical tree for this evidence. #56 landed the same writer change on `daily/2026-11-06` at `4d45f400`; the 1002/1003 fixtures and the writer math are the same, so the no-op is inferred for that branch. It was not re-run at `4d45f400` (unverified by a local or CI build on that revision).

## Out-of-band counts

A cell is out-of-band when `p_anomaly_calibrated` falls outside the **raw** 2.5/97.5 bootstrap percentile band, recomputed with `SeedSequence([seed, i])` for `i` in `0..999`. The grid is 20×20 = 400 cells.

| seed | cells | raw-band out-of-band (before `6176bc18`) | raw-band out-of-band (after `8bcce8ed`) | published-band out-of-band before (clamped) | published-band out-of-band after (raw) |
|---|---|---|---|---|---|
| 1002 | 400 | 0 | 0 | 0 | 0 |
| 1003 | 400 | 0 | 0 | 0 | 0 |

The CHANGELOG claim that seed 1002 is a no-op for the old widening is confirmed. Seed 1003 is also a no-op: no cell has `p` outside the raw band, so the published `ci_low`/`ci_high` (and therefore the output bytes) do not change.

## Before/after SHA-256 (author-local, env-specific; not produced by CircleCI)

These hashes were computed by the author in a scratch copy on CPython 3.12.16 with the pins and flags listed above. CircleCI at the #63 head ran the test suite only (`sar/registry.py --test-all`); it did not compute or store these file hashes, and it did not compare builds at `6176bc18` and `8bcce8ed`. Treat the table as an author-reported local run, not a CI artifact.


| file | SHA-256 at `6176bc18` (before, clamp) | SHA-256 at `8bcce8ed` (after, raw) | identical? |
|---|---|---|---|
| `fusion_1002.json` | `3b987b05ae2e5c748ad2d7a20a2c5bea99927de229c4a2982b6e94d9600dbfe4` | `3b987b05ae2e5c748ad2d7a20a2c5bea99927de229c4a2982b6e94d9600dbfe4` | yes |
| `uncertainty_map_1002.tif` | `09baac2b2a82a44c14db10c4ccf1da7f9e0bdd5702afaa03b48b6425c3eb411a` | `09baac2b2a82a44c14db10c4ccf1da7f9e0bdd5702afaa03b48b6425c3eb411a` | yes |
| `fusion_1003.json` | `3e4611727c76da64ff6b4b022da41da47abb3cae9366ca167410829c63f87089` | `3e4611727c76da64ff6b4b022da41da47abb3cae9366ca167410829c63f87089` | yes |
| `uncertainty_map_1003.tif` | `4e6f1199f896e30b0128dc7223d0d458097259f48eb913c4a08a51a155a2a040` | `4e6f1199f896e30b0128dc7223d0d458097259f48eb913c4a08a51a155a2a040` | yes |

Because both official seeds have zero out-of-band cells, a reintroduced clamp would not change these hashes. The regression that fails when the clamp is restored is `test_score_scene_does_not_widen_band_to_contain_p` (stub model from #61), not the seed-1002/1003 fixture tests.
