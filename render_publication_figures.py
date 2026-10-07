"""Render every publication figure from code and refresh the checksum manifest.

Requirements: the Supplementary Material workbooks in ``data/private/`` and the
Times New Roman font installed (the scripts stop otherwise; set
ALC_ALLOW_FONT_FALLBACK=1 only for previews).

The figure scripts run in a temporary copy of the repository; only the files
in ``figures/`` are copied back, so the frozen tables in ``results/`` are never
touched (the kinetics scripts also rewrite their CSV outputs, and line endings
or library builds on another machine could change those bytes). The ML runner
is called with ``--publication``.

The font that Matplotlib actually resolves is written to
``figures/RENDER_LOG.json``; ``tests/test_repository.py`` fails unless it is
Times New Roman, so preview renders cannot be released by mistake.

Usage (from the repository root):
    python render_publication_figures.py
"""

from __future__ import annotations

import csv
import datetime
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KINETICS_FIGURE_SCRIPTS = [
    "02_build_figure2_dwell_ramp_validation.py",          # Figure 3
    "03_build_figure3_TG_DTG_profiles.py",                # Figure 4 and Figure S2
    "04_build_figure4_activation_energy.py",              # Figure 5
    "05_build_supplementary_regression_diagnostics.py",   # Figures S1a and S1b
    "06_build_figure5_activation_enthalpy_with_CI.py",    # Figure 6
]
FIGURE_SUFFIXES = {".png", ".pdf"}
SCHEMATICS = ("Figure1_", "Figure2_")  # drawn outside the code; never overwritten


def write_manifest() -> None:
    rows = []
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT).as_posix()
        if not path.is_file() or rel == "SHA256SUMS.csv" or rel.startswith(".git/") or "__pycache__" in rel:
            continue
        if rel.startswith("data/private/") and rel != "data/private/.gitkeep":
            continue
        data = path.read_bytes()
        rows.append((rel, len(data), hashlib.sha256(data).hexdigest()))
    with (ROOT / "SHA256SUMS.csv").open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["relative_path", "bytes", "sha256"])
        writer.writerows(rows)


def resolved_font() -> dict:
    """Font Matplotlib resolves with the publication rc (the same rc the figure scripts use)."""
    sys.dont_write_bytecode = True  # keep the release tree free of __pycache__
    sys.path.insert(0, str(ROOT / "src" / "kinetics"))
    import matplotlib
    from matplotlib import font_manager
    from alc_core import publication_font_rc  # raises unless Times New Roman or ALC_ALLOW_FONT_FALLBACK=1

    matplotlib.rcParams.update(publication_font_rc())
    path = font_manager.findfont(font_manager.FontProperties(family="serif"), fallback_to_default=True)
    return {"font_family": font_manager.FontProperties(fname=path).get_name(), "font_file": Path(path).name,
            "fallback_allowed": os.environ.get("ALC_ALLOW_FONT_FALLBACK") == "1",
            "matplotlib": matplotlib.__version__, "python": platform.python_version(), "platform": platform.system()}


def main() -> None:
    font = resolved_font()
    print(f"Resolved publication font: {font['font_family']} ({font['font_file']})")
    rendered = []
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        for script in KINETICS_FIGURE_SCRIPTS:
            print(f"=== {script}")
            subprocess.run([sys.executable, script], cwd=work / "src" / "kinetics", check=True)
        print("=== src/ml/run_ml_analysis.py --publication")
        subprocess.run([sys.executable, "src/ml/run_ml_analysis.py", "--publication"], cwd=work, check=True)
        copied = 0
        for folder in ("main", "supplementary"):
            for path in (work / "figures" / folder).iterdir():
                target = ROOT / "figures" / folder / path.name
                if (path.suffix in FIGURE_SUFFIXES and "_reproduced" not in path.name and target.exists()
                        and not path.name.startswith(SCHEMATICS)):
                    shutil.copy2(path, target)
                    rendered.append(f"figures/{folder}/{path.name}")
                    copied += 1
    log = {**font, "rendered_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "figures": sorted(rendered), "not_rendered_from_code": ["figures/main/Figure1_analytical_workflow.png",
                                                                  "figures/main/Figure2_experimental_setup.png"]}
    (ROOT / "figures" / "RENDER_LOG.json").write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    write_manifest()
    print(f"PASS: {copied} publication figure files rendered and copied; results/ untouched; SHA256SUMS.csv rebuilt")


if __name__ == "__main__":
    main()
