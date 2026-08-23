# Arab Light Crude TGA: Isoconversional Kinetics and Heating-Rate-Holdout Machine Learning

> Computational companion repository — code, frozen results, and publication figures — for
> **"Integrated Isoconversional Kinetics and Heating-Rate-Holdout Machine Learning for Thermogravimetric Analysis of Arab Light Crude under Nitrogen and Air"**

[![DOI](https://zenodo.org/badge/1343750345.svg)](https://doi.org/10.5281/zenodo.22069185)
![Python](https://img.shields.io/badge/Python-3.13.5-blue)
![License](https://img.shields.io/badge/License-BSD%203--Clause-green)
![Tests](https://img.shields.io/badge/Tests-7%2F7%20passing-brightgreen)
![Status](https://img.shields.io/badge/Status-Pre--acceptance-orange)

**Archived release:** v0.1.1 &nbsp;|&nbsp; **Version DOI:** https://doi.org/10.5281/zenodo.22069186 &nbsp;|&nbsp; **All-versions DOI:** https://doi.org/10.5281/zenodo.22069185

---

## Authors

| Name | Affiliation |
|---|---|
| K. M. Oajedul Islam | University of Dhaka, Bangladesh |
| Md. Abdullah Al-Mamun | Khulna University of Engineering and Technology (KUET), Bangladesh |
| Md. Zaid Hossain | Khulna University of Engineering and Technology (KUET), Bangladesh |

---

## Overview

This repository provides the complete computational record for a paired study of Arab Light crude thermogravimetric analysis under two atmospheres (N₂ and air) at three heating rates (5, 10, and 20 °C min⁻¹). It covers two parallel analytical tracks:

- **Kinetics track** — FWO, KAS, and Starink isoconversional regressions at α = 0.2–0.8, with full uncertainty quantification (conditional 95% CI, df = 1), activation enthalpy (ΔH‡), and preprocessing sensitivity analysis.
- **Machine learning track** — complete-heating-rate-holdout (LORO) evaluation of five models (RF, GBR, SVR, MLR, PLSR), predictor ablation, post-hoc sensitivity, and deterministic heating-rate baselines.

> **Data availability.** Raw TGA measurements and the cleaned ML dataset are withheld pending article acceptance. Expected filenames, schemas, and SHA-256 identifiers are documented in [`data/README.md`](data/README.md) so the later data release can be independently verified.

---

## Repository structure

```text
arab-light-crude-tga-kinetics-ml/
├── data/
│   ├── private/              ← withheld datasets (see data/README.md)
│   └── README.md             ← expected filenames, schemas, SHA-256 identifiers
├── docs/
│   ├── REPRODUCIBILITY.md    ← step-by-step rerun guide
│   ├── PROVENANCE.md         ← kinetics reconstruction disclosure
│   ├── RESULTS_VALIDATION.md ← completed numerical audit
│   ├── FILE_INVENTORY.md     ← figure-to-code mapping
│   └── RELEASE_CHECKLIST.md  ← pre-publication steps
├── figures/
│   ├── main/                 ← Figures 1–8 (PNG + PDF)
│   └── supplementary/        ← Figures S1a–S7 (PNG + PDF)
├── notebooks/
│   ├── kinetics/             ← executed kinetics notebooks (01–09)
│   └── ML_analysis_executed.ipynb
├── results/
│   ├── kinetics/             ← frozen kinetics tables, workbooks, provenance
│   └── ml/                   ← frozen ML tables, baseline audits, workbook
├── src/
│   ├── kinetics/             ← active kinetics pipeline (01–09 + core modules)
│   └── ml/                   ← consolidated ML runner
├── tests/
│   └── test_repository.py    ← 7 dataset-free integrity tests
├── run_all.py                ← single-command full pipeline
├── requirements.txt          ← pinned Python dependencies
├── environment.yml           ← Conda environment spec
├── SHA256SUMS.csv            ← SHA-256 manifest (107 files)
├── CITATION.cff              ← machine-readable citation metadata
├── CHANGELOG.md
└── LICENSE                   ← BSD 3-Clause
```

---

## Headline results

### Kinetics (KAS method, α = 0.2–0.8)

| Atmosphere | α range | Eₐ range (kJ mol⁻¹) | R² range | Notes |
|:---:|:---:|:---:|:---:|---|
| N₂ | 0.2–0.8 | 45.6 → 118.1 | 0.988–0.998 | CIs include zero from α = 0.5 |
| Air | 0.2–0.7 | 30.6 → 91.9 | 0.995–1.000 | Principal region |
| Air | 0.8 | 258.9 ± 34.9 (SE) | 0.982 | Late-residue oxidation; CI [−185, +703] — **qualitative only** |

> Conditional 95% CIs use t-critical = 12.706 (df = 1, n = 3 heating rates). Air α = 0.8 is treated qualitatively throughout.

### Machine learning (complete-heating-rate-holdout / LORO)

| Model | Mean R² | Mean RMSEP (mass%) | Mean MAE (mass%) |
|:---:|:---:|:---:|:---:|
| **RF** | **0.9861** | **3.78** | **2.94** |
| **GBR** | **0.9861** | **3.79** | **2.95** |
| SVR | 0.826 | 11.89 | 10.32 |
| MLR | 0.928 | 8.58 | 7.25 |
| PLSR | 0.928 | 8.58 | 7.25 |

| Deterministic baseline | Mean R² | Mean RMSEP (mass%) |
|:---:|:---:|:---:|
| Linear-β interpolation | 0.9941 | 2.28 |
| Nearest-rate | 0.9861 | 3.78 |

> RF and GBR perform equally well and both match the nearest-rate deterministic baseline, while the linear-β interpolation outperforms all trained models. Results are for one Arab Light sample at each atmosphere–heating-rate condition — not replicate-based population estimates.

---

## Kinetics preprocessing disclosure

The kinetics preprocessing code (`src/kinetics/01_build_canonical_pipeline.py`) is a **validated reconstruction** of the original method, inferred from the archived Methods text, Supplementary Table S1, and the frozen `Kinetic_Talpha` reference outputs — it is **not** the originally executed source code.

Re-running it reproduces the authoritative T_α values to within **0.154 K** (α = 0.2–0.8) and activation energies to within **0.046–0.536 kJ mol⁻¹**. The key reconstruction detail was inferring that the Air baseline correction anchor is T = 1000 K (the canonical grid boundary), not the raw acquisition endpoint near 1262 K.

Full disclosure: [`docs/PROVENANCE.md`](docs/PROVENANCE.md) and `results/kinetics/Canonical_Reconstruction_provenance.txt`.

The machine-learning branch is verified against the authoritative results workbook to **machine precision** (max absolute difference ≤ 8.88 × 10⁻¹⁶). See [`docs/RESULTS_VALIDATION.md`](docs/RESULTS_VALIDATION.md).

---

## Installation

Python 3.13.5 was used for the computational freeze.

**pip (recommended):**
```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Conda:**
```bash
conda env create -f environment.yml
conda activate arab-light-tga
```

**Dependencies:** `numpy==2.3.5` · `pandas==2.2.3` · `scipy==1.17.0` · `scikit-learn==1.8.0` · `matplotlib==3.10.8` · `openpyxl==3.1.5`

---

## Reproducing the analyses

**Step 1 — add the private datasets** (after acceptance):

Place the verified workbooks in `data/private/` using exact filenames from [`data/README.md`](data/README.md).

**Step 2 — run everything:**

```bash
python run_all.py
```

Or run individual branches:

```bash
# Kinetics only
python src/kinetics/run_all_latest.py

# Machine learning only
python src/ml/run_ml_analysis.py
```

Fresh runs write figures with a `_reproduced` suffix, preserving the frozen publication assets.

**Step 3 — verify integrity (no dataset required):**

```bash
python -m unittest discover -s tests -v
```

All 7 tests pass on the distributed package without any private inputs.

> The frozen outputs in `results/` allow full numerical review before the datasets are made public. See [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) for acceptance criteria and expected output values.

---

## Figure inventory

| Figure | File | Generated by |
|:---:|---|---|
| 1 | `figures/main/Figure1_experimental_setup.*` | Static schematic (SVG source included) |
| 2 | `figures/main/Figure2_dwell_ramp_domain_validation.*` | `src/kinetics/02_build_figure2_dwell_ramp_validation.py` |
| 3 | `figures/main/Figure3_TG_DTG_profiles.*` | `src/kinetics/03_build_figure3_TG_DTG_profiles.py` |
| 4 | `figures/main/Figure4_apparent_activation_energy.*` | `src/kinetics/04_build_figure4_activation_energy.py` |
| 5 | `figures/main/Figure5_activation_enthalpy.*` | `src/kinetics/06_build_figure5_activation_enthalpy_with_CI.py` |
| 6 | `figures/main/Figure6_ML_holdout_predictions.png` | `src/ml/run_ml_analysis.py` |
| 7 | `figures/main/Figure7_ML_model_performance.png` | `src/ml/run_ml_analysis.py` |
| 8 | `figures/main/Figure8_ML_atmosphere_resolved_performance.png` | `src/ml/run_ml_analysis.py` |
| S1a/S1b | `figures/supplementary/FigureS1*.*` | `src/kinetics/05_build_supplementary_regression_diagnostics.py` |
| S2 | `figures/supplementary/FigureS2*.*` | `src/kinetics/03_build_figure3_TG_DTG_profiles.py` |
| S3–S7 | `figures/supplementary/FigureS3–S7*.png` | `src/ml/run_ml_analysis.py` |

---

## Repository integrity

The SHA-256 manifest (`SHA256SUMS.csv`) covers all 107 files. Verify from the repository root:

```bash
python -c "
import csv, hashlib
rows = list(csv.DictReader(open('SHA256SUMS.csv')))
bad = [r['relative_path'] for r in rows
       if hashlib.sha256(open(r['relative_path'],'rb').read()).hexdigest() != r['sha256']]
print('OK' if not bad else f'MISMATCH: {bad}')
"
```

Archive SHA-256 (v1.0.0): `562fa0d89fb6d90bb2e138727ec70471e89d1fbb522bac4bf944021db8ef6af5`

---

## Citation

If you use this code or its results, please cite the archived release:

```bibtex
@software{islam_alc_tga_2026,
  author    = {Islam, K. M. Oajedul and Al-Mamun, Md. Abdullah and Hossain, Md. Zaid},
  title     = {Arab Light Crude TGA: Isoconversional Kinetics and
               Heating-Rate-Holdout Machine Learning},
  version   = {1.0.0},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.22069186},
  url       = {https://doi.org/10.5281/zenodo.22069186}
}
```

Full citation metadata are in [`CITATION.cff`](CITATION.cff). Journal article DOI will be added after acceptance.

---

## License

Source code and repository documentation are released under the **BSD 3-Clause License** — see [`LICENSE`](LICENSE).
Frozen result files and publication figures remain subject to the associated article's publication terms unless separately licensed by the authors.

---

## Release status

**v0.1.1** — Assembled 2026-08-23. Code and results complete; manuscript under review; dataset withheld pending acceptance.
Complete [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md) before tagging v1.0.0.
