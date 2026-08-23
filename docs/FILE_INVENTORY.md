# File and manuscript mapping

| Article item | Repository asset | Generating code or status |
|---|---|---|
| Figure 1 | `figures/main/Figure1_experimental_setup.*` | Static schematic; SVG source included |
| Figure 2 | `figures/main/Figure2_dwell_ramp_domain_validation.*` | `src/kinetics/02_build_figure2_dwell_ramp_validation.py` |
| Figure 3 | `figures/main/Figure3_TG_DTG_profiles.*` | `src/kinetics/03_build_figure3_TG_DTG_profiles.py` |
| Figure 4 | `figures/main/Figure4_apparent_activation_energy.*` | `src/kinetics/04_build_figure4_activation_energy.py` |
| Figure 5 | `figures/main/Figure5_activation_enthalpy.png` | `src/kinetics/06_build_figure5_activation_enthalpy_with_CI.py` |
| Figure 6 | `figures/main/Figure6_ML_holdout_predictions.png` | `src/ml/run_ml_analysis.py` |
| Figure 7 | `figures/main/Figure7_ML_model_performance.png` | `src/ml/run_ml_analysis.py` |
| Figure 8 | `figures/main/Figure8_ML_atmosphere_resolved_performance.png` | `src/ml/run_ml_analysis.py` |
| Figures S1a–S1b | `figures/supplementary/FigureS1*.{png,pdf}` | `src/kinetics/05_build_supplementary_regression_diagnostics.py` |
| Figure S2 | `figures/supplementary/FigureS2_time_domain_mass_comparison.*` | Figure 3 kinetics script |
| Figures S3–S7 | `figures/supplementary/FigureS3*.png` through `FigureS7*.png` | `src/ml/run_ml_analysis.py` |
| Canonical preprocessing reconstruction | `results/kinetics/Canonical_Talpha_validation.csv`, `Canonical_pipeline_m0_mf.csv` | `src/kinetics/01_build_canonical_pipeline.py`, executed in `notebooks/kinetics/01_build_canonical_pipeline.ipynb` |
| Complete kinetic tables | `results/kinetics/` | Active kinetics scripts and frozen workbooks |
| Complete ML tables | `results/ml/*.csv` | Consolidated ML runner |
| ML result workbook | `results/ml/Arab_Light_TGA_ML_REVISED_Results_FINAL_WITH_FIGURES.xlsx` | Frozen authoritative workbook |
| Executed ML audit | `notebooks/ML_analysis_executed.{ipynb,pdf}` | Latest supplied execution record |
| Kinetics notebook mirrors | `notebooks/kinetics/` | Active notebook versions from the frozen kinetics package |

The exact publication figures have no `_reproduced` suffix. Fresh analysis runs use that suffix to preserve the frozen article assets.
