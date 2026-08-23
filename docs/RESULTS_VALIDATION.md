# Completed validation record

Validation date: 2026-08-23

## Kinetics

- Full active kinetics sequence completed successfully in the pinned package environment.
- Maximum absolute T-alpha reconstruction difference at alpha 0.2–0.8: **0.1543 K**.
- Maximum activation-energy reconstruction difference at alpha 0.2–0.7: **0.0456 kJ/mol**.
- Maximum activation-energy reconstruction difference at Air alpha 0.8: **0.5357 kJ/mol**.
- All current Figures 2–5 and S1a–S2 regenerated without execution failure.

## Machine learning

The consolidated runner was independently executed against the withheld cleaned workbook.

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
