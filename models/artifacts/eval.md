# Krishiayan model evaluation

Samples: 2400 (plot-id grouped split)

| Head | MAE | R² | 90% interval coverage |
|---|---:|---:|---:|
| n_mgkg | 11.1268 | 0.9733 | 0.8792 |
| p_mgkg | 1.0775 | 0.972 | 0.9125 |
| k_mgkg | 9.3109 | 0.9716 | 0.925 |
| soc_pct | 0.0292 | 0.974 | 0.9104 |
| ph_hat | 0.0971 | 0.9701 | 0.9042 |
| yield_index | 0.0154 | 0.9655 | 0.9 |
| stress | accuracy 0.9187 | — | — |

## Wet-soil optical path

- Wet test rows: 239
- Mean raw 660 nm (collapsed): 0.0129
- Mean corrected 660 nm: 0.2815
- SOC MAE wet / dry: 0.0312 / 0.0272

Simulated data is labelled `sim:` everywhere. These numbers prove the pipeline recovers planted truth.
