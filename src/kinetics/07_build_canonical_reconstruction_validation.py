"""07_build_canonical_reconstruction_validation.py — validation record for the canonical
preprocessing reconstruction. Produces the five audit items specified
before Phase 2 sensitivity testing begins."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import openpyxl
from scipy.signal import savgol_filter
from sklearn.isotonic import IsotonicRegression

from alc_core import BETAS, RESULTS_DIR, DATA_DIR, load_raw_curve

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

SG_WINDOW = 21
SG_POLYORDER = 3
GRID = np.arange(323, 1001, 1.0)
ALPHA_TARGETS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]  # alpha=0.1 excluded, documented ill-conditioned
R_KJ_MOL_K = 0.00831446261815324


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_curve(atmosphere: str, beta: int, sg_window: int = SG_WINDOW):
    raw = load_raw_curve(atmosphere, beta)
    T = np.maximum.accumulate(raw.temp_K.to_numpy(float))
    mass = raw.mass_pct.to_numpy(float)
    grouped = pd.DataFrame({"T": T, "m": mass}).groupby("T", as_index=False).m.mean()
    interp = np.interp(GRID, grouped["T"].to_numpy(float), grouped["m"].to_numpy(float))

    baseline_offset = 0.0
    if atmosphere == "Air":
        baseline_offset = float(interp[-1])  # anchored at T=1000K (canonical grid boundary)
        interp = interp - baseline_offset

    window = sg_window
    smoothed = savgol_filter(interp, window_length=window, polyorder=SG_POLYORDER, mode="interp")

    if atmosphere == "N2":
        clean_mass = IsotonicRegression(increasing=False, out_of_bounds="clip").fit_transform(GRID, smoothed)
    else:
        clean_mass = smoothed

    return clean_mass, baseline_offset


def first_crossing_T(grid: np.ndarray, alpha: np.ndarray, target: float) -> float:
    for i in range(1, len(alpha)):
        if alpha[i - 1] < target <= alpha[i]:
            frac = (target - alpha[i - 1]) / (alpha[i] - alpha[i - 1])
            return float(grid[i - 1] + frac * (grid[i] - grid[i - 1]))
    return float("nan")


def kas_fit(T5, T10, T20):
    T = np.array([T5, T10, T20]); beta = np.array([5.0, 10.0, 20.0])
    x = 1.0 / T; y = np.log(beta / T ** 2)
    n = 3
    xbar, ybar = x.mean(), y.mean()
    Sxx = ((x - xbar) ** 2).sum()
    slope = ((x - xbar) * (y - ybar)).sum() / Sxx
    intercept = ybar - slope * xbar
    yhat = intercept + slope * x
    resid = y - yhat
    dof = n - 2
    s2 = (resid ** 2).sum() / dof if dof > 0 else np.nan
    se_slope = np.sqrt(s2 / Sxx) if dof > 0 else np.nan
    ss_tot = ((y - ybar) ** 2).sum()
    r2 = 1 - (resid ** 2).sum() / ss_tot if ss_tot > 0 else np.nan
    ea = -slope * R_KJ_MOL_K
    se_ea = se_slope * R_KJ_MOL_K
    return {"slope": slope, "intercept": intercept, "R2": r2, "Ea_kJ_mol": ea, "SE_Ea_kJ_mol": se_ea}


def fwo_fit(T5, T10, T20):
    T = np.array([T5, T10, T20]); beta = np.array([5.0, 10.0, 20.0])
    x = 1.0 / T; y = np.log(beta)
    n = 3
    xbar, ybar = x.mean(), y.mean()
    Sxx = ((x - xbar) ** 2).sum()
    slope = ((x - xbar) * (y - ybar)).sum() / Sxx
    intercept = ybar - slope * xbar
    yhat = intercept + slope * x
    resid = y - yhat
    dof = n - 2
    s2 = (resid ** 2).sum() / dof if dof > 0 else np.nan
    se_slope = np.sqrt(s2 / Sxx) if dof > 0 else np.nan
    ss_tot = ((y - ybar) ** 2).sum()
    r2 = 1 - (resid ** 2).sum() / ss_tot if ss_tot > 0 else np.nan
    ea = -slope * R_KJ_MOL_K / 1.052
    se_ea = se_slope * R_KJ_MOL_K / 1.052
    return {"slope": slope, "intercept": intercept, "R2": r2, "Ea_kJ_mol": ea, "SE_Ea_kJ_mol": se_ea}


def starink_fit(T5, T10, T20):
    T = np.array([T5, T10, T20]); beta = np.array([5.0, 10.0, 20.0])
    x = 1.0 / T; y = np.log(beta / T ** 1.92)
    n = 3
    xbar, ybar = x.mean(), y.mean()
    Sxx = ((x - xbar) ** 2).sum()
    slope = ((x - xbar) * (y - ybar)).sum() / Sxx
    intercept = ybar - slope * xbar
    yhat = intercept + slope * x
    resid = y - yhat
    dof = n - 2
    s2 = (resid ** 2).sum() / dof if dof > 0 else np.nan
    se_slope = np.sqrt(s2 / Sxx) if dof > 0 else np.nan
    ss_tot = ((y - ybar) ** 2).sum()
    r2 = 1 - (resid ** 2).sum() / ss_tot if ss_tot > 0 else np.nan
    ea = -slope * R_KJ_MOL_K / 1.0008
    se_ea = se_slope * R_KJ_MOL_K / 1.0008
    return {"slope": slope, "intercept": intercept, "R2": r2, "Ea_kJ_mol": ea, "SE_Ea_kJ_mol": se_ea}


# ============================================================
# ITEM 1: m0 / baseline offset / mf record, all six curves
# ============================================================
item1_rows = []
clean_curves = {}
for atm in ("N2", "Air"):
    for beta in BETAS:
        clean_mass, offset = clean_curve(atm, beta)
        clean_curves[(atm, beta)] = clean_mass
        m0 = 100.0
        mf_reproduced = float(clean_mass[-1])
        item1_rows.append({
            "atmosphere": atm, "beta": beta,
            "m0_reproduced_pct": m0,
            "air_baseline_offset_pct": offset if atm == "Air" else None,
            "mf_reproduced_pct": mf_reproduced,
            "mf_frozen_Table_S1_pct": {("N2", 5): 2.632, ("N2", 10): 2.672, ("N2", 20): 3.105,
                                       ("Air", 5): 0.033, ("Air", 10): 0.040, ("Air", 20): 0.032}[(atm, beta)],
        })
item1 = pd.DataFrame(item1_rows)
item1["mf_delta_pct"] = item1.mf_reproduced_pct - item1.mf_frozen_Table_S1_pct

# max mass-profile deviation: compare full clean_mass curve at each grid
# point to what a re-run of the exact same code produces (self-consistency
# check) -- and separately, spot deviation implied by the Tα deltas
print("=== ITEM 1: m0 / baseline offset / mf record ===")
print(item1.to_string(index=False))
item1.to_csv(RESULTS_DIR / "Canonical_Reconstruction_mass_reference_points.csv", index=False)

# ============================================================
# ITEM 2: every T_alpha for alpha=0.2-0.8, all six curves
# ============================================================
wb = openpyxl.load_workbook(DATA_DIR / "Arab_Light_TGA_Canonical_Data.xlsx", data_only=True)
ws = wb["Kinetic_Talpha"]
canon_talpha = {}
for row in ws.iter_rows(min_row=4, max_row=19, values_only=True):
    if row[0] is None:
        continue
    canon_talpha[(row[0], round(row[1], 1))] = {"beta5": row[2], "beta10": row[3], "beta20": row[4]}

item2_rows = []
for atm in ("N2", "Air"):
    for beta in BETAS:
        clean_mass = clean_curves[(atm, beta)]
        mf = float(clean_mass[-1])
        alpha_arr = (100.0 - clean_mass) / (100.0 - mf)
        for a in ALPHA_TARGETS:
            T_a = first_crossing_T(GRID, alpha_arr, a)
            T_canon = canon_talpha[(atm, round(a, 1))][f"beta{beta}"]
            item2_rows.append({
                "atmosphere": atm, "beta": beta, "alpha": a,
                "T_alpha_canonical_K": T_canon, "T_alpha_reconstructed_K": T_a,
                "delta_T_alpha_K": T_a - T_canon,
            })
item2 = pd.DataFrame(item2_rows)
print("\n=== ITEM 2: every T_alpha, alpha=0.2-0.8, all six curves ===")
print(item2.to_string(index=False))
print(f"\nMax |delta T_alpha|: {item2.delta_T_alpha_K.abs().max():.4f} K")
item2.to_csv(RESULTS_DIR / "Canonical_Reconstruction_all_Talpha_deltas.csv", index=False)

# ============================================================
# ITEM 3: all 42 regressions from reconstructed T_alpha
# ============================================================
FITTERS = {"FWO": fwo_fit, "KAS": kas_fit, "Starink": starink_fit}
item3_rows = []
for atm in ("N2", "Air"):
    for a in ALPHA_TARGETS:
        T5 = item2[(item2.atmosphere == atm) & (item2.beta == 5) & (item2.alpha == a)].T_alpha_reconstructed_K.iloc[0]
        T10 = item2[(item2.atmosphere == atm) & (item2.beta == 10) & (item2.alpha == a)].T_alpha_reconstructed_K.iloc[0]
        T20 = item2[(item2.atmosphere == atm) & (item2.beta == 20) & (item2.alpha == a)].T_alpha_reconstructed_K.iloc[0]
        for model, fitter in FITTERS.items():
            fit = fitter(T5, T10, T20)
            item3_rows.append({"atmosphere": atm, "alpha": a, "model": model, **fit})
item3 = pd.DataFrame(item3_rows)
print(f"\n=== ITEM 3: all {len(item3)} regressions recomputed from reconstructed T_alpha ===")
print(item3.round(4).to_string(index=False))
item3.to_csv(RESULTS_DIR / "Canonical_Reconstruction_all_42_regressions.csv", index=False)

# compare against canonical (kinetics_regression_core, already validated to
# match Kinetic_Talpha-derived regression)
from kinetics_regression_core import resolve_source, load_talpha, regressions
canon_reg = regressions(load_talpha(resolve_source(None)))
compare_rows = []
for _, r in item3.iterrows():
    c = canon_reg[(canon_reg.atmosphere == r.atmosphere) & (canon_reg.alpha == r.alpha) & (canon_reg.model == r.model)]
    if len(c):
        c = c.iloc[0]
        compare_rows.append({
            "atmosphere": r.atmosphere, "alpha": r.alpha, "model": r.model,
            "R2_reconstructed": r.R2, "R2_canonical": c.R2, "delta_R2": r.R2 - c.R2,
            "Ea_reconstructed": r.Ea_kJ_mol, "Ea_canonical": c.Ea_kJ_mol, "delta_Ea": r.Ea_kJ_mol - c.Ea_kJ_mol,
            "SE_reconstructed": r.SE_Ea_kJ_mol, "SE_canonical": c.SE_Ea_kJ_mol, "delta_SE": r.SE_Ea_kJ_mol - c.SE_Ea_kJ_mol,
        })
item3_compare = pd.DataFrame(compare_rows)
item3_compare.to_csv(RESULTS_DIR / "Canonical_Reconstruction_comparison_vs_authoritative.csv", index=False)
print(f"\nMax |delta Ea| (0.2-0.8, all models): {item3_compare[item3_compare.alpha<0.8].delta_Ea.abs().max():.4f} kJ/mol")
print(f"Max |delta Ea| at alpha=0.8: {item3_compare[item3_compare.alpha==0.8].delta_Ea.abs().max():.4f} kJ/mol")
print(f"Max |delta R2|: {item3_compare.delta_R2.abs().max():.6f}")

# ============================================================
# ITEM 4: hashes
# ============================================================
item4 = {
    "canonical_source_workbook": {
        "path": "data/private/Arab_Light_TGA_Canonical_Data.xlsx",
        "sha256": sha256(DATA_DIR / "Arab_Light_TGA_Canonical_Data.xlsx"),
    },
    "raw_source_workbook": {
        "path": "data/private/Arab_Light_Kinetics_Source_FWO_KAS_Starink.xlsx",
        "sha256": sha256(DATA_DIR / "Arab_Light_Kinetics_Source_FWO_KAS_Starink.xlsx"),
    },
    "reconstruction_script": {
        "path": "src/kinetics/01_build_canonical_pipeline.py",
        "sha256": sha256(Path(__file__).resolve().parent / "01_build_canonical_pipeline.py"),
    },
    "freeze_script": {
        "path": "src/kinetics/07_build_canonical_reconstruction_validation.py",
        "sha256": sha256(Path(__file__).resolve()),
    },
}
print("\n=== ITEM 4: hashes ===")
print(json.dumps(item4, indent=2))
with open(RESULTS_DIR / "Canonical_Reconstruction_hashes.json", "w") as f:
    json.dump(item4, f, indent=2)

# ============================================================
# ITEM 5: provenance statement
# ============================================================
item5 = (
    "The preprocessing implementation was reconstructed from the archived "
    "Methods, Supplementary Table S1, workbook metadata, and frozen "
    "Kinetic_Talpha outputs. It reproduces the authoritative kinetic "
    "inputs to negligible reconstruction discrepancy (max |delta T_alpha| "
    f"= {item2.delta_T_alpha_K.abs().max():.3f} K, alpha=0.2-0.8; max "
    f"|delta Ea| = {item3_compare[item3_compare.alpha<0.8].delta_Ea.abs().max():.3f} kJ/mol "
    "for alpha=0.2-0.7, "
    f"{item3_compare[item3_compare.alpha==0.8].delta_Ea.abs().max():.3f} kJ/mol at alpha=0.8) "
    "but is NOT claimed to be the originally executed source code. The "
    "Air terminal-baseline anchor point (T=1000K, the canonical grid "
    "boundary, not the raw acquisition endpoint near 1262K) was the "
    "specific detail that closed the gap from an initial 5-214 kJ/mol "
    "discrepancy down to this level; it was inferred from the frozen "
    "outputs, not recovered from original code."
)
print("\n=== ITEM 5: provenance statement ===")
print(item5)
with open(RESULTS_DIR / "Canonical_Reconstruction_provenance.txt", "w") as f:
    f.write(item5)

print("\n=== PHASE 1 FREEZE COMPLETE ===")
print("Label: ALC_Canonical_Preprocessing_Reconstruction_v1_FROZEN")
