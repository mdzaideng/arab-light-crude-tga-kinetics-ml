# Kinetics source

Run `python src/kinetics/run_all_latest.py` from any working directory. Inputs are resolved from `data/private/`; outputs are written to `results/kinetics/` and `figures/`.

The numbered scripts preserve the frozen execution order. `alc_core.py` contains shared preprocessing and path utilities; `kinetics_regression_core.py` contains the three isoconversional regression implementations.

`09_build_manifest.py` regenerates the repository-wide `SHA256SUMS.csv` after a completed release build.
