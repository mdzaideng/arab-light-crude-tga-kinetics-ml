"""Run the complete kinetics and ML pipelines from the repository root."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-kinetics", action="store_true")
    parser.add_argument("--skip-ml", action="store_true")
    args = parser.parse_args()

    commands = []
    if not args.skip_kinetics:
        commands.append([sys.executable, str(ROOT / "src" / "kinetics" / "run_all_latest.py")])
    if not args.skip_ml:
        commands.append([sys.executable, str(ROOT / "src" / "ml" / "run_ml_analysis.py")])

    for command in commands:
        print(f"\n=== {' '.join(command)} ===")
        subprocess.run(command, cwd=ROOT, check=True)
    print("\nPASS: requested analysis branches completed")


if __name__ == "__main__":
    main()
