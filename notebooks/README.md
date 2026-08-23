# Notebook archive

`ML_analysis_executed.ipynb` and its PDF rendering are the latest supplied execution record for the revised ML core. The `kinetics/` subfolder retains the active notebook mirrors from the frozen kinetics package, including `01_build_canonical_pipeline.ipynb` — the executed record for the canonical preprocessing reconstruction, added to close the gap left when only the `.py` source was originally archived. Its output cells reproduce the frozen `Canonical_Talpha_validation.csv`/`Canonical_pipeline_m0_mf.csv` exactly.

Use the Python files in `src/` for portable reruns. The ML notebook expects the cleaned dataset filename in its working directory and predates the final deterministic-baseline packaging step.
