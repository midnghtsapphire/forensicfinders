# ert-model (registry 510)

Analytic / semi-analytic **DC resistivity** forward model for training-game
ground detection: Wenner and dipole–dipole arrays over a 1-D layered
half-space or a buried resistive/conductive sphere (air void).

## Run

```bash
make sim SEED=42
make test
python3 -m ert_model --array wenner --a 2 --rho-layers 100 --profile 0 2 --seed 42 --out out.json
```

Synthetic fixtures only (`fixtures/*synthetic*`). No case/PII data.
No `forensic_pipeline` import. numpy (BSD-3) + stdlib only.

## Equations

- Ohm / steady current: ∇ · (σ ∇V) = 0 (Telford et al. 1990, ch. 8).
- Wenner: K = 2πa ; dipole–dipole: K = π n (n+1)(n+2) a.
- Two-layer Wenner image series (truncation N=80 documented in JSON constants).
- Buried sphere: conductivity contrast β = (σs−σh)/(σs+2σh); insulating
  (air) limit β → −1/2; leading induced dipole + free-surface image.

## Licence

Match repo. numpy BSD-3. Optional offline cross-check: pyGIMLi (Apache-2.0),
SimPEG (MIT) — not required at runtime. Ultralytics/AGPL forbidden. No gprMax link.
