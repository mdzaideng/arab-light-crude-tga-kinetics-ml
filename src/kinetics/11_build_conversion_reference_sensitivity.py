"""Conversion-reference, endpoint, and N2-isotonic sensitivity of the isoconversional estimates.

Re-implementation written from the article text (Section 2.2, Section 3.6, and
Supplementary Sections S3 and S16), because the script that produced the
published values was not found in any archived package. Each test changes one
definition and keeps everything else identical to the canonical pipeline
(``alc_core.canonical_clean_curve``):

``reference``  m0 = 100 % (beginning of the complete program), m_f = cleaned
               mass at 1000 K, first-crossing T_alpha scanned forward over the
               full 323-1000 K grid. This reproduces the canonical
               reconstruction exactly.
``m0_onset``   m0 = cleaned mass at the 90 % stable-ramp onset temperature
               (linear interpolation on the 1 K grid; onset temperatures from
               ``results/kinetics/Figure2_Ramp_Onset_Sensitivity.csv``); m_f
               and the T_alpha scan unchanged.
``endpoint``   grid extended to the common raw-data endpoint (floor of the
               lowest maximum raw temperature over the six runs, ~1261 K);
               m_f = cleaned mass at that endpoint; the Air terminal offset
               stays anchored at 1000 K; m0 = 100 %.
``no_isotonic`` N2 only: isotonic constraint omitted; everything else unchanged.

Output: ``results/kinetics/Conversion_Reference_Sensitivity.csv`` with T_alpha,
Ea for FWO, KAS and Starink, and the difference from ``reference``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from sklearn.isotonic import IsotonicRegression

from alc_core import BETAS, GRID, RESULTS_DIR, SG_POLYORDER, SG_WINDOW_K_DEFAULT, load_raw_curve

R_KJ_MOL_K = 0.00831446261815324
ALPHAS = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
METHODS = {"FWO": (0.0, 1.052), "KAS": (2.0, 1.0), "Starink": (1.92, 1.0008)}


def cleaned(atm: str, beta: int, grid: np.ndarray, isotonic: bool = True) -> np.ndarray:
    raw = load_raw_curve(atm, beta)
    temperature = np.maximum.accumulate(raw.temp_K.to_numpy(float))
    grouped = pd.DataFrame({"T": temperature, "m": raw.mass_pct.to_numpy(float)}).groupby("T", as_index=False).m.mean()
    mass = np.interp(grid, grouped["T"].to_numpy(float), grouped["m"].to_numpy(float))
    if atm == "Air":
        mass = mass - float(np.interp(1000.0, grid, mass))
    mass = savgol_filter(mass, window_length=SG_WINDOW_K_DEFAULT, polyorder=SG_POLYORDER, mode="interp")
    if atm == "N2" and isotonic:
        mass = IsotonicRegression(increasing=False, out_of_bounds="clip").fit_transform(grid, mass)
    return mass


def first_crossing(grid: np.ndarray, alpha: np.ndarray, target: float) -> float:
    for i in range(1, len(alpha)):
        if alpha[i - 1] < target <= alpha[i]:
            return float(grid[i - 1] + (target - alpha[i - 1]) / (alpha[i] - alpha[i - 1]) * (grid[i] - grid[i - 1]))
    return float("nan")


def ea(method: str, temps: list[float]) -> float:
    exponent, factor = METHODS[method]
    t = np.array(temps)
    y = np.log(np.array(BETAS, float) / t ** exponent) if exponent else np.log(np.array(BETAS, float))
    slope = np.polyfit(1.0 / t, y, 1)[0]
    return float(-slope * R_KJ_MOL_K / factor)


def main() -> None:
    onsets = pd.read_csv(RESULTS_DIR / "Figure2_Ramp_Onset_Sensitivity.csv")
    onsets = onsets[(onsets.threshold_fraction_nominal - 0.90).abs() < 1e-9].set_index(["atmosphere", "beta_C_per_min"])
    raw_end = min(load_raw_curve(a, b).temp_K.max() for a in ("N2", "Air") for b in BETAS)
    long_grid = np.arange(323.0, np.floor(raw_end) + 1.0, 1.0)

    rows = []
    for atm in ("N2", "Air"):
        tests = ["reference", "m0_onset", "endpoint"] + (["no_isotonic"] if atm == "N2" else [])
        for test in tests:
            grid = long_grid if test == "endpoint" else GRID
            info, alphas = {}, {}
            for beta in BETAS:
                mass = cleaned(atm, beta, grid, isotonic=(test != "no_isotonic"))
                m_f = float(mass[-1]) if test == "endpoint" else float(np.interp(1000.0, grid, mass))
                m0 = float(np.interp(onsets.loc[(atm, beta)].onset_temperature_K, grid, mass)) if test == "m0_onset" else 100.0
                alphas[beta] = (m0 - mass) / (m0 - m_f)
                info[beta] = (m0, m_f, float(grid[-1]))
            for alpha in ALPHAS:
                temps = [first_crossing(grid, alphas[b], alpha) for b in BETAS]
                row = {"atmosphere": atm, "test": test, "alpha": alpha,
                       "T5_K": temps[0], "T10_K": temps[1], "T20_K": temps[2]}
                for b in BETAS:
                    row[f"m0_beta{b}_pct"], row[f"mf_beta{b}_pct"], row["grid_end_K"] = info[b]
                for method in METHODS:
                    row[f"{method}_Ea_kJ_mol"] = ea(method, temps)
                rows.append(row)
    table = pd.DataFrame(rows)
    reference = table[table.test == "reference"].set_index(["atmosphere", "alpha"])
    for method in METHODS:
        table[f"{method}_delta_vs_reference_kJ_mol"] = [
            r[f"{method}_Ea_kJ_mol"] - reference.loc[(r.atmosphere, r.alpha), f"{method}_Ea_kJ_mol"] for _, r in table.iterrows()
        ]
    table.to_csv(RESULTS_DIR / "Conversion_Reference_Sensitivity.csv", index=False)
    summary = table[table.test != "reference"].assign(main=lambda d: d.alpha <= 0.7)
    print(summary.groupby(["atmosphere", "test", "main"]).KAS_delta_vs_reference_kJ_mol.agg(lambda s: f"{s.abs().min():.3f}-{s.abs().max():.3f}").to_string())


if __name__ == "__main__":
    main()
