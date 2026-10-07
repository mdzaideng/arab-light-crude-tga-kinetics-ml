# Arab Light crude TGA: kinetics and heating-rate-holdout machine learning

Computational companion repository — code, frozen results, and figures — for **“Isoconversional Kinetics and Heating-Rate-Holdout Machine Learning for Arab Light Crude TGA under N₂ and Air.”**

This repository contains the analysis code, executed notebooks, frozen numerical results, and publication figures. Experimental and cleaned datasets are provided only as the article's Supplementary Material and can be verified with the SHA-256 values listed in [data/README.md](data/README.md).

**Kinetics preprocessing status.** The kinetics preprocessing code (`src/kinetics/01\_build\_canonical\_pipeline.py`) is a **validated reconstruction** of the original method, built from the archived Methods text, Supplementary Table S1, and the frozen `Kinetic\_Talpha` reference outputs — it is *not* the originally executed source. Running it reproduces the authoritative T\_alpha values to within 0.154 K (alpha 0.2–0.8) and the corresponding activation energies to within 0.046–0.536 kJ/mol; see [docs/PROVENANCE.md](docs/PROVENANCE.md) and `results/kinetics/Canonical\_Reconstruction\_provenance.txt` for the full disclosure. The machine-learning branch, by contrast, is verified against the authoritative results workbook to machine precision (see [docs/RESULTS\_VALIDATION.md](docs/RESULTS_VALIDATION.md)).

## What is included

* FWO, KAS, and Starink isoconversional kinetics code
* canonical preprocessing reconstruction and sensitivity checks
* complete-heating-rate-holdout ML code for RF, GBR, SVR, MLR, and PLSR
* predictor-ablation, post-hoc sensitivity, and deterministic heating-rate baselines
* final machine-readable result tables and consolidated result workbooks
* publication Figures 1–9 and Supplementary Figures S1a–S7, numbered as in the article (see [docs/FILE\_INVENTORY.md](docs/FILE_INVENTORY.md))
* pinned environments, validation tests, checksums, citation metadata, and release guidance

## Repository layout

```text
data/                 Input-file names, schema, and SHA-256 values (datasets not distributed here)
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
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Conda users can instead run `conda env create -f environment.yml`.

## Reproduce the analyses

1. Place the Supplementary Material workbooks in `data/private/` using the exact filenames listed in [data/README.md](data/README.md).
2. Run everything:

```bash
python run\_all.py
```

To re-render every publication figure (Times New Roman required) without touching the frozen tables:

```bash
python render\_publication\_figures.py
```

Individual branches can be run with:

```bash
python src/kinetics/run\_all\_latest.py
python src/ml/run\_ml\_analysis.py
```

The frozen outputs already distributed in `results/` allow numerical review without the input workbooks. See [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) for expected checks and [docs/RESULTS\_VALIDATION.md](docs/RESULTS_VALIDATION.md) for the completed audit.

## Headline frozen results

* KAS apparent activation energy: 45.6–118.1 kJ/mol under N2 and 30.6–91.9 kJ/mol across the principal Air region (alpha 0.2–0.7).
* Air alpha 0.8: 258.9 ± 34.9 kJ/mol regression SE; interpreted separately because its conditional interval and preprocessing sensitivity are large.
* RF and GBR complete-rate holdouts: mean R2 approximately 0.9861 and RMSEP approximately 3.78 mass-percentage points.
* Linear heating-rate baseline: mean R2 0.9941 and RMSEP 2.2815, outperforming the trained models overall in this dataset.

These are descriptive results for one Arab Light sample measured once at each atmosphere–heating-rate condition. They are not replicate-based population estimates.

## Data status

Experimental and cleaned datasets are provided only as the article's Supplementary Material and can be verified with the SHA-256 values listed in [data/README.md](data/README.md). No synthetic or substituted dataset is included. To rerun the analyses, place the Supplementary Material workbooks in `data/private/` under the filenames given there.

## Citation and license

Citation metadata are provided in [CITATION.cff](CITATION.cff). Please cite the associated article and the archived release (all versions: https://doi.org/10.5281/zenodo.22069185). Licence scope: source code and repository documentation are released under the [BSD 3-Clause License](LICENSE); numerical result files in `results/` are released under [CC BY 4.0](LICENSE-DATA). Publication figures in `figures/` are covered by neither licence; their reuse follows the terms of the associated journal article. Experimental and cleaned datasets are not part of this repository.

## Release status

Version `1.0.1` (2026-10-06). Packaging and documentation update of v1.0.0; frozen numerical results are unchanged, Table 1 and conversion-reference scripts were added, and all data figures are rendered from code (`figures/RENDER\_LOG.json` records the font used). See [CHANGELOG.md](CHANGELOG.md).

