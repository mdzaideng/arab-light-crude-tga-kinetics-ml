from __future__ import annotations
from pathlib import Path
import subprocess, sys
HERE=Path(__file__).resolve().parent
SCRIPTS=[
"01_build_canonical_pipeline.py",
"07_build_canonical_reconstruction_validation.py",
"08_build_preprocessing_sensitivity.py",
"02_build_figure2_dwell_ramp_validation.py",
"03_build_figure3_TG_DTG_profiles.py",
"04_build_figure4_activation_energy.py",
"05_build_supplementary_regression_diagnostics.py",
"06_build_figure5_activation_enthalpy_with_CI.py",
"10_build_table1_tg_dtg_descriptors.py",
"11_build_conversion_reference_sensitivity.py",
]
for name in SCRIPTS:
    print(f"\n=== {name} ===")
    subprocess.run([sys.executable, str(HERE/name)], check=True, cwd=HERE)
print("\nPASS: all current kinetics scripts completed")
