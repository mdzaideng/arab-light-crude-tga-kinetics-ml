# Changelog

## 1.0.1 — 2026-10-06

Packaging, documentation, and traceability release. Frozen numerical results (T_alpha, Ea, activation enthalpy, all ML metrics) are unchanged. Every data figure is now rendered from code in one typeface (see below); the conversion-reference sensitivity values are now produced by a script in the repository.

- moved the GitHub Actions workflow from `workflows/` to `.github/workflows/` so the dataset-free integrity tests run on push; restored `data/private/.gitkeep`;
- figure files renamed to the article numbering (nine main figures, Supplementary Figures S1a–S7); the data figures were then re-rendered (next item). Renames: `Figure1_experimental_setup` → `Figure2_experimental_setup`; `Figure2_dwell_ramp_domain_validation` → `Figure3_…`; `Figure3_TG_DTG_profiles` → `Figure4_…`; `Figure4_apparent_activation_energy` → `Figure5_…`; `Figure5_activation_enthalpy` → `Figure6_…`; `Figure6_ML_holdout_predictions` → `Figure7_…`; `Figure7_ML_model_performance` → `Figure8_…`; `Figure8_ML_atmosphere_resolved_performance` → `Figure9_…`; added `Figure1_analytical_workflow.png` (static schematic, no source file). Figure-writing lines in the kinetics scripts and the ML runner updated to the new names; script names, frozen result-table names, and executed notebooks keep their original internal numbering (mapping in `docs/FILE_INVENTORY.md`). Test expectations: 9 main and 8 supplementary PNGs;
- all data figures (Figures 3–9, S1a–S7) re-rendered from code with `render_publication_figures.py` in Times New Roman (STIX for mathematics), matching the typeface of the archived kinetics figures. `alc_core.publication_font_rc()` stops with an error if Times New Roman is missing (`ALC_ALLOW_FONT_FALLBACK=1` allows previews only). The render script records the font Matplotlib actually resolved in `figures/RENDER_LOG.json`, and `tests/test_repository.py` fails unless that font is Times New Roman, so a preview render cannot be released. Figure text harmonised: "β = 5 °C min⁻¹", "Remaining mass (%)", "±", R², N₂, temperatures in K, "RMSEP (percentage points)". Figure 4: in-figure cross-reference to the dwell panel corrected from "(see Fig. S1)" to "(see Fig. 3)" and both notes moved off the curves. Plotted data are unchanged;
- ML figures: in v1.0.0, Figures 7 and 8 came from the executed notebook and Figures 9 and S3–S7 from earlier notebooks that are not part of this package. All eight are now produced by `src/ml/run_ml_analysis.py --publication` (figures only; result tables untouched). Figure 7 keeps the notebook layout. Figure 8 keeps the notebook layout, but its bars now span the minimum–maximum of the six holdout cases instead of ±1 SD (the SVR SD bar exceeded R² = 1). Models and withheld curves are categorical, so Figures 9 and S5 show markers without connecting lines; Figure S5 orders the withheld curves by atmosphere and heating rate (5, 10, 20 °C min⁻¹) and looks values up by case rather than by row order. Figures S3, S4, S6 and S7 follow the runner's layout;
- added `src/kinetics/10_build_table1_tg_dtg_descriptors.py` and its output `results/kinetics/Table1_TG_DTG_descriptors.csv` (article Table 1; the article no longer reports a mass-loss interval, but three candidate definitions remain in the CSV for transparency);
- added `src/kinetics/11_build_conversion_reference_sensitivity.py` and `results/kinetics/Conversion_Reference_Sensitivity.csv`: re-implementation, from the article text, of the stable-ramp-onset m0, ~1261 K endpoint, and N2-isotonic sensitivity tests, whose original script was not found. The authors adopted this implementation; the article's values (Section 3.6, Supplementary Sections S3 and S16) are taken from this output (see `docs/RESULTS_VALIDATION.md`);
- `LICENSE` is now the verbatim BSD 3-Clause text; the licence-scope statement moved to `README.md`; Python versions on record documented in `docs/RESULTS_VALIDATION.md`;
- added `src/ml/export_holdout_predictions.py` (per-point holdout predictions, written outside the repository) and `results/ml/Holdout_regeneration_check.txt` (regenerated metrics agree with the archived tables to ≤ 1.8 × 10⁻¹⁵);
- data policy: experimental and cleaned datasets are provided only as the article's Supplementary Material and can be verified with the SHA-256 values listed in `data/README.md`; wording updated in `README.md`, `data/README.md`, `src/ml/run_ml_analysis.py`, `docs/`;
- `CITATION.cff`: version 1.0.1, release date, concept DOI; authors Hossain, Al-Mamun, Islam with ORCID iDs and affiliations (same order in `LICENSE`);
- licensing: code and documentation BSD 3-Clause; numerical results in `results/` CC BY 4.0 (`LICENSE-DATA`);
- `docs/REPRODUCIBILITY.md` corrected: only the ML runner writes `_reproduced` figure names; the kinetics scripts overwrite the publication file names;
- regenerated `SHA256SUMS.csv` for the full file set.

## 1.0.0 — 2026-08-23

First Zenodo-archived release (DOI 10.5281/zenodo.22069186). Content identical to 0.1.1-preacceptance except author metadata in `CITATION.cff` and `LICENSE`.

## 0.1.1-preacceptance — 2026-08-23

- added `notebooks/kinetics/01_build_canonical_pipeline.ipynb`: an executed record for the canonical preprocessing reconstruction, closing the gap where only the `.py` source existed; re-running it reproduces the shipped `Canonical_Talpha_validation.csv`/`Canonical_pipeline_m0_mf.csv` exactly (independently re-verified, main-region max |delta T_alpha| = 0.1543 K);
- removed a `tests/__pycache__/*.pyc` file that had been left in the 0.1.0 archive, contradicting the "no cache files" exclusion; tightened `tests/test_repository.py` so a shipped cache directory anywhere else in the tree fails the test, while the transient cache the test run itself creates in `tests/` is not misread as a violation;
- added a pre-zip cache-cleanup step to `docs/RELEASE_CHECKLIST.md`;
- surfaced the kinetics reconstruction-vs-original-source disclosure directly in `README.md` (previously only in `docs/PROVENANCE.md`);
- reworded "Reproducibility repository"/"Reproducibility code" in `README.md` and `CITATION.cff` to "Computational companion repository/code" to avoid any conflation with the project's separate, unrelated rule against calling single (non-replicate) TGA measurements "reproducible";
- regenerated `SHA256SUMS.csv` for the updated file set; full manifest and test suite re-verified against the rebuilt archive.

## 0.1.0-preacceptance — 2026-08-23

- assembled the latest-only kinetics and revised ML branches;
- removed manuscripts, Supplementary Information, datasets, old orientations, and intermediates;
- added a portable consolidated ML runner and deterministic heating-rate baselines;
- verified ML tables against the authoritative workbook to machine precision;
- reran the complete active kinetics pipeline;
- added final article figures, pinned environments, provenance, checksums, tests, and release guidance.
