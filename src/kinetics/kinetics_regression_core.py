from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "alc-matplotlib-cache"))

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import openpyxl
import pandas as pd
from scipy.stats import t as student_t


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[1]
PRIVATE_DATA_DIR = REPOSITORY_ROOT / "data" / "private"
DEFAULT_SOURCE_NAMES = (
    "Arab_Light_TGA_Canonical_Data.xlsx",
)
BETAS = np.array([5.0, 10.0, 20.0])
ALPHAS = np.array([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
ATMOSPHERES = ("N2", "Air")
MODELS = ("FWO", "KAS", "Starink")
MODEL_FACTORS = {"FWO": 1.052, "KAS": 1.0, "Starink": 1.0008}
R_KJ_MOL_K = 0.00831446261815324


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the uncertainty-aware main apparent activation-energy figure."
    )
    parser.add_argument("--source", type=Path, help="Input cleaned TGA workbook.")
    parser.add_argument(
        "--output-dir", type=Path, default=SCRIPT_DIR,
        help="Output directory (default: directory containing this script).",
    )
    return parser.parse_args()


def resolve_source(requested: Path | None) -> Path:
    if requested is not None:
        source = requested.expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Source workbook not found: {source}")
        return source
    search_dirs = (PRIVATE_DATA_DIR, SCRIPT_DIR)
    for directory in search_dirs:
        for name in DEFAULT_SOURCE_NAMES:
            candidate = directory / name
            if candidate.is_file():
                return candidate
    raise FileNotFoundError(
        "No source workbook found beside the script. Pass --source or bundle one of: "
        + ", ".join(DEFAULT_SOURCE_NAMES)
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_talpha(source: Path) -> dict[tuple[str, float], dict[int, float]]:
    workbook = openpyxl.load_workbook(source, data_only=True, read_only=True)
    required = {"README", "Kinetic_Talpha", "Cleaning_Audit"}
    missing = sorted(required - set(workbook.sheetnames))
    if missing:
        raise ValueError(f"Workbook missing required sheet(s): {missing}")
    rows = list(workbook["Kinetic_Talpha"].iter_rows(values_only=True))
    header_index = None
    for index, row in enumerate(rows):
        normalized = [str(value).strip().lower() if value is not None else "" for value in row]
        if "atmosphere" in normalized and "alpha" in normalized:
            header_index = index
            break
    if header_index is None:
        raise ValueError("Could not locate the atmosphere/alpha header row in Kinetic_Talpha.")
    header = [str(value).strip() if value is not None else "" for value in rows[header_index]]
    atm_col = header.index("atmosphere")
    alpha_col = header.index("alpha")
    beta_cols: dict[int, int] = {}
    for beta in (5, 10, 20):
        candidates = [
            col for col, name in enumerate(header)
            if name.lower().replace(" ", "") in
            {f"t{beta}_k", f"t{beta}(k)", f"t_beta_{beta}_k", f"t{beta}k"}
        ]
        if not candidates:
            candidates = [
                col for col, name in enumerate(header)
                if name and beta in [int(token) for token in re.findall(r"\d+", name)]
            ]
        if len(candidates) != 1:
            raise ValueError(f"Expected one Talpha column for beta={beta}; found {candidates}")
        beta_cols[beta] = candidates[0]
    data: dict[tuple[str, float], dict[int, float]] = {}
    max_required_col = max([atm_col, alpha_col, *beta_cols.values()])
    for row in rows[header_index + 1:]:
        if len(row) <= max_required_col:
            continue
        if row[atm_col] is None or row[alpha_col] is None:
            continue
        atmosphere = str(row[atm_col]).strip()
        if atmosphere not in ATMOSPHERES:
            continue
        alpha = round(float(row[alpha_col]), 1)
        if alpha not in set(ALPHAS):
            continue
        temperatures = {beta: float(row[col]) for beta, col in beta_cols.items() if row[col] is not None}
        if set(temperatures) != {5, 10, 20}:
            raise ValueError(f"{atmosphere}, alpha={alpha}: incomplete Talpha triplet")
        if not all(np.isfinite(value) and value > 0 for value in temperatures.values()):
            raise ValueError(f"{atmosphere}, alpha={alpha}: invalid temperature")
        data[(atmosphere, alpha)] = temperatures
    expected = {(atm, round(float(alpha), 1)) for atm in ATMOSPHERES for alpha in ALPHAS}
    if set(data) != expected:
        raise ValueError(f"Talpha coverage mismatch; missing={sorted(expected - set(data))}")
    return data


def transformed_response(model: str, beta: float, temperature: float) -> float:
    if model == "FWO":
        return float(np.log(beta))
    if model == "KAS":
        return float(np.log(beta / temperature**2))
    if model == "Starink":
        return float(np.log(beta / temperature**1.92))
    raise KeyError(model)


def regressions(talpha: dict[tuple[str, float], dict[int, float]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    critical = float(student_t.ppf(0.975, 1))
    for atmosphere in ATMOSPHERES:
        for alpha in ALPHAS:
            temperatures = np.array(
                [talpha[(atmosphere, round(float(alpha), 1))][int(beta)] for beta in BETAS],
                dtype=float,
            )
            x = 1.0 / temperatures
            design = np.column_stack([np.ones(3), x])
            for model in MODELS:
                y = np.array([
                    transformed_response(model, beta, temperature)
                    for beta, temperature in zip(BETAS, temperatures)
                ])
                intercept, slope = np.linalg.lstsq(design, y, rcond=None)[0]
                fitted = intercept + slope * x
                residual = y - fitted
                sse = float(residual @ residual)
                sst = float(((y - y.mean()) ** 2).sum())
                dof = 1
                se_slope = math.sqrt((sse / dof) / float(((x - x.mean()) ** 2).sum()))
                factor = MODEL_FACTORS[model]
                ea = -float(slope) * R_KJ_MOL_K / factor
                se_ea = se_slope * R_KJ_MOL_K / factor
                rows.append({
                    "atmosphere": atmosphere,
                    "alpha": float(alpha),
                    "model": model,
                    "T5_K": float(temperatures[0]),
                    "T10_K": float(temperatures[1]),
                    "T20_K": float(temperatures[2]),
                    "slope": float(slope),
                    "intercept": float(intercept),
                    "R2": 1.0 - sse / sst,
                    "SE_slope": se_slope,
                    "Ea_kJ_mol": ea,
                    "SE_Ea_kJ_mol": se_ea,
                    "t_critical_95": critical,
                    "CI95_lower_kJ_mol": ea - critical * se_ea,
                    "CI95_upper_kJ_mol": ea + critical * se_ea,
                    "CI95_half_width_kJ_mol": critical * se_ea,
                    "n": 3,
                    "dof": 1,
                    "region": "late_residue_oxidation" if atmosphere == "Air" and np.isclose(alpha, 0.8) else "main_region",
                })
    frame = pd.DataFrame(rows)
    if len(frame) != 42 or not (frame["dof"] == 1).all():
        raise AssertionError("Expected 42 fits with df=1")
    air_late = frame[(frame.atmosphere == "Air") & np.isclose(frame.alpha, 0.8) & (frame.model == "KAS")].iloc[0]
    if not (round(float(air_late.Ea_kJ_mol), 1) == 258.9 and
            round(float(air_late.SE_Ea_kJ_mol), 1) == 34.9 and
            round(float(air_late.CI95_half_width_kJ_mol), 1) == 443.7):
        raise AssertionError("Air alpha=0.8 KAS acceptance check failed")
    return frame


def plot_main_figure(frame: pd.DataFrame, output_dir: Path) -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9.0,
        "axes.labelsize": 10.0,
        "axes.titlesize": 10.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.1,
        "axes.linewidth": 0.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    blue = "#1F77B4"
    red = "#C9332B"
    figure = plt.figure(figsize=(7.35, 3.85), constrained_layout=False)
    grid = figure.add_gridspec(2, 2, width_ratios=[1.0, 1.0], height_ratios=[0.28, 1.0],
                              left=0.09, right=0.985, bottom=0.17, top=0.90,
                              wspace=0.25, hspace=0.07)
    ax_n2 = figure.add_subplot(grid[:, 0])
    ax_air_top = figure.add_subplot(grid[0, 1])
    ax_air = figure.add_subplot(grid[1, 1], sharex=ax_air_top)

    def arrays(atmosphere: str):
        subset = frame[frame.atmosphere == atmosphere]
        kas = subset[subset.model == "KAS"].sort_values("alpha")
        pivot = subset.pivot(index="alpha", columns="model", values="Ea_kJ_mol").sort_index()
        return kas, pivot.min(axis=1), pivot.max(axis=1)

    kas_n2, low_n2, high_n2 = arrays("N2")
    x_n2 = kas_n2.alpha.to_numpy()
    ax_n2.fill_between(x_n2, low_n2.to_numpy(), high_n2.to_numpy(), color=blue, alpha=0.16, linewidth=0)
    ax_n2.errorbar(x_n2, kas_n2.Ea_kJ_mol, yerr=kas_n2.SE_Ea_kJ_mol,
                   color=blue, marker="o", ms=4.6, lw=1.6, capsize=2.5, capthick=1.0,
                   ecolor=blue, zorder=3)

    kas_air, low_air, high_air = arrays("Air")
    main = kas_air[kas_air.region == "main_region"]
    late = kas_air[kas_air.region == "late_residue_oxidation"]
    main_idx = main.alpha.to_numpy()
    ax_air.fill_between(main_idx, low_air.loc[main_idx].to_numpy(), high_air.loc[main_idx].to_numpy(),
                        color=red, alpha=0.16, linewidth=0)
    ax_air.errorbar(main.alpha, main.Ea_kJ_mol, yerr=main.SE_Ea_kJ_mol,
                    color=red, marker="o", ms=4.6, lw=1.6, capsize=2.5, capthick=1.0,
                    ecolor=red, zorder=3)
    late_alpha = float(late.alpha.iloc[0])
    ax_air_top.fill_between([late_alpha - 0.014, late_alpha + 0.014],
                            [float(low_air.loc[late_alpha])] * 2,
                            [float(high_air.loc[late_alpha])] * 2,
                            color=red, alpha=0.16, linewidth=0)
    ax_air_top.errorbar(late.alpha, late.Ea_kJ_mol, yerr=late.SE_Ea_kJ_mol,
                        color=red, marker="D", mfc="white", mec=red, mew=1.5,
                        ms=5.4, lw=0, capsize=2.5, capthick=1.0, ecolor=red, zorder=3)

    for axis in (ax_n2, ax_air, ax_air_top):
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(direction="out", width=0.8, length=3.5)
        axis.grid(axis="y", color="#D9D9D9", linewidth=0.55, alpha=0.65)
        axis.set_xlim(0.17, 0.83)
    ax_n2.set_ylim(35, 138)
    ax_n2.set_yticks([40, 60, 80, 100, 120])
    ax_air.set_ylim(23, 103)
    ax_air.set_yticks([30, 50, 70, 90])
    ax_air_top.set_ylim(218, 300)
    ax_air_top.set_yticks([240, 280])
    ax_air_top.tick_params(axis="x", which="both", bottom=False, labelbottom=False)

    # Broken-axis marks, confined to the left spine of the Air panels.
    kwargs = dict(transform=ax_air_top.transAxes, color="black", clip_on=False, lw=0.9)
    ax_air_top.plot((-0.014, 0.014), (-0.035, 0.035), **kwargs)
    kwargs.update(transform=ax_air.transAxes)
    ax_air.plot((-0.014, 0.014), (0.965, 1.035), **kwargs)

    ax_n2.set_xlabel(r"Conversion, $\alpha$")
    ax_air.set_xlabel(r"Conversion, $\alpha$")
    ax_n2.set_ylabel(r"Apparent activation energy, $E_{\alpha}$ (kJ mol$^{-1}$)")
    ax_air.set_ylabel(r"Apparent activation energy, $E_{\alpha}$ (kJ mol$^{-1}$)")
    ax_n2.set_xticks(ALPHAS)
    ax_air.set_xticks(ALPHAS)
    ax_n2.text(-0.16, 1.02, "(a)", transform=ax_n2.transAxes, fontweight="bold", fontsize=11, va="bottom")
    ax_air_top.text(-0.16, 1.05, "(b)", transform=ax_air_top.transAxes, fontweight="bold", fontsize=11, va="bottom")
    ax_n2.set_title(r"Pyrolysis (N$_2$)", pad=7, fontweight="semibold")
    ax_air_top.set_title("Combustion (Air)", pad=6, fontweight="semibold")
    ax_air_top.annotate(r"late residue oxidation ($\alpha=0.8$)",
                        xy=(late_alpha, float(late.Ea_kJ_mol.iloc[0])), xytext=(0.48, 0.78),
                        textcoords="axes fraction", ha="center", va="center", fontsize=7.8,
                        arrowprops=dict(arrowstyle="-", color="#555555", lw=0.75))

    legend_handles = [
        Line2D([0], [0], color="#444444", marker="o", lw=1.4, markersize=4.4,
               label="KAS estimate +/- regression SE"),
        Patch(facecolor="#777777", alpha=0.18, edgecolor="none",
              label="FWO/KAS/Starink min-max spread"),
        Line2D([0], [0], color=red, marker="D", mfc="white", mec=red, mew=1.4,
               lw=0, markersize=5.2, label="Air late residue oxidation"),
    ]
    figure.legend(handles=legend_handles, loc="lower center", bbox_to_anchor=(0.54, 0.008),
                  ncol=3, frameon=False, handlelength=2.0, columnspacing=1.5)
    output_dir.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_dir / "Figure4_apparent_activation_energy.pdf", dpi=600)
    figure.savefig(output_dir / "Figure4_apparent_activation_energy.png", dpi=600)
    plt.close(figure)


def write_outputs(source: Path, frame: pd.DataFrame, output_dir: Path) -> None:
    frame.to_csv(output_dir / "Figure4_Regression_Diagnostics.csv", index=False, float_format="%.15g")
    summary = []
    for atmosphere in ATMOSPHERES:
        subset = frame[frame.atmosphere == atmosphere]
        pivot = subset.pivot(index="alpha", columns="model", values="Ea_kJ_mol")
        kas = subset[subset.model == "KAS"].set_index("alpha")
        for alpha in ALPHAS:
            summary.append({
                "atmosphere": atmosphere,
                "alpha": float(alpha),
                "KAS_Ea_kJ_mol": float(kas.loc[alpha, "Ea_kJ_mol"]),
                "KAS_SE_kJ_mol": float(kas.loc[alpha, "SE_Ea_kJ_mol"]),
                "KAS_CI95_lower_kJ_mol": float(kas.loc[alpha, "CI95_lower_kJ_mol"]),
                "KAS_CI95_upper_kJ_mol": float(kas.loc[alpha, "CI95_upper_kJ_mol"]),
                "KAS_CI95_half_width_kJ_mol": float(kas.loc[alpha, "CI95_half_width_kJ_mol"]),
                "method_min_kJ_mol": float(pivot.loc[alpha].min()),
                "method_max_kJ_mol": float(pivot.loc[alpha].max()),
                "method_range_kJ_mol": float(pivot.loc[alpha].max() - pivot.loc[alpha].min()),
                "n": 3,
                "dof": 1,
                "region": str(kas.loc[alpha, "region"]),
            })
    pd.DataFrame(summary).to_csv(output_dir / "Figure4_Plot_Data.csv", index=False, float_format="%.15g")
    caption = (
        "Figure 2. Conversion-dependent apparent activation energy for Arab Light crude under "
        "(a) N2 pyrolysis and (b) air combustion. Symbols and lines show KAS estimates; error bars "
        "are conditional regression standard errors from the three-heating-rate fits (n=3, df=1). "
        "Shaded envelopes show the min-max spread across FWO, KAS, and Starink estimates and are not "
        "confidence intervals or independent validation. The Air alpha=0.8 point is plotted separately "
        "because it represents late residue oxidation rather than the alpha=0.2-0.7 main conversion "
        "region. For this point, KAS E_alpha = 258.9 +/- 34.9 kJ mol^-1 (SE); because df=1, the "
        "two-sided 95% CI half-width is 443.7 kJ mol^-1 (t_0.975,1=12.706). It is therefore interpreted "
        "qualitatively. The reported regression uncertainty is conditional on the extracted T_alpha "
        "values and does not include experimental repeatability, instrument, or preprocessing uncertainty."
    )
    (output_dir / "Figure4_caption.txt").write_text(caption + "\n", encoding="utf-8")
    protocol = {
        "figure": "Figure4_apparent_activation_energy",
        "source_file": source.name,
        "source_sha256": sha256(source),
        "input_sheet": "Kinetic_Talpha",
        "primary_estimator": "KAS",
        "error_bars": "ordinary least-squares regression SE(Ea), n=3, df=1",
        "method_envelope": "min-max of FWO, KAS, and Starink point estimates; not a confidence interval",
        "air_alpha_0_8": {
            "interpretation": "late residue oxidation; separate from the main conversion region",
            "KAS_Ea_kJ_mol": 258.915581925267,
            "KAS_SE_kJ_mol": 34.9221775527547,
            "t_critical_95_df1": float(student_t.ppf(0.975, 1)),
            "CI95_half_width_kJ_mol": 443.715443932037,
        },
        "limitations": [
            "FWO/KAS/Starink agreement is internal method consistency, not independent validation.",
            "Regression uncertainty is conditional on extracted Talpha values.",
            "With three heating rates, every regression has one residual degree of freedom.",
        ],
    }
    (output_dir / "Figure4_protocol.json").write_text(json.dumps(protocol, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    print("NOTE: kinetics_regression_core.py is the shared regression library.")
    print("The current main Figure 4 build is 03_CODE/04_build_figure4_activation_energy.py, which")
    print("includes the 95% CI overlay and broken-axis Air treatment. This")
    print("legacy entrypoint writes a superseded figure design for reference only.")
    args = parse_args()
    source = resolve_source(args.source)
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    talpha = load_talpha(source)
    frame = regressions(talpha)
    plot_main_figure(frame, output_dir)
    write_outputs(source, frame, output_dir)
    print(json.dumps({
        "source": str(source),
        "source_sha256": sha256(source),
        "output_dir": str(output_dir),
        "fits": len(frame),
    }, indent=2))


if __name__ == "__main__":
    main()
