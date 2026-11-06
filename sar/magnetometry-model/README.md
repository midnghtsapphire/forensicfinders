# magnetometry-model (registry 520)

Analytic **total-field magnetic anomaly** forward model: buried dipole /
induced sphere and thin dyke, with seeded noise.

## Run

```bash
make sim SEED=42
make test
python3 -m magnetometry_model --kind sphere --depth 5 --radius 1 --kappa 0.1 \
  --B0 50000 --inc 65 --dec 10 --profile -20:20:0.5 --seed 42 --out mag.json
```

## Equations (Blakely 1995)

- Dipole: B = (μ0/4π)[3(m·r̂)r̂ − m]/r³
- Sphere: m = (4π R³/μ0)(κ/(3+κ)) B0  (N=1/3 demagnetization)
- ΔT ≈ B̂0 · Banom
- Thin dyke: 2-D infinite-strike form; vertical dyke + vertical M → even ΔT

**Spec correction:** axial dipole m=1 A·m² at z=10 m gives Bz = 0.2 nT
(= 2×10⁻¹⁰ T), not 2.0 nT as typed in specs v0.

Synthetic fixtures only. No forensic_pipeline. numpy BSD-3 + stdlib.
