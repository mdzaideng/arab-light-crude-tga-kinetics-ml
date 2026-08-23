# Changelog

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
