# Arab Light crude TGA: kinetics and heating-rate-holdout machine learning

Computational companion repository — code, frozen results, and figures — for **“Integrated Isoconversional Kinetics and Heating-Rate-Holdout Machine Learning for Thermogravimetric Analysis of Arab Light Crude under Nitrogen and Air.”**

This pre-acceptance release contains the analysis code, frozen numerical results, and publication figures. It intentionally does **not** contain the article manuscript, Supplementary Information, raw TGA measurements, canonical kinetics workbook, or cleaned ML dataset. The private inputs can be added later without changing the repository structure.

**Kinetics preprocessing status.** The kinetics preprocessing code (`src/kinetics/01_build_canonical_pipeline.py`) is a **validated reconstruction** of the original method, built from the archived Methods text, Supplementary Table S1, and the frozen `Kinetic_Talpha` reference outputs — it is *not* the originally executed source. Running it reproduces the authoritative T_alpha values to within 0.154 K (alpha 0.2–0.8) and the corresponding activation energies to within 0.046–0.536 kJ/mol; see [docs/PROVENANCE.md](docs/PROVENANCE.md) and `results/kinetics/Canonical_Reconstruction_provenance.txt` for the full disclosure. The machine-learning branch, by contrast, is verified against the authoritative results workbook to machine precision (see [docs/RESULTS_VALIDATION.md](docs/RESULTS_VALIDATION.md)).

## What is included

- FWO, KAS, and Starink isoconversional kinetics code
- canonical preprocessing reconstruction and sensitivity checks
- complete-heating-rate-holdout ML code for RF, GBR, SVR, MLR, and PLSR
- predictor-ablation, post-hoc sensitivity, and deterministic heating-rate baselines
- final machine-readable result tables and consolidated result workbooks
- publication Figures 1–8 and Supplementary Figures S1a–S7
- pinned environments, validation tests, checksums, citation metadata, and release guidance

## Repository layout

```text
data/                 Private-input instructions; no dataset is distributed
docs/                 Reproducibility, provenance, mapping, and release notes
figures/main/         Final main-text figures
figures/supplementary Final supplementary figures
notebooks/            Latest executed ML notebook retained for auditability
results/kinetics/     Frozen kinetics tables, workbooks, checks, and provenance
results/ml/           Frozen ML tables, baseline audits, and results workbook
src/kinetics/         Active kinetics pipeline
src/ml/               Consolidated ML and deterministic-baseline pipeline
tests/                Dataset-free repository integrity tests
```

## Installation

Python 3.13.5 was used for the computational freeze.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Conda users can instead run `conda env create -f environment.yml`.

## Reproduce the analyses

1. Place the private workbooks in `data/private/` using the exact filenames listed in [data/README.md](data/README.md).
2. Run everything:

```bash
python run_all.py
```

Individual branches can be run with:

```bash
python src/kinetics/run_all_latest.py
python src/ml/run_ml_analysis.py
```

The frozen outputs already distributed in `results/` allow numerical review before the datasets are made public. See [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) for expected checks and [docs/RESULTS_VALIDATION.md](docs/RESULTS_VALIDATION.md) for the completed audit.

## Headline frozen results

- KAS apparent activation energy: 45.6–118.1 kJ/mol under N2 and 30.6–91.9 kJ/mol across the principal Air region (alpha 0.2–0.7).
- Air alpha 0.8: 258.9 ± 34.9 kJ/mol regression SE; interpreted separately because its conditional interval and preprocessing sensitivity are large.
- RF and GBR complete-rate holdouts: mean R2 approximately 0.9861 and RMSEP approximately 3.78 mass-percentage points.
- Linear heating-rate baseline: mean R2 0.9941 and RMSEP 2.2815, outperforming the trained models overall in this dataset.

These are descriptive results for one Arab Light sample measured once at each atmosphere–heating-rate condition. They are not replicate-based population estimates.

## Data status

The inputs are withheld from this GitHub package at the author’s request until article acceptance. No synthetic or substituted dataset has been inserted. The exact expected filenames, sheets, schema, and SHA-256 identifiers are documented so that the later data release can be verified.

## Citation and license

Citation metadata are provided in [CITATION.cff](CITATION.cff). Replace the temporary author entry and add the article DOI before the first public archival release. Code is released under the [BSD 3-Clause License](LICENSE); result data and figures remain subject to the associated article’s publication terms unless separately licensed by the authors.

## Release status

Version `0.1.1-preacceptance` — GitHub-ready computational package, assembled 2026-08-23 (post-review fixes applied). Complete the short [release checklist](docs/RELEASE_CHECKLIST.md) before publishing.
