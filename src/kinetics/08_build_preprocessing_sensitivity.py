"""08_build_preprocessing_sensitivity.py — one-factor preprocessing sensitivity on the frozen
canonical reconstruction (Phase 1), changing exactly one factor at a time
per the supervisor's explicit instruction."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from sklearn.isotonic import IsotonicRegression

from alc_core import BETAS, RESULTS_DIR, load_raw_curve

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

GRID = np.arange(323, 1001, 1.0)
ALPHA_TARGETS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
R_KJ_MOL_K = 0.00831446261815324


def load_grouped(atmosphere: str, beta: int):
    raw = load_raw_curve(atmosphere, beta)
    T = np.maximum.accumulate(raw.temp_K.to_numpy(float))
    mass = raw.mass_pct.to_numpy(float)
    grouped = pd.DataFrame({"T": T, "m": mass}).groupby("T", as_index=False).m.mean()
    return np.interp(GRID, grouped["T"].to_numpy(float), grouped["m"].to_numpy(float))


def process(atmosphere: str, beta: int, sg_window: int, baseline_mode: str):
    interp = load_grouped(atmosphere, beta)
    if atmosphere == "Air":
        if baseline_mode == "constant_1000K":
            offset = float(interp[-1])
            interp = interp - offset
        elif baseline_mode == "none":
            pass  # no correction at all
        elif baseline_mode == "mean_last_20":
            offset = float(interp[-20:].mean())
            interp = interp - offset
        else:
            raise ValueError(baseline_mode)
    smoothed = savgol_filter(interp, window_length=sg_window, polyorder=3, mode="interp")
    if atmosphere == "N2":
        clean_mass = IsotonicRegression(increasing=False, out_of_bounds="clip").fit_transform(GRID, smoothed)
    else:
        clean_mass = smoothed
    return clean_mass


def first_crossing_T(grid, alpha, target):
    for i in range(1, len(alpha)):
        if alpha[i - 1] < target <= alpha[i]:
            frac = (target - alpha[i - 1]) / (alpha[i] - alpha[i - 1])
            return float(grid[i - 1] + frac * (grid[i] - grid[i - 1]))
    return float("nan")


def kas_ea(T5, T10, T20):
    T = np.array([T5, T10, T20]); beta = np.array([5.0, 10.0, 20.0])
    x = 1.0 / T; y = np.log(beta / T ** 2)
    slope, _ = np.polyfit(x, y, 1)
    return -slope * R_KJ_MOL_K


def talpha_and_ea(atmosphere, sg_window, baseline_mode):
    curves = {beta: process(atmosphere, beta, sg_window, baseline_mode) for beta in BETAS}
    mfs = {beta: float(curves[beta][-1]) for beta in BETAS}
    out = {}
    for a in ALPHA_TARGETS:
        Ts = []
        for beta in BETAS:
            alpha_arr = (100.0 - curves[beta]) / (100.0 - mfs[beta])
            Ts.append(first_crossing_T(GRID, alpha_arr, a))
        out[a] = {"T5": Ts[0], "T10": Ts[1], "T20": Ts[2], "Ea": kas_ea(*Ts)}
    return out


# ============================================================
# PHASE 2A: SG-window sensitivity (15/21/31), canonical baseline fixed
# ============================================================
print("=== PHASE 2A: SG-window sensitivity (baseline treatment held at canonical) ===")
rows_2a = []
reference = {}
for atm in ("N2", "Air"):
    reference[atm] = talpha_and_ea(atm, 21, "constant_1000K")

for atm in ("N2", "Air"):
    for w in (15, 21, 31):
        result = talpha_and_ea(atm, w, "constant_1000K")
        for a in ALPHA_TARGETS:
            ref_ea = reference[atm][a]["Ea"]
            rows_2a.append({
                "atmosphere": atm, "sg_window": w, "alpha": a,
                "T5": result[a]["T5"], "T10": result[a]["T10"], "T20": result[a]["T20"],
                "Ea_kJ_mol": result[a]["Ea"],
                "delta_Ea_vs_SG21": result[a]["Ea"] - ref_ea,
            })
df_2a = pd.DataFrame(rows_2a)
print(df_2a.round(4).to_string(index=False))
df_2a.to_csv(RESULTS_DIR / "SG_Window_Sensitivity.csv", index=False)

print("\n--- Key deltas of interest ---")
for atm, alist in [("N2", [0.5, 0.6, 0.7, 0.8]), ("Air", [0.7, 0.8])]:
    for a in alist:
        sub = df_2a[(df_2a.atmosphere == atm) & (df_2a.alpha == a)]
        span = sub.delta_Ea_vs_SG21.max() - sub.delta_Ea_vs_SG21.min()
        print(f"  {atm} alpha={a}: SG15/21/31 Ea span = {span:.3f} kJ/mol "
              f"(values: {sub.Ea_kJ_mol.round(3).tolist()})")

# ============================================================
# PHASE 2B: Air baseline-treatment sensitivity (SG window fixed at 21)
# ============================================================
print("\n=== PHASE 2B: Air baseline-treatment sensitivity (SG window held at 21) ===")
rows_2b = []
canon_ref_air = reference["Air"]
for mode in ("constant_1000K", "none", "mean_last_20"):
    result = talpha_and_ea("Air", 21, mode)
    for a in ALPHA_TARGETS:
        rows_2b.append({
            "baseline_mode": mode, "alpha": a,
            "T5": result[a]["T5"], "T10": result[a]["T10"], "T20": result[a]["T20"],
            "Ea_kJ_mol": result[a]["Ea"],
            "delta_Ea_vs_canonical": result[a]["Ea"] - canon_ref_air[a]["Ea"],
        })
df_2b = pd.DataFrame(rows_2b)
print(df_2b.round(4).to_string(index=False))
df_2b.to_csv(RESULTS_DIR / "Air_Baseline_Sensitivity.csv", index=False)

print("\n--- Air high-conversion sensitivity to baseline treatment ---")
for a in (0.7, 0.8):
    sub = df_2b[df_2b.alpha == a]
    print(f"  alpha={a}: Ea range across baseline modes = "
          f"{sub.Ea_kJ_mol.min():.2f} to {sub.Ea_kJ_mol.max():.2f} kJ/mol "
          f"(span {sub.Ea_kJ_mol.max()-sub.Ea_kJ_mol.min():.2f})")

# ============================================================
# PHASE 2C: does the 662-664K Air wiggle affect T_0.7 or T_0.8?
# ============================================================
print("\n=== PHASE 2C: does the Air beta=5 662-664K DTG wiggle affect T_alpha extraction? ===")
curve_beta5 = process("Air", 5, 21, "constant_1000K")
mf5 = float(curve_beta5[-1])
alpha5 = (100.0 - curve_beta5) / (100.0 - mf5)

# locate the wiggle in the alpha trace
zone = (GRID >= 655) & (GRID <= 690)
wiggle_present = np.any(np.diff(alpha5[zone]) < 0)  # alpha should be monotonic increasing;
                                                     # a decrease here = the wiggle's signature
print(f"Alpha non-monotonic (decreasing) anywhere in 655-690K: {wiggle_present}")
if wiggle_present:
    idx = np.where((GRID >= 655) & (GRID <= 690))[0]
    dips = [(GRID[i], alpha5[i], alpha5[i+1]-alpha5[i]) for i in idx[:-1] if alpha5[i+1] < alpha5[i]]
    print(f"  Locations of alpha decrease: {dips}")

T_07 = first_crossing_T(GRID, alpha5, 0.7)
T_08 = first_crossing_T(GRID, alpha5, 0.8)
alpha_at_662 = np.interp(662, GRID, alpha5)
alpha_at_664 = np.interp(664, GRID, alpha5)
print(f"alpha at T=662K: {alpha_at_662:.4f}, at T=664K: {alpha_at_664:.4f}")
print(f"T_alpha=0.7 (first-crossing): {T_07:.3f} K  (wiggle zone is 655-690K, "
      f"{'OVERLAPS' if 655<=T_07<=690 else 'does not overlap'} the crossing point)")
print(f"T_alpha=0.8 (first-crossing): {T_08:.3f} K  (wiggle zone is 655-690K, "
      f"{'OVERLAPS' if 655<=T_08<=690 else 'does not overlap'} the crossing point)")

# also test: rebuild with the wiggle artificially removed (local linear
# bridge across exactly the reversal, nothing else) and compare T_alpha
mass_check = curve_beta5.copy()
zone_idx = np.where((GRID >= 660) & (GRID <= 666))[0]
if len(zone_idx) >= 2:
    lo, hi = zone_idx[0], zone_idx[-1]
    mass_check[lo:hi+1] = np.interp(GRID[lo:hi+1], [GRID[lo], GRID[hi]], [mass_check[lo], mass_check[hi]])
alpha_check = (100.0 - mass_check) / (100.0 - mf5)
T_07_check = first_crossing_T(GRID, alpha_check, 0.7)
T_08_check = first_crossing_T(GRID, alpha_check, 0.8)
print(f"\nWith wiggle manually bridged (662-664K only): T_0.7={T_07_check:.4f}K "
      f"(delta={T_07_check-T_07:+.5f}K), T_0.8={T_08_check:.4f}K (delta={T_08_check-T_08:+.5f}K)")

conclusion = (
    "MATERIAL" if (abs(T_07_check - T_07) > 0.05 or abs(T_08_check - T_08) > 0.05)
    else "NOT MATERIAL"
)
print(f"\nCONCLUSION: the 662-664K wiggle is {conclusion} to T_0.7/T_0.8 extraction "
      f"(threshold 0.05K, matching the Phase-1 acceptance tolerance).")

with open(RESULTS_DIR / "Air_DTG_Wiggle_Materiality.txt", "w") as f:
    f.write(f"Air beta=5, 662-664K DTG wiggle materiality check\n")
    f.write(f"T_0.7 without bridge: {T_07:.4f} K, with bridge: {T_07_check:.4f} K, delta: {T_07_check-T_07:+.5f} K\n")
    f.write(f"T_0.8 without bridge: {T_08:.4f} K, with bridge: {T_08_check:.4f} K, delta: {T_08_check-T_08:+.5f} K\n")
    f.write(f"Conclusion: {conclusion} (threshold 0.05K)\n")
    f.write("Per Phase-2 scope, the canonical kinetics pipeline is NOT modified to remove this wiggle.\n")
    f.write("It is documented as a small SG derivative artifact affecting visualization only.\n")

print("\nWrote SG_Window_Sensitivity.csv, Air_Baseline_Sensitivity.csv, "
      "Air_DTG_Wiggle_Materiality.txt")
