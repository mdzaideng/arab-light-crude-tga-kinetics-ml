"""Reproduce the Arab Light TGA complete-heating-rate-holdout analysis.

The script reads the withheld cleaned workbook from ``data/private`` and
writes machine-readable results to ``results/ml`` plus publication-style
figures to ``figures``. The input workbook is intentionally not distributed
in this pre-acceptance repository release.
"""

from __future__ import annotations

import argparse
import copy
import os
import platform
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "alc-ml-mpl-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = ROOT / "data" / "private" / "arab_light_TGA_cleaned_ML_ready_v2.xlsx"
DEFAULT_RESULTS = ROOT / "results" / "ml"
DEFAULT_MAIN_FIGURES = ROOT / "figures" / "main"
DEFAULT_SUPP_FIGURES = ROOT / "figures" / "supplementary"

RANDOM_STATE = 42
FEATURES = ["temp_K", "beta"]
TARGET = "mass_pct"
ATMOSPHERES = ["N2", "Air"]
MODEL_NAMES = ["RF", "GBR", "SVR", "MLR", "PLSR"]
LORO_CASES = [
    ("N2", [5, 20], 10, "Intermediate-rate holdout"),
    ("N2", [5, 10], 20, "Upper-bound holdout"),
    ("N2", [10, 20], 5, "Lower-bound holdout"),
    ("Air", [5, 20], 10, "Intermediate-rate holdout"),
    ("Air", [5, 10], 20, "Upper-bound holdout"),
    ("Air", [10, 20], 5, "Lower-bound holdout"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--main-figures-dir", type=Path, default=DEFAULT_MAIN_FIGURES)
    parser.add_argument("--supp-figures-dir", type=Path, default=DEFAULT_SUPP_FIGURES)
    return parser.parse_args()


def make_models(feature_count: int = 2):
    return {
        "RF": (
            RandomForestRegressor(
                n_estimators=100, max_depth=10, random_state=RANDOM_STATE, n_jobs=-1
            ),
            False,
        ),
        "GBR": (
            GradientBoostingRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                random_state=RANDOM_STATE,
            ),
            False,
        ),
        "SVR": (SVR(kernel="rbf", C=10, gamma=0.01, epsilon=0.01), True),
        "MLR": (LinearRegression(), False),
        "PLSR": (PLSRegression(n_components=min(2, feature_count), scale=True), False),
    }


def fit_predict(model, x_train, y_train, x_test, scale: bool = False):
    if scale:
        scaler = StandardScaler()
        x_train = scaler.fit_transform(x_train)
        x_test = scaler.transform(x_test)
    model.fit(x_train, y_train)
    return np.ravel(model.predict(x_test))


def score(y_true, y_pred):
    return {
        "R2": r2_score(y_true, y_pred),
        "RMSEP": np.sqrt(mean_squared_error(y_true, y_pred)),
        "MAE": mean_absolute_error(y_true, y_pred),
    }


def load_data(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {path}\nSee data/README.md for the expected private files."
        )
    frame = pd.read_excel(path, sheet_name="ML_Master")
    required = {"curve_id", "atmosphere", "beta", "temp_K", "temp_C", "mass_pct", "alpha"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"ML_Master is missing required columns: {missing}")
    frame = frame[["curve_id", "atmosphere", "beta", "temp_K", "temp_C", "mass_pct", "alpha"]].copy()
    counts = frame.groupby(["atmosphere", "beta"]).size()
    expected = pd.MultiIndex.from_product([ATMOSPHERES, [5, 10, 20]])
    if not expected.isin(counts.index).all():
        raise ValueError("The dataset must contain N2 and Air curves at 5, 10, and 20 C/min.")
    return frame


def subset(frame, atmosphere, betas, features):
    out = frame[(frame.atmosphere == atmosphere) & frame.beta.isin(betas)].copy()
    out = out.sort_values(["beta", "temp_K"])
    return out, out[features].to_numpy(), out[TARGET].to_numpy()


def aggregate(frame: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    summary = frame.groupby(groups)[["R2", "RMSEP", "MAE"]].agg(["mean", "std", "min", "max"])
    summary.columns = ["_".join(item) for item in summary.columns]
    return summary.reset_index()


def complete_holdouts(frame):
    rows = []
    predictions = {}
    for atmosphere, train_betas, test_beta, holdout_type in LORO_CASES:
        _, x_train, y_train = subset(frame, atmosphere, train_betas, FEATURES)
        test, x_test, y_test = subset(frame, atmosphere, [test_beta], FEATURES)
        for name, (model, scale) in make_models().items():
            pred = fit_predict(copy.deepcopy(model), x_train.copy(), y_train, x_test.copy(), scale)
            rows.append(
                {
                    "Atmosphere": atmosphere,
                    "Train_betas": ",".join(map(str, train_betas)),
                    "Test_beta": test_beta,
                    "Holdout_type": holdout_type,
                    "Model": name,
                    **score(y_test, pred),
                }
            )
            predictions[(atmosphere, tuple(train_betas), test_beta, name)] = (test.copy(), pred)
    results = pd.DataFrame(rows)
    summary = aggregate(results, ["Model"])
    summary["Model"] = pd.Categorical(summary.Model, MODEL_NAMES, ordered=True)
    summary = summary.sort_values("Model").reset_index(drop=True)
    return results, summary, predictions


def random_benchmark(frame):
    rows = []
    for atmosphere in ATMOSPHERES:
        current = frame[frame.atmosphere == atmosphere]
        x = current[FEATURES].to_numpy()
        y = current[TARGET].to_numpy()
        x_train, x_test, y_train, y_test = train_test_split(
            x, y, test_size=0.20, random_state=RANDOM_STATE
        )
        for name, (model, scale) in make_models().items():
            pred = fit_predict(copy.deepcopy(model), x_train.copy(), y_train, x_test.copy(), scale)
            rows.append({"Atmosphere": atmosphere, "Model": name, **score(y_test, pred)})
    results = pd.DataFrame(rows)
    summary = aggregate(results, ["Model"])
    summary["Model"] = pd.Categorical(summary.Model, MODEL_NAMES, ordered=True)
    summary = summary.sort_values("Model").reset_index(drop=True)
    return results, summary


def feature_ablation(frame):
    rows = []
    for atmosphere, train_betas, test_beta, holdout_type in LORO_CASES:
        for label, features in [("T only", ["temp_K"]), ("T + beta", FEATURES)]:
            _, x_train, y_train = subset(frame, atmosphere, train_betas, features)
            _, x_test, y_test = subset(frame, atmosphere, [test_beta], features)
            for name in ["RF", "GBR"]:
                model, scale = make_models(len(features))[name]
                pred = fit_predict(copy.deepcopy(model), x_train, y_train, x_test, scale)
                rows.append(
                    {
                        "Atmosphere": atmosphere,
                        "Train_betas": ",".join(map(str, train_betas)),
                        "Test_beta": test_beta,
                        "Holdout_type": holdout_type,
                        "Model": name,
                        "Feature_set": label,
                        **score(y_test, pred),
                    }
                )
    results = pd.DataFrame(rows)
    return results, aggregate(results, ["Model", "Feature_set"])


def deterministic_baselines(frame):
    rows = []
    for atmosphere, train_betas, test_beta, holdout_type in LORO_CASES:
        test = frame[(frame.atmosphere == atmosphere) & (frame.beta == test_beta)].sort_values("temp_K")
        temperatures = test.temp_K.to_numpy()
        y_test = test[TARGET].to_numpy()
        curves = {}
        for beta in train_betas:
            curve = frame[(frame.atmosphere == atmosphere) & (frame.beta == beta)].sort_values("temp_K")
            curves[beta] = np.interp(temperatures, curve.temp_K, curve[TARGET])

        nearest_beta = min(train_betas, key=lambda value: abs(value - test_beta))
        low, high = sorted(train_betas)
        weight = (test_beta - low) / (high - low)
        predictions = {
            "Nearest-rate": curves[nearest_beta],
            "Linear-beta": curves[low] + weight * (curves[high] - curves[low]),
        }
        for baseline, prediction in predictions.items():
            rows.append(
                {
                    "Atmosphere": atmosphere,
                    "Train_betas": ",".join(map(str, train_betas)),
                    "Test_beta": test_beta,
                    "Holdout_type": holdout_type,
                    "Baseline": baseline,
                    **score(y_test, prediction),
                }
            )
    results = pd.DataFrame(rows)
    return results, aggregate(results, ["Baseline"])


def rf_sensitivity(frame):
    representative = []
    all_cases = []
    for n_estimators in [10, 30, 100]:
        _, x_train, y_train = subset(frame, "N2", [5, 20], FEATURES)
        _, x_test, y_test = subset(frame, "N2", [10], FEATURES)
        for depth in range(1, 11):
            model = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=depth,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            )
            model.fit(x_train, y_train)
            representative.append(
                {
                    "n_estimators": n_estimators,
                    "max_depth": depth,
                    "Train_R2": r2_score(y_train, model.predict(x_train)),
                    "Test_R2": r2_score(y_test, model.predict(x_test)),
                }
            )

    for depth in range(1, 11):
        for atmosphere, train_betas, test_beta, _ in LORO_CASES:
            _, x_train, y_train = subset(frame, atmosphere, train_betas, FEATURES)
            _, x_test, y_test = subset(frame, atmosphere, [test_beta], FEATURES)
            model = RandomForestRegressor(
                n_estimators=100, max_depth=depth, random_state=RANDOM_STATE, n_jobs=-1
            )
            model.fit(x_train, y_train)
            pred = model.predict(x_test)
            all_cases.append({"max_depth": depth, **score(y_test, pred)})
    detail = pd.DataFrame(all_cases)
    summary = detail.groupby("max_depth").agg(
        Mean_R2=("R2", "mean"),
        SD_R2=("R2", "std"),
        Mean_RMSEP=("RMSEP", "mean"),
        SD_RMSEP=("RMSEP", "std"),
    ).reset_index()
    return pd.DataFrame(representative), summary


def gbr_sensitivity(frame):
    _, x_train, y_train = subset(frame, "N2", [5, 20], FEATURES)
    _, x_test, y_test = subset(frame, "N2", [10], FEATURES)
    rows = []
    n_values = [1, 2, 3, 5, 10, 20, 30, 50, 100]
    for depth in range(1, 8):
        for n_estimators in n_values:
            model = GradientBoostingRegressor(
                n_estimators=n_estimators,
                max_depth=depth,
                learning_rate=0.1,
                random_state=RANDOM_STATE,
            )
            model.fit(x_train, y_train)
            rows.append(
                {
                    "max_depth": depth,
                    "n_estimators": n_estimators,
                    "Train_R2": r2_score(y_train, model.predict(x_train)),
                    "Test_R2": r2_score(y_test, model.predict(x_test)),
                }
            )
    return pd.DataFrame(rows)


def linear_equivalence(holdout_results):
    wide = holdout_results[holdout_results.Model.isin(["MLR", "PLSR"])].pivot_table(
        index=["Atmosphere", "Train_betas", "Test_beta"], columns="Model", values=["R2", "RMSEP", "MAE"]
    )
    return pd.DataFrame(
        {
            "Metric": ["R2", "RMSEP", "MAE"],
            "Maximum_absolute_difference": [
                np.max(np.abs(wide[metric]["MLR"] - wide[metric]["PLSR"]))
                for metric in ["R2", "RMSEP", "MAE"]
            ],
        }
    )


def plot_holdouts(predictions, destination):
    fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.3), sharey=True)
    for ax, panel, (atmosphere, train_betas, test_beta, _) in zip(
        axes.ravel(), "abcdef", LORO_CASES
    ):
        test, rf_pred = predictions[(atmosphere, tuple(train_betas), test_beta, "RF")]
        _, gbr_pred = predictions[(atmosphere, tuple(train_betas), test_beta, "GBR")]
        y = test[TARGET].to_numpy()
        ax.plot(test.temp_C, y, lw=2.1, label="Experimental")
        ax.plot(test.temp_C, rf_pred, "--", lw=1.6, label=f"RF, R2={r2_score(y, rf_pred):.4f}")
        ax.plot(test.temp_C, gbr_pred, ":", lw=1.9, label=f"GBR, R2={r2_score(y, gbr_pred):.4f}")
        ax.set_title(f"{atmosphere}: train beta={train_betas}; test beta={test_beta}")
        ax.set_xlabel("Temperature (C)")
        ax.set_ylabel("Remaining mass (%)")
        ax.grid(alpha=0.25, linestyle="--")
        ax.legend(loc="best", fontsize=8)
        ax.text(0.02, 0.96, f"({panel})", transform=ax.transAxes, va="top", fontweight="bold")
    fig.tight_layout()
    fig.savefig(destination, dpi=500, bbox_inches="tight")
    plt.close(fig)


def plot_model_summary(results, destination):
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    x = np.arange(len(MODEL_NAMES))
    for ax, metric, title in zip(axes, ["R2", "RMSEP"], ["Coefficient of determination", "Prediction error"]):
        for index, model in enumerate(MODEL_NAMES):
            values = results[results.Model == model][metric].to_numpy()
            ax.scatter(np.full(len(values), index) + np.linspace(-0.09, 0.09, len(values)), values, s=28, alpha=0.7)
            ax.errorbar(index, values.mean(), yerr=values.std(ddof=1), fmt="s", capsize=4)
        ax.set_xticks(x, MODEL_NAMES)
        ax.grid(axis="y", alpha=0.25, linestyle="--")
        ax.set_title(title)
        ax.set_ylabel(metric if metric == "R2" else "RMSEP (mass %)")
    fig.tight_layout()
    fig.savefig(destination, dpi=500, bbox_inches="tight")
    plt.close(fig)


def plot_atmosphere_metrics(results, destination):
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), sharex=True)
    labels = {10: "Intermediate 10", 20: "Upper 20", 5: "Lower 5"}
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    for column, atmosphere in enumerate(ATMOSPHERES):
        current = results[results.Atmosphere == atmosphere]
        for row, metric in enumerate(["R2", "RMSEP"]):
            ax = axes[row, column]
            for color, test_beta in zip(colors, [10, 20, 5]):
                values = current[current.Test_beta == test_beta].set_index("Model").reindex(MODEL_NAMES)
                ax.plot(MODEL_NAMES, values[metric], marker="o", lw=1.5, color=color, label=labels[test_beta])
            ax.set_title(f"{atmosphere}: {metric}")
            ax.set_ylabel(metric if metric == "R2" else "RMSEP (mass %)")
            ax.grid(alpha=0.25, linestyle="--")
            if row == 0:
                ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(destination, dpi=400, bbox_inches="tight")
    plt.close(fig)


def plot_rf_sensitivity(representative, summary, destination):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for n_estimators, current in representative.groupby("n_estimators"):
        axes[0].plot(current.max_depth, current.Test_R2, marker="o", label=f"{n_estimators} trees")
    axes[0].set_title("Representative N2 intermediate holdout")
    axes[0].set_xlabel("Maximum depth")
    axes[0].set_ylabel("Test R2")
    axes[0].legend(frameon=False)
    axes[1].errorbar(summary.max_depth, summary.Mean_R2, yerr=summary.SD_R2, marker="o", capsize=3)
    axes[1].axvline(10, color="0.4", linestyle="--", label="Prespecified depth")
    axes[1].set_title("Six-holdout mean +/- SD")
    axes[1].set_xlabel("Maximum depth")
    axes[1].set_ylabel("R2")
    for ax in axes:
        ax.grid(alpha=0.25, linestyle="--")
    fig.tight_layout()
    fig.savefig(destination, dpi=400, bbox_inches="tight")
    plt.close(fig)


def plot_gbr_sensitivity(results, destination):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for depth, current in results.groupby("max_depth"):
        axes[0].plot(current.n_estimators, current.Test_R2, label=f"depth {depth}")
    current = results[results.max_depth == 4]
    axes[1].plot(current.n_estimators, current.Train_R2, marker="o", label="Training")
    axes[1].plot(current.n_estimators, current.Test_R2, marker="s", label="Testing")
    axes[0].set_title("Representative N2 intermediate holdout")
    axes[1].set_title("Prespecified depth = 4")
    for ax in axes:
        ax.set_xlabel("Number of estimators")
        ax.set_ylabel("R2")
        ax.grid(alpha=0.25, linestyle="--")
        ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(destination, dpi=400, bbox_inches="tight")
    plt.close(fig)


def plot_ablation(results, destination):
    cases = [f"{atm}-{beta}" for atm, _, beta, _ in LORO_CASES]
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 7.5), sharex=True)
    x = np.arange(len(cases))
    for column, model in enumerate(["RF", "GBR"]):
        current = results[results.Model == model]
        for feature, style in [("T only", "o-"), ("T + beta", "s--")]:
            subset_rows = current[current.Feature_set == feature]
            axes[0, column].plot(x, subset_rows.R2, style, label=feature)
            axes[1, column].plot(x, subset_rows.RMSEP, style, label=feature)
        axes[0, column].set_title(model)
        axes[0, column].set_ylabel("R2")
        axes[1, column].set_ylabel("RMSEP (mass %)")
        axes[1, column].set_xticks(x, cases, rotation=35, ha="right")
        for ax in axes[:, column]:
            ax.grid(alpha=0.25, linestyle="--")
            ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(destination, dpi=400, bbox_inches="tight")
    plt.close(fig)


def plot_rf_grid(frame, destination):
    _, x_train, y_train = subset(frame, "N2", [5, 20], FEATURES)
    _, x_test, y_test = subset(frame, "N2", [10], FEATURES)
    n_values = [1, 2, 3, 5, 10, 20, 30, 50, 100]
    depths = range(1, 8)
    fig, axes = plt.subplots(3, 3, figsize=(12, 10))
    for ax, n_estimators in zip(axes.ravel(), n_values):
        train_scores, test_scores = [], []
        for depth in depths:
            model = RandomForestRegressor(n_estimators=n_estimators, max_depth=depth, random_state=RANDOM_STATE, n_jobs=-1)
            model.fit(x_train, y_train)
            train_scores.append(r2_score(y_train, model.predict(x_train)))
            test_scores.append(r2_score(y_test, model.predict(x_test)))
        ax.plot(depths, test_scores, "o-", label="Testing")
        ax.plot(depths, train_scores, "s-", label="Training")
        ax.set_title(f"n_estimators={n_estimators}")
        ax.grid(alpha=0.25, linestyle="--")
    axes[0, 0].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(destination, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_gbr_grid(results, destination):
    fig, axes = plt.subplots(3, 3, figsize=(12, 10))
    for ax, depth in zip(axes.ravel(), range(1, 8)):
        current = results[results.max_depth == depth]
        ax.plot(current.n_estimators, current.Test_R2, label="Testing")
        ax.plot(current.n_estimators, current.Train_R2, label="Training")
        ax.set_title(f"max_depth={depth}")
        ax.grid(alpha=0.25, linestyle="--")
    for ax in axes.ravel()[7:]:
        ax.set_visible(False)
    axes[0, 0].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(destination, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    for directory in [args.results_dir, args.main_figures_dir, args.supp_figures_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    frame = load_data(args.data)

    holdout, holdout_summary, predictions = complete_holdouts(frame)
    random_results, random_summary = random_benchmark(frame)
    ablation, ablation_summary = feature_ablation(frame)
    baselines, baseline_summary = deterministic_baselines(frame)
    rf_representative, rf_summary = rf_sensitivity(frame)
    gbr_results = gbr_sensitivity(frame)
    equivalence = linear_equivalence(holdout)

    exports = {
        "Holdout_Results.csv": holdout,
        "Holdout_Summary.csv": holdout_summary,
        "Random_Benchmark.csv": random_results,
        "Random_Summary.csv": random_summary,
        "Ablation_Results.csv": ablation,
        "Ablation_Summary.csv": ablation_summary,
        "Deterministic_Baseline_Results.csv": baselines,
        "Deterministic_Baseline_Summary.csv": baseline_summary,
        "RF_Representative_Sensitivity.csv": rf_representative,
        "RF_Six_Holdout_Depth_Summary.csv": rf_summary,
        "GBR_Representative_Sensitivity.csv": gbr_results,
        "MLR_PLSR_Equivalence_Audit.csv": equivalence,
    }
    for filename, table in exports.items():
        table.to_csv(args.results_dir / filename, index=False)

    environment = pd.DataFrame(
        [
            ("Python", platform.python_version()),
            ("NumPy", np.__version__),
            ("pandas", pd.__version__),
            ("scikit-learn", sklearn.__version__),
            ("SciPy", scipy.__version__),
            ("Matplotlib", matplotlib.__version__),
            ("Random seed", RANDOM_STATE),
        ],
        columns=["Component", "Version_or_value"],
    )
    environment.to_csv(args.results_dir / "Software_Environment.csv", index=False)

    plot_holdouts(predictions, args.main_figures_dir / "Figure6_ML_holdout_predictions_reproduced.png")
    plot_model_summary(holdout, args.main_figures_dir / "Figure7_ML_model_performance_reproduced.png")
    plot_atmosphere_metrics(holdout, args.main_figures_dir / "Figure8_ML_atmosphere_resolved_performance_reproduced.png")
    plot_rf_sensitivity(rf_representative, rf_summary, args.supp_figures_dir / "FigureS3_RF_posthoc_sensitivity_reproduced.png")
    plot_gbr_sensitivity(gbr_results, args.supp_figures_dir / "FigureS4_GBR_posthoc_sensitivity_reproduced.png")
    plot_ablation(ablation, args.supp_figures_dir / "FigureS5_feature_ablation_reproduced.png")
    plot_rf_grid(frame, args.supp_figures_dir / "FigureS6_RF_sensitivity_grid_reproduced.png")
    plot_gbr_grid(gbr_results, args.supp_figures_dir / "FigureS7_GBR_sensitivity_grid_reproduced.png")

    print(f"PASS: wrote {len(exports) + 1} ML result tables")
    print(baseline_summary.to_string(index=False))


if __name__ == "__main__":
    main()
