"""Export per-point holdout predictions and check them against the frozen metrics.

Per-point predictions were never archived; only metrics are in ``results/ml``.
This script re-runs the frozen complete-heating-rate holdouts with the code in
``run_ml_analysis.py`` (unchanged configurations, random_state = 42), writes the
per-point predictions (all five regressors and both deterministic baselines) and
the Figure S6 grid to ``--out`` (outside the repository, because the files
contain measured data), and writes the regeneration check against the archived
metric tables to ``results/ml/Holdout_regeneration_check.txt``.

Usage:
    python src/ml/export_holdout_predictions.py --out <directory>
"""

from __future__ import annotations

import argparse
import importlib.util
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("run_ml_analysis", ROOT / "src" / "ml" / "run_ml_analysis.py")
ml = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ml)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ml.DEFAULT_DATA)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    frame = ml.load_data(args.data)

    holdout, _, predictions = ml.complete_holdouts(frame)
    rows = []
    for (atm, train, test_beta, name), (test, pred) in predictions.items():
        for t_k, t_c, y, p in zip(test.temp_K, test.temp_C, test[ml.TARGET], pred):
            rows.append(dict(atmosphere=atm, train_betas_C_per_min=",".join(map(str, train)),
                             test_beta_C_per_min=test_beta, predictor=name, temp_K=t_k, temp_C=t_c,
                             measured_mass_pct=y, predicted_mass_pct=p))
    for atm, train, test_beta, _ in ml.LORO_CASES:
        test = frame[(frame.atmosphere == atm) & (frame.beta == test_beta)].sort_values("temp_K")
        temps = test.temp_K.to_numpy()
        curves = {}
        for beta in train:
            curve = frame[(frame.atmosphere == atm) & (frame.beta == beta)].sort_values("temp_K")
            curves[beta] = np.interp(temps, curve.temp_K, curve[ml.TARGET])
        nearest = min(train, key=lambda value: abs(value - test_beta))
        low, high = sorted(train)
        weight = (test_beta - low) / (high - low)
        for name, pred in {"Nearest-rate baseline": curves[nearest],
                           "Linear-beta baseline": curves[low] + weight * (curves[high] - curves[low])}.items():
            for t_k, t_c, y, p in zip(temps, test.temp_C, test[ml.TARGET], pred):
                rows.append(dict(atmosphere=atm, train_betas_C_per_min=",".join(map(str, train)),
                                 test_beta_C_per_min=test_beta, predictor=name, temp_K=t_k, temp_C=t_c,
                                 measured_mass_pct=y, predicted_mass_pct=p))
    pd.DataFrame(rows).to_csv(args.out / "holdout_predictions.csv", index=False)

    _, x_train, y_train = ml.subset(frame, "N2", [5, 20], ml.FEATURES)
    _, x_test, y_test = ml.subset(frame, "N2", [10], ml.FEATURES)
    grid = []
    for n_estimators in [1, 2, 3, 5, 10, 20, 30, 50, 100]:
        for depth in range(1, 8):
            model = RandomForestRegressor(n_estimators=n_estimators, max_depth=depth,
                                          random_state=ml.RANDOM_STATE, n_jobs=-1).fit(x_train, y_train)
            grid.append(dict(n_estimators=n_estimators, max_depth=depth,
                             Train_R2=r2_score(y_train, model.predict(x_train)),
                             Test_R2=r2_score(y_test, model.predict(x_test))))
    pd.DataFrame(grid).to_csv(args.out / "RF_grid_FigureS6.csv", index=False)

    regenerated = {
        "Holdout_Results.csv": holdout,
        "Deterministic_Baseline_Results.csv": ml.deterministic_baselines(frame)[0],
        "Ablation_Results.csv": ml.feature_ablation(frame)[0],
        "Random_Benchmark.csv": ml.random_benchmark(frame)[0],
        "RF_Representative_Sensitivity.csv": ml.rf_sensitivity(frame)[0],
        "RF_Six_Holdout_Depth_Summary.csv": ml.rf_sensitivity(frame)[1],
        "GBR_Representative_Sensitivity.csv": ml.gbr_sensitivity(frame),
    }
    lines = [
        "Holdout regeneration check against archived metric tables (results/ml).",
        "Per-point predictions were never archived; this compares regenerated metrics with the frozen CSV files.",
        f"Python {platform.python_version()}, NumPy {np.__version__}, pandas {pd.__version__}, scikit-learn {sklearn.__version__}",
        "",
    ]
    for filename, table in regenerated.items():
        archived = pd.read_csv(ROOT / "results" / "ml" / filename)
        numeric = archived.select_dtypes("number").columns
        same_shape = archived.shape == table.shape
        diff = float(np.nanmax(np.abs(archived[numeric].to_numpy(float) - table[numeric].to_numpy(float)))) if same_shape else float("nan")
        lines.append(f"{filename}: shape match = {same_shape}; max |difference| = {diff:.3e}")
    (ROOT / "results" / "ml" / "Holdout_regeneration_check.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
