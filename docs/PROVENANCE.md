# Package provenance and version selection

This repository was assembled from the three supplied computational archives and checked against the final combined main manuscript and Supplementary Information. The manuscripts were used only to verify titles, figure numbering, captions, result mapping, and the final analytical orientation; neither document is included here.

## Retained authoritative branches

- **Kinetics:** the 2026-08-19 `Arab_Light_Kinetics_Submission_Ready` frozen package, after an independent full rerun of its active scripts.
- **Machine learning:** the 2026-08-08 revised executed notebook and final results workbook, supplemented by a consolidated portable runner that reproduces the final holdout tables and implements the deterministic-baseline audit reported in the combined article.
- **Publication assets:** exact images extracted from the two final supporting documents and hash-matched against the frozen kinetics assets where standalone originals existed.

## Deliberately excluded

- main manuscript and Supplementary Information;
- raw, canonical, and cleaned input workbooks;
- July tree-ensemble step PDFs and analysis reports;
- obsolete July notebooks, figures, result tables, Colab paths, and cross-atmosphere/virtual-rate orientations;
- checkpoint notebooks, Python caches, R history, duplicate figures, and old Figure 1 orientation;
- superseded manuscript-specific files from the kinetics and ML archives.

## Important reconstruction disclosure

The kinetics preprocessing implementation is a validated reconstruction of the frozen method and outputs, not a claim that the originally executed preprocessing source was recovered. Its archived provenance statement is retained in `results/kinetics/Canonical_Reconstruction_provenance.txt`.
