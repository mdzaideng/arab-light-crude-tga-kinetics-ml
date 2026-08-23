"""Build current main Figure 4: apparent activation energy with uncertainty.

KAS point estimates carry regression SE. Conditional 95% intervals from the
separate n=3 regressions are shown as discrete whiskers (not a continuous
confidence ribbon). FWO/KAS/Starink min-max spread remains a separate,
descriptive method envelope. Air alpha=0.8 is isolated and treated
qualitatively; its full conditional CI is disclosed in text rather than drawn
to scale.
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from alc_core import FIG_MAIN_DIR, RESULTS_DIR, save_figure
from kinetics_regression_core import resolve_source, load_talpha, regressions

FIG_MAIN_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

source = resolve_source(None)
talpha = load_talpha(source)
df = regressions(talpha)
kas = df[df.model == "KAS"].copy()
envelope = df.groupby(["atmosphere", "alpha"]).Ea_kJ_mol.agg(["min", "max"]).reset_index()
df.to_csv(RESULTS_DIR / "Figure4_all_regressions_with_CI.csv", index=False)

N2_ALPHAS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
AIR_MAIN_ALPHAS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9.5,
    "axes.labelsize": 11, "axes.titlesize": 12,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

fig = plt.figure(figsize=(12.5, 5.5))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 3], hspace=0.06, wspace=0.25)
ax_n2 = fig.add_subplot(gs[:, 0])
ax_air_top = fig.add_subplot(gs[0, 1])
ax_air = fig.add_subplot(gs[1, 1])

# N2
color_n2 = "#1f77b4"
n2 = kas[(kas.atmosphere == "N2") & kas.alpha.isin(N2_ALPHAS)].sort_values("alpha")
env_n2 = envelope[(envelope.atmosphere == "N2") & envelope.alpha.isin(N2_ALPHAS)].sort_values("alpha")
ax_n2.fill_between(env_n2.alpha, env_n2["min"], env_n2["max"], color=color_n2, alpha=0.17, zorder=1)
ci_low = n2.Ea_kJ_mol - n2.CI95_lower_kJ_mol
ci_high = n2.CI95_upper_kJ_mol - n2.Ea_kJ_mol
ax_n2.errorbar(n2.alpha, n2.Ea_kJ_mol, yerr=[ci_low, ci_high], fmt="none",
               ecolor="0.55", elinewidth=1.0, capsize=4, capthick=1.0, zorder=2)
ax_n2.errorbar(n2.alpha, n2.Ea_kJ_mol, yerr=n2.SE_Ea_kJ_mol, fmt="o-",
               color=color_n2, lw=1.55, ms=5, capsize=3, zorder=4)
ax_n2.axhline(0, color="0.75", lw=0.7, zorder=0)
ax_n2.axvline(0.5, color="0.4", lw=0.9, ls=":", zorder=0)
ax_n2.text(0.51, 0.04, "individual 95% slope CIs\ninclude zero from $\\alpha$=0.5",
           transform=ax_n2.get_xaxis_transform(), fontsize=7.6, color="0.32", va="bottom")
ax_n2.set_xlim(0.15, 0.85)
ax_n2.set_ylim(-65, 300)
ax_n2.set_title("Pyrolysis (N$_2$)", fontweight="bold")
ax_n2.set_xlabel(r"Conversion, $\alpha$")
ax_n2.set_ylabel(r"Apparent activation energy, $E_\alpha$ (kJ mol$^{-1}$)")
ax_n2.spines["top"].set_visible(False)
ax_n2.spines["right"].set_visible(False)
ax_n2.text(-0.11, 1.02, "(a)", transform=ax_n2.transAxes, fontsize=11.5, fontweight="bold")

# Air principal region
color_air = "#d62728"
air = kas[(kas.atmosphere == "Air") & kas.alpha.isin(AIR_MAIN_ALPHAS)].sort_values("alpha")
env_air = envelope[(envelope.atmosphere == "Air") & envelope.alpha.isin(AIR_MAIN_ALPHAS)].sort_values("alpha")
r08 = kas[(kas.atmosphere == "Air") & np.isclose(kas.alpha, 0.8)].iloc[0]

ax_air.fill_between(env_air.alpha, env_air["min"], env_air["max"], color=color_air, alpha=0.17, zorder=1)
air_ci_low = air.Ea_kJ_mol - air.CI95_lower_kJ_mol
air_ci_high = air.CI95_upper_kJ_mol - air.Ea_kJ_mol
ax_air.errorbar(air.alpha, air.Ea_kJ_mol, yerr=[air_ci_low, air_ci_high], fmt="none",
                ecolor="0.55", elinewidth=1.0, capsize=4, capthick=1.0, zorder=2)
ax_air.errorbar(air.alpha, air.Ea_kJ_mol, yerr=air.SE_Ea_kJ_mol, fmt="o-",
                color=color_air, lw=1.55, ms=5, capsize=3, zorder=4)
ax_air.set_ylim(0, 120)
ax_air.set_xlim(0.15, 0.85)
ax_air.set_xlabel(r"Conversion, $\alpha$")
ax_air.set_ylabel(r"Apparent activation energy, $E_\alpha$ (kJ mol$^{-1}$)")
ax_air.spines["top"].set_visible(False)
ax_air.spines["right"].set_visible(False)
ax_air.text(0.03, 0.94, "individual 95% slope CIs remain > 0\nfor $\\alpha$=0.2-0.7",
            transform=ax_air.transAxes, fontsize=7.6, va="top", color="0.32")

# Air alpha=0.8, with full SE visible (previous clipping fixed).
upper_margin = max(12.0, 0.18 * r08.SE_Ea_kJ_mol)
ax_air_top.set_ylim(r08.Ea_kJ_mol - r08.SE_Ea_kJ_mol - upper_margin,
                    r08.Ea_kJ_mol + r08.SE_Ea_kJ_mol + upper_margin)
ax_air_top.set_xlim(ax_air.get_xlim())
ax_air_top.errorbar([0.8], [r08.Ea_kJ_mol], yerr=[r08.SE_Ea_kJ_mol],
                    fmt="D", mfc="white", mec=color_air, ms=7.5, mew=1.3,
                    ecolor=color_air, elinewidth=1.2, capsize=4, zorder=5)
ax_air_top.set_title("Combustion (Air)", fontweight="bold")
ax_air_top.spines["bottom"].set_visible(False)
ax_air_top.spines["right"].set_visible(False)
ax_air_top.tick_params(bottom=False, labelbottom=False)
ax_air_top.set_yticks([round(r08.Ea_kJ_mol - r08.SE_Ea_kJ_mol), round(r08.Ea_kJ_mol), round(r08.Ea_kJ_mol + r08.SE_Ea_kJ_mol)])
annotation_text = (
    rf"late residue oxidation, $\alpha$=0.8" + "\n"
    + rf"{r08.Ea_kJ_mol:.1f} $\pm$ {r08.SE_Ea_kJ_mol:.1f} kJ mol$^{{-1}}$ (SE)" + "\n"
    + rf"conditional 95% CI [{r08.CI95_lower_kJ_mol:.0f}, {r08.CI95_upper_kJ_mol:.0f}]" + "\n"
    + r"SG-window span ~22 kJ mol$^{-1}$; qualitative only"
)
ax_air_top.annotate(
    annotation_text,
    xy=(0.8, r08.Ea_kJ_mol), xytext=(0.34, r08.Ea_kJ_mol + 3),
    fontsize=7.0, color="#8b0000", va="center", ha="left",
    arrowprops=dict(arrowstyle="->", color="#8b0000", lw=0.8),
)
ax_air_top.text(-0.11, 1.14, "(b)", transform=ax_air_top.transAxes, fontsize=11.5, fontweight="bold")

# Broken-axis marks on left edge of Air panels.
d = 0.012
kwargs = dict(transform=ax_air_top.transAxes, color="k", clip_on=False, lw=0.8)
ax_air_top.plot((-d, +d), (-d * 3, +d * 3), **kwargs)
kwargs.update(transform=ax_air.transAxes)
ax_air.plot((-d, +d), (1 - d, 1 + d), **kwargs)

legend_items = [
    Line2D([0], [0], color="0.25", marker="o", lw=1.5, label="KAS estimate +/- regression SE"),
    Line2D([0], [0], color="0.55", lw=1.0, marker="_", markersize=8, label="individual conditional 95% CI (df=1)"),
    Patch(facecolor="0.45", alpha=0.17, label="FWO/KAS/Starink min-max spread"),
]
fig.legend(handles=legend_items, loc="lower center", ncol=3, frameon=False,
           bbox_to_anchor=(0.5, -0.02), fontsize=8.1)
fig.subplots_adjust(left=0.075, right=0.99, top=0.94, bottom=0.14, wspace=0.25)
save_figure(
    fig,
    FIG_MAIN_DIR / "Figure4_apparent_activation_energy.png",
    FIG_MAIN_DIR / "Figure4_apparent_activation_energy.pdf",
    dpi=400,
)
plt.close(fig)

print("Wrote Figure4_apparent_activation_energy.png / .pdf")
print(f"Air alpha=0.8 SE top = {r08.Ea_kJ_mol + r08.SE_Ea_kJ_mol:.2f}; axis top = {r08.Ea_kJ_mol + r08.SE_Ea_kJ_mol + upper_margin:.2f}")
