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
- generation of Figures 7–9 and S3–S7 equivalents.

Primary metrics are R2, RMSEP, and MAE on remaining mass percentage. Complete-curve holdouts—not the random row split—are the primary validation.

## Expected outputs

The runners write to the existing `results/` and `figures/` directories. The ML runner writes `_reproduced` figure names by default so the published ML figures are not overwritten; the kinetics scripts write the publication figure names in `figures/main` and `figures/supplementary` directly, so run them in a separate checkout if the archived images must be preserved.

## Publication figures

```bash
python render_publication_figures.py
```

This renders Figures 3–9 and S1a–S7 from code, in Times New Roman with STIX mathematics, and rebuilds `SHA256SUMS.csv`. It runs every figure script in a temporary copy of the repository and copies back only the figure files, so the frozen tables in `results/` are never touched. Times New Roman must be installed; the scripts stop otherwise. `ALC_ALLOW_FONT_FALLBACK=1` allows previews with Liberation Serif (same glyph metrics) or DejaVu Serif. Figures 1 and 2 are static schematics and are never overwritten. The resolved font is written to `figures/RENDER_LOG.json`; the integrity test fails unless it is Times New Roman.

## Dataset-free checks

```bash
python -m unittest discover -s tests -v
```

These tests verify repository structure, parseability, absence of prohibited manuscript/data files, figure integrity, and portable source paths without requiring the dataset workbooks.
