# gpr-void-detector (registry 530)

Deterministic detector of air- or water-filled voids in **synthetic B-scans**
from / compatible with `gpr-wave-model`. Hyperbola fit + Fresnel polarity.
**No Ultralytics / AGPL. No gprMax link** (offline fixture factory only).

## Run

```bash
make sim SEED=42
make test
python3 -m gpr_void_detector --bscan fixtures/synthetic_air_void_bscan.json \
  --soil-er 9 --dx 0.05 --dt 0.1 --seed 42 --out detections.json
```

## Extension of gpr-wave-model

Imports `gpr_wave_model.velocity`, `fresnel_r`, and (for fixtures)
`synthetic_hyperbola_bscan`. Does **not** replace gpr-wave-model.
Does **not** import `forensic_pipeline`.

## Polarity map

| Fresnel R (soil→target) | gpr-wave-model `polarity` | detector label |
|---|---|---|
| R>0 (e.g. soil→air) | same | air_like |
| R<0 (e.g. soil→water) | reversed | water_like |
