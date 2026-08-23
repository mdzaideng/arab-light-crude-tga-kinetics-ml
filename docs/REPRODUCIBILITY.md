# Reproducibility guide

## Environment

The frozen environment is Python 3.13.5 with the package versions in `requirements.txt`. The analysis is deterministic where stochastic estimators are used because `random_state=42` is fixed.

## Kinetics branch

Run:

```bash
python src/kinetics/run_all_latest.py
```

The active sequence is:

1. preserve experimental time order;
2. replace small backward temperature fluctuations with cumulative maximum;
3. interpolate to a 1 K grid from 323 to 1000 K;
4. apply the Air-only constant terminal offset at 1000 K;
5. apply Savitzky–Golay smoothing with window 21 and polynomial order 3;
6. apply a non-increasing isotonic constraint to N2 only;
7. calculate DTG, fractional conversion, and first-crossing conversion temperatures;
8. run FWO, KAS, and Starink regressions at alpha 0.2–0.8;
9. produce uncertainty, reconstruction, and preprocessing-sensitivity outputs.

Acceptance checks:

- maximum absolute reconstructed T-alpha difference over alpha 0.2–0.8: at most 0.5 K;
- recorded freeze result: 0.154 K;
- maximum reconstructed activation-energy difference over alpha 0.2–0.7: approximately 0.046 kJ/mol;
- Air alpha 0.8 remains a separately interpreted late-conversion regime.

## ML branch

Run:

```bash
python src/ml/run_ml_analysis.py
```

The script performs:

- random 80:20 row-split benchmark for context only;
- six complete-heating-rate holdouts, one curve withheld per atmosphere;
- RF, GBR, SVR, MLR, and PLSR evaluation;
- temperature-only versus temperature-plus-heating-rate ablation for RF and GBR;
- RF and GBR post-hoc sensitivity checks;
- nearest-rate and linear-in-heating-rate deterministic baselines;
- generation of Figures 6–8 and S3–S7 equivalents.

Primary metrics are R2, RMSEP, and MAE on remaining mass percentage. Complete-curve holdouts—not the random row split—are the primary validation.

## Expected outputs

The runners write to the existing `results/` and `figures/` directories. Publication PNGs without the `_reproduced` suffix are the exact frozen article assets. A fresh run writes `_reproduced` images so the archived article figures are not silently overwritten.

## Dataset-free checks

```bash
python -m unittest discover -s tests -v
```

These tests verify repository structure, parseability, absence of prohibited manuscript/data files, figure integrity, and portable source paths without requiring private inputs.
