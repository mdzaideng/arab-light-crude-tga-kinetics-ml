# File and manuscript mapping

Figure numbers follow the article (nine main-text figures, Supplementary Figures S1a–S7). Script names and frozen result-table names keep their original internal numbering (for example `02_build_figure2_...py`, `Figure2_Threshold_Sensitivity.csv`); this table is the authoritative map. Executed notebooks are retained as run and were not edited.

| Article item | Repository asset | Generating code or status | Supplementary Data S1 sheet |
|---|---|---|---|
| Figure 1 | `figures/main/Figure1_analytical_workflow.png` | Static schematic, extracted from the manuscript file; no source file | — |
| Figure 2 | `figures/main/Figure2_experimental_setup.{png,svg}` | Static schematic; SVG source included | — |
| Figure 3 | `figures/main/Figure3_dwell_ramp_domain_validation.{png,pdf}` | `src/kinetics/02_build_figure2_dwell_ramp_validation.py` | Fig3_dwell, Fig3_ramp_stabilization, Fig3_onsets |
| Figure 4 | `figures/main/Figure4_TG_DTG_profiles.{png,pdf}` | `src/kinetics/03_build_figure3_TG_DTG_profiles.py` (re-rendered in v1.0.1) | Fig4_TG_DTG |
| Figure 5 | `figures/main/Figure5_apparent_activation_energy.{png,pdf}` | `src/kinetics/04_build_figure4_activation_energy.py` | Fig5_Ea_KAS |
| Figure 6 | `figures/main/Figure6_activation_enthalpy.png` | `src/kinetics/06_build_figure5_activation_enthalpy_with_CI.py` | Fig6_dH_KAS |
| Figure 7 | `figures/main/Figure7_ML_holdout_predictions.png` | `src/ml/run_ml_analysis.py --publication` (layout of the executed notebook); per-point values via `src/ml/export_holdout_predictions.py` | Fig7_holdout_predictions |
| Figure 8 | `figures/main/Figure8_ML_model_performance.png` | `src/ml/run_ml_analysis.py --publication` (layout of the executed notebook) | Fig8_9_holdout_metrics |
| Figure 9 | `figures/main/Figure9_ML_atmosphere_resolved_performance.png` | `src/ml/run_ml_analysis.py --publication` | Fig8_9_holdout_metrics |
| Table 1 | `results/kinetics/Table1_TG_DTG_descriptors.csv` | `src/kinetics/10_build_table1_tg_dtg_descriptors.py` | Table1_descriptors |
| Conversion-reference, endpoint and N2-isotonic sensitivity (Section 3.6, SI S3/S16) | `results/kinetics/Conversion_Reference_Sensitivity.csv` | `src/kinetics/11_build_conversion_reference_sensitivity.py` (re-implementation; see docs/RESULTS_VALIDATION.md) | — |
| Figures S1a–S1b | `figures/supplementary/FigureS1*.{png,pdf}` | `src/kinetics/05_build_supplementary_regression_diagnostics.py` | FigS1_regression_points, FigS1_regression_fits |
| Figure S2 | `figures/supplementary/FigureS2_time_domain_mass_comparison.{png,pdf}` | `src/kinetics/03_build_figure3_TG_DTG_profiles.py` | FigS2_and_raw_curves |
| Figures S3–S7 | `figures/supplementary/FigureS3*.png` … `FigureS7*.png` | `src/ml/run_ml_analysis.py --publication` | FigS3_*, FigS4_S7_*, FigS5_*, FigS6_* |
| Canonical preprocessing reconstruction | `results/kinetics/Canonical_Talpha_validation.csv`, `Canonical_pipeline_m0_mf.csv` | `src/kinetics/01_build_canonical_pipeline.py`, executed in `notebooks/kinetics/01_build_canonical_pipeline.ipynb` | — |
| Complete kinetic tables | `results/kinetics/` | Active kinetics scripts and frozen workbooks | — |
| Complete ML tables | `results/ml/*.csv` | Consolidated ML runner | — |
| ML regeneration check | `results/ml/Holdout_regeneration_check.txt` | `src/ml/export_holdout_predictions.py` | — |
| ML result workbook | `results/ml/Arab_Light_TGA_ML_REVISED_Results_FINAL_WITH_FIGURES.xlsx` | Frozen authoritative workbook | — |
| Executed ML audit | `notebooks/ML_analysis_executed.{ipynb,pdf}` | Latest supplied execution record | — |
| Kinetics notebook mirrors | `notebooks/kinetics/` | Active notebook versions from the frozen kinetics package | — |

All data figures (3–9, S1a–S7) are rendered together by `render_publication_figures.py` (Times New Roman). The resolved font and the list of rendered files are recorded in `figures/RENDER_LOG.json`. The exact publication figures have no `_reproduced` suffix. The ML runner writes `_reproduced` copies; the kinetics scripts overwrite the publication file names (see docs/REPRODUCIBILITY.md).

Frozen workbook sheets (`Figure_Map_LATEST` in `results/kinetics/Arab_Light_Kinetics_Consolidated_Results.xlsx`) keep the internal numbering used when they were frozen.
