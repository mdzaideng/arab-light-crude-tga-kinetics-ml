# Completed validation record

Validation date: 2026-08-23

## Kinetics

- Full active kinetics sequence completed successfully in the pinned package environment.
- Maximum absolute T-alpha reconstruction difference at alpha 0.2–0.8: **0.1543 K**.
- Maximum activation-energy reconstruction difference at alpha 0.2–0.7: **0.0456 kJ/mol**.
- Maximum activation-energy reconstruction difference at Air alpha 0.8: **0.5357 kJ/mol**.
- All current Figures 2–5 and S1a–S2 regenerated without execution failure.

## Machine learning

The consolidated runner was independently executed against the cleaned workbook supplied as Supplementary Material.

- Holdout results matched the authoritative ML workbook to a maximum absolute numeric difference of **8.88 × 10^-16**.
- Ablation results matched to **1.78 × 10^-15**.
- Random benchmark results matched to **1.78 × 10^-15**.
- RF six-holdout depth sensitivity matched to **1.89 × 10^-15**.
- MLR/PLSR equivalence audit matched to **3.16 × 10^-30**.

Deterministic baseline means across the six complete-curve cases:

| Baseline | Mean R2 | Mean RMSEP | Mean MAE |
|---|---:|---:|---:|
| Nearest rate | 0.986122 | 3.783700 | 2.943419 |
| Linear beta | 0.994057 | 2.281534 | 1.816515 |

## Package exclusions verified

No `.docx` file, raw/canonical/cleaned dataset workbook, old-orientation figure, checkpoint, cache, or obsolete analysis report is included in the release tree.

## Software environments on record

Three Python versions appear in this package; the numerical results agree across them to the stated tolerances.

| Record | Python | Other packages | Where recorded |
|---|---|---|---|
| Computational freeze (executed ML notebook; SI Table S6) | 3.13.5 | NumPy 2.3.5, pandas 2.2.3, scikit-learn 1.8.0, SciPy 1.17.0, Matplotlib 3.10.8 | `notebooks/ML_analysis_executed.ipynb` |
| Consolidated ML runner verification (2026-08-23) | 3.12.13 | same versions | `results/ml/Software_Environment.csv` |
| v1.0.1 regeneration (2026-10-06) | 3.13.16 | same versions (pinned `requirements.txt`) | `results/ml/Holdout_regeneration_check.txt` |

## v1.0.1 regeneration (2026-10-06)

- Full kinetics sequence (`src/kinetics/run_all_latest.py`) re-run with the three Supplementary Material workbooks: every CSV in `results/kinetics/` reproduced with zero difference.
- ML metric tables regenerated with `src/ml/export_holdout_predictions.py`: maximum absolute difference from the archived tables ≤ 1.8 × 10⁻¹⁵ (see `results/ml/Holdout_regeneration_check.txt`).
- `src/kinetics/11_build_conversion_reference_sensitivity.py` is a re-implementation written from the article text; its `reference` branch reproduces the canonical reconstruction to 2.5 × 10⁻¹² kJ/mol, and its N2-isotonic delta (zero) agrees with the earlier manuscript. Its stable-ramp-onset and ~1261 K endpoint deltas differed from the values quoted in the earlier manuscript (10.0, 16.5, 186.6, 3.0, and 1.3 kJ/mol), whose generating script was not available; thirteen alternative readings of the method were tested and none reproduced those values. The authors adopted this documented implementation, and the article now reports its output. See `results/kinetics/Conversion_Reference_Sensitivity.csv`.
