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
from alc_core import publication_font_rc
from matplotlib.lines import Line2D
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
COLORS = [plt.colormaps["viridis"](value) for value in np.linspace(0.05, 0.95, len(ALPHAS))]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild corrected Figure S1 regression diagnostics from Kinetic_Talpha."
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Input XLSX. If omitted, a canonical source filename is searched beside this script or in ../Data.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPOSITORY_ROOT / "figures" / "supplementary",
        help="Output directory (default: figures/supplementary in the repository).",
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
        "No source workbook found in data/private or beside the script. Pass --source or provide: "
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
    column_atmosphere = header.index("atmosphere")
    column_alpha = header.index("alpha")
    beta_columns: dict[int, int] = {}
    for beta in (5, 10, 20):
        candidates = [
            column
            for column, name in enumerate(header)
            if name.lower().replace(" ", "")
            in {f"t{beta}_k", f"t{beta}(k)", f"t_beta_{beta}_k", f"t{beta}k"}
        ]
        if not candidates:
            candidates = [
                column
                for column, name in enumerate(header)
                if name and beta in [int(token) for token in re.findall(r"\d+", name)]
            ]
        if len(candidates) != 1:
            raise ValueError(
                f"Expected one temperature column for beta={beta}; found {candidates}: {header}"
            )
        beta_columns[beta] = candidates[0]

    data: dict[tuple[str, float], dict[int, float]] = {}
    max_required_col = max([column_atmosphere, column_alpha, *beta_columns.values()])
    for row in rows[header_index + 1 :]:
        if len(row) <= max_required_col:
            continue
        if row[column_atmosphere] is None or row[column_alpha] is None:
            continue
        atmosphere = str(row[column_atmosphere]).strip()
        if atmosphere not in ATMOSPHERES:
            continue
        alpha = round(float(row[column_alpha]), 1)
        if alpha not in {round(float(value), 1) for value in ALPHAS}:
            continue
        temperatures = {
            beta: float(row[column])
            for beta, column in beta_columns.items()
            if row[column] is not None
        }
        if set(temperatures) != {5, 10, 20}:
            raise ValueError(f"{atmosphere}, alpha={alpha}: incomplete heating-rate triplet.")
        if not all(np.isfinite(value) and value > 0 for value in temperatures.values()):
            raise ValueError(f"{atmosphere}, alpha={alpha}: invalid temperature.")
        data[(atmosphere, alpha)] = temperatures

    for atmosphere in ATMOSPHERES:
        present = {alpha for (atm, alpha) in data if atm == atmosphere}
        missing_alpha = sorted(set(ALPHAS) - present)
        if missing_alpha:
            raise ValueError(f"{atmosphere}: missing conversion levels {missing_alpha}")
    if len(data) != len(ATMOSPHERES) * len(ALPHAS):
        raise ValueError(f"Expected 14 atmosphere-alpha records; found {len(data)}")
    return data


def transformed_response(model: str, beta: float, temperature: float) -> float:
    if model == "FWO":
        return float(np.log(beta))
    if model == "KAS":
        return float(np.log(beta / temperature**2))
    if model == "Starink":
        return float(np.log(beta / temperature**1.92))
    raise KeyError(model)


def fit_ols(x: np.ndarray, y: np.ndarray) -> dict[str, object]:
    n = x.size
    design = np.column_stack([np.ones(n), x])
    intercept, slope = np.linalg.lstsq(design, y, rcond=None)[0]
    fitted = intercept + slope * x
    residuals = y - fitted
    dof = n - 2
    sse = float(residuals @ residuals)
    sst = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - sse / sst
    se_slope = math.sqrt((sse / dof) / float(((x - x.mean()) ** 2).sum()))
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "R2": float(r2),
        "SE_slope": float(se_slope),
        "dof": int(dof),
        "residuals": residuals,
    }


def calculate_regressions(
    talpha: dict[tuple[str, float], dict[int, float]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    talpha_rows: list[dict[str, object]] = []
    diagnostic_rows: list[dict[str, object]] = []
    critical = float(student_t.ppf(0.975, 1))
    for atmosphere in ATMOSPHERES:
        for alpha in ALPHAS:
            temperatures = np.array(
                [talpha[(atmosphere, round(float(alpha), 1))][int(beta)] for beta in BETAS],
                dtype=float,
            )
            talpha_rows.append(
                {
                    "atmosphere": atmosphere,
                    "alpha": float(alpha),
                    "T5_K": temperatures[0],
                    "T10_K": temperatures[1],
                    "T20_K": temperatures[2],
                    "T_mean_K": float(temperatures.mean()),
                    "n_heating_rates": 3,
                }
            )
            x = 1.0 / temperatures
            for model in MODELS:
                y = np.array(
                    [transformed_response(model, beta, temperature) for beta, temperature in zip(BETAS, temperatures)],
                    dtype=float,
                )
                fit = fit_ols(x, y)
                factor = MODEL_FACTORS[model]
                ea = -float(fit["slope"]) * R_KJ_MOL_K / factor
                se_ea = float(fit["SE_slope"]) * R_KJ_MOL_K / factor
                residuals = np.asarray(fit["residuals"])
                note = (
                    "late_air_residue_oxidation"
                    if atmosphere == "Air" and math.isclose(float(alpha), 0.8)
                    else "main_region"
                )
                diagnostic_rows.append(
                    {
                        "atmosphere": atmosphere,
                        "alpha": float(alpha),
                        "model": model,
                        "T5_K": temperatures[0],
                        "T10_K": temperatures[1],
                        "T20_K": temperatures[2],
                        "slope_x_1_per_K": fit["slope"],
                        "intercept": fit["intercept"],
                        "R2": fit["R2"],
                        "SE_slope": fit["SE_slope"],
                        "Ea_kJ_mol": ea,
                        "SE_Ea_kJ_mol": se_ea,
                        "t_critical_95": critical,
                        "CI95_half_width_Ea_kJ_mol": critical * se_ea,
                        "n": 3,
                        "dof": fit["dof"],
                        "residual_beta5": residuals[0],
                        "residual_beta10": residuals[1],
                        "residual_beta20": residuals[2],
                        "note": note,
                    }
                )

    talpha_frame = pd.DataFrame(talpha_rows)
    diagnostics = pd.DataFrame(diagnostic_rows)
    r2_matrix = (
        diagnostics.pivot(index=["atmosphere", "alpha"], columns="model", values="R2")
        .reset_index()[["atmosphere", "alpha", "FWO", "KAS", "Starink"]]
    )
    if len(diagnostics) != 42 or not (diagnostics.n.eq(3) & diagnostics.dof.eq(1)).all():
        raise AssertionError("Regression dimension or degrees-of-freedom check failed")
    acceptance = r2_matrix[(r2_matrix.atmosphere == "Air") & np.isclose(r2_matrix.alpha, 0.8)].iloc[0]
    expected = {"FWO": 0.9836, "KAS": 0.9821, "Starink": 0.9822}
    for model, value in expected.items():
        if round(float(acceptance[model]), 4) != value:
            raise AssertionError(f"Air alpha=0.8 {model} R2 mismatch: {acceptance[model]}")
    return talpha_frame, diagnostics, r2_matrix


def style_axis(axis: plt.Axes) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.tick_params(direction="out")


def method_range_text(diagnostics: pd.DataFrame, atmosphere: str, model: str) -> str:
    subset = diagnostics[(diagnostics.atmosphere == atmosphere) & (diagnostics.model == model)]
    if atmosphere == "N2":
        return rf"$R^2$: {subset.R2.min():.4f}-{subset.R2.max():.4f}"
    main = subset[subset.note == "main_region"]
    late = subset[subset.note == "late_air_residue_oxidation"].iloc[0]
    return (
        rf"$R^2$ ($\alpha$=0.2-0.7): {main.R2.min():.4f}-{main.R2.max():.4f}"
        + "\n"
        + rf"$\alpha$=0.8*: {late.R2:.4f}"
    )


def create_diagnostic_figure(
    atmosphere: str,
    talpha: dict[tuple[str, float], dict[int, float]],
    diagnostics: pd.DataFrame,
    output: Path,
) -> None:
    plt.rcParams.update(
        {
            **publication_font_rc(),
            "font.size": 9.5,
            "axes.labelsize": 10.5,
            "axes.titlesize": 11,
            "legend.fontsize": 8.2,
            "xtick.labelsize": 8.8,
            "ytick.labelsize": 8.8,
            "axes.linewidth": 0.9,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    y_labels = {
        "FWO": r"ln $\beta$",
        "KAS": r"ln($\beta/T^2$)",
        "Starink": r"ln($\beta/T^{1.92}$)",
    }
    figure, axes = plt.subplots(1, 3, figsize=(12.6, 4.65))
    for panel_index, (axis, model) in enumerate(zip(axes, MODELS)):
        for alpha_index, alpha in enumerate(ALPHAS):
            alpha_key = round(float(alpha), 1)
            temperatures = np.array(
                [talpha[(atmosphere, alpha_key)][int(beta)] for beta in BETAS], dtype=float
            )
            x_plot = 1000.0 / temperatures
            y = np.array(
                [transformed_response(model, beta, temperature) for beta, temperature in zip(BETAS, temperatures)]
            )
            row = diagnostics[
                (diagnostics.atmosphere == atmosphere)
                & np.isclose(diagnostics.alpha, alpha)
                & (diagnostics.model == model)
            ].iloc[0]
            line_x = np.linspace(float(x_plot.min()), float(x_plot.max()), 50)
            line_y = row.intercept + row.slope_x_1_per_K * (line_x / 1000.0)
            axis.plot(line_x, line_y, color=COLORS[alpha_index], lw=1.25, alpha=0.82)
            axis.scatter(
                x_plot,
                y,
                color=COLORS[alpha_index],
                s=25,
                edgecolor="white",
                linewidth=0.35,
                zorder=3,
            )
        axis.set_xlabel(r"$1000/T_\alpha$ (K$^{-1}$)")
        axis.set_ylabel(y_labels[model])
        axis.set_title(model, fontweight="bold", pad=27)
        axis.text(
            0.5,
            1.01,
            method_range_text(diagnostics, atmosphere, model),
            transform=axis.transAxes,
            ha="center",
            va="bottom",
            fontsize=7.6,
            linespacing=1.15,
        )
        axis.text(
            -0.13,
            1.09,
            f"({chr(97 + panel_index)})",
            transform=axis.transAxes,
            fontsize=11.5,
            fontweight="bold",
        )
        style_axis(axis)

    handles = []
    labels = []
    for index, alpha in enumerate(ALPHAS):
        flag = "*" if atmosphere == "Air" and math.isclose(float(alpha), 0.8) else ""
        handles.append(
            Line2D([0], [0], color=COLORS[index], marker="o", lw=1.25, ms=4.5)
        )
        labels.append(rf"$\alpha$ = {alpha:.1f}{flag}")
    figure.legend(
        handles,
        labels,
        loc="lower center",
        ncol=7,
        frameon=False,
        bbox_to_anchor=(0.5, 0.035 if atmosphere == "Air" else 0.02),
    )
    if atmosphere == "Air":
        figure.text(
            0.5,
            0.012,
            r"* Late residue oxidation; separate diagnostic, not pooled with the main $\alpha=0.2$-$0.7$ region.",
            ha="center",
            fontsize=7.5,
        )
    figure.subplots_adjust(left=0.075, right=0.985, top=0.82, bottom=0.20, wspace=0.30)
    stem = "FigureS1a_regression_N2" if atmosphere == "N2" else "FigureS1b_regression_Air"
    figure.savefig(output / f"{stem}.png", dpi=400, bbox_inches="tight")
    figure.savefig(output / f"{stem}.pdf", bbox_inches="tight", metadata={"Creator": "ALC Kinetics v6.1 reproducible pipeline", "CreationDate": None, "ModDate": None})
    plt.close(figure)


def main() -> None:
    args = parse_args()
    source = resolve_source(args.source)
    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    talpha = load_talpha(source)
    talpha_frame, diagnostics, r2_matrix = calculate_regressions(talpha)

    for atmosphere in ATMOSPHERES:
        create_diagnostic_figure(atmosphere, talpha, diagnostics, output)

    talpha_frame.to_csv(output / "FigureS1_Talpha_Inputs.csv", index=False)
    diagnostics.to_csv(output / "FigureS1_Regression_Diagnostics.csv", index=False)
    r2_matrix.to_csv(output / "FigureS1_R2_Matrix.csv", index=False)
    captions = {
        "FigureS1a": (
            "Isoconversional regression diagnostics for Arab Light crude oil under N2. Symbols denote the three "
            "heating rates (5, 10, and 20 degrees C/min), and lines are ordinary-least-squares fits for each conversion. "
            "The shared legend identifies conversion only; method-specific R2 ranges are stated above their respective "
            "panels, and exact values are reported in the regression audit table. Each fit contains n=3 observations "
            "with one residual degree of freedom; R2 therefore describes linear fit agreement but not parameter precision."
        ),
        "FigureS1b": (
            "Isoconversional regression diagnostics for Arab Light crude oil in Air. Symbols denote the three heating "
            "rates (5, 10, and 20 degrees C/min), and lines are ordinary-least-squares fits for each conversion. The "
            "shared legend identifies conversion only; method-specific R2 ranges and the separate alpha=0.8 values are "
            "stated above their respective panels. Alpha=0.8* represents late residue oxidation and is not pooled with "
            "the alpha=0.2-0.7 main region. Each fit contains n=3 observations with one residual degree of freedom; R2 "
            "does not quantify slope precision."
        ),
    }
    (output / "FigureS1_captions.txt").write_text(
        "Figure S1a. " + captions["FigureS1a"] + "\n\nFigure S1b. " + captions["FigureS1b"] + "\n",
        encoding="utf-8",
    )
    protocol = {
        "analysis_version": "Current Supplementary Figure S1 regression diagnostics",
        "source_file": source.name,
        "source_sha256": sha256(source),
        "direct_input_sheet": "Kinetic_Talpha",
        "heating_rates_C_min": BETAS.tolist(),
        "conversion_levels": ALPHAS.tolist(),
        "models": {
            "FWO": "y=ln(beta); Ea=-slope*R/1.052",
            "KAS": "y=ln(beta/T^2); Ea=-slope*R",
            "Starink": "y=ln(beta/T^1.92); Ea=-slope*R/1.0008",
        },
        "regression_x": "1/T_alpha in K^-1; figures display 1000/T_alpha",
        "regression": "ordinary least squares with intercept",
        "n_per_fit": 3,
        "residual_dof": 1,
        "uncertainty": (
            "Slope and Ea standard errors are conditional on the extracted T_alpha values. The 95% CI half-width "
            "uses t(0.975, df=1). Instrument, preprocessing, interpolation, and repeatability uncertainty are excluded."
        ),
        "r2_display_policy": (
            "Shared legends encode alpha only. Each method panel states its own R2 range; the Air alpha=0.8 value is "
            "shown separately. Exact four-decimal and full-precision values are retained in the audit outputs."
        ),
        "captions": captions,
    }
    (output / "FigureS1_protocol.json").write_text(
        json.dumps(protocol, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(r2_matrix.to_string(index=False, float_format=lambda value: f"{value:.6f}"))
    print("\nAir alpha=0.8 KAS 95% CI half-width (kJ/mol):", end=" ")
    value = diagnostics[
        (diagnostics.atmosphere == "Air")
        & np.isclose(diagnostics.alpha, 0.8)
        & (diagnostics.model == "KAS")
    ].CI95_half_width_Ea_kJ_mol.iloc[0]
    print(f"{value:.1f}")


if __name__ == "__main__":
    main()
