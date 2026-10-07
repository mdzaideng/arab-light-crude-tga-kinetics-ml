"""Rebuild the post-review publication Figure 5 from frozen v6.1 regression outputs.

This publication-layer wrapper was added during final packaging to capture the final
visual uncertainty treatment after activation enthalpy was promoted to a main result.
It does NOT alter the frozen kinetic calculations. Numeric inputs are read from the
v6.1 all-regression CSV and Delta H^‡ is calculated as Ea - R*Tmean.

Usage from repository root:
    python src/kinetics/06_build_figure5_activation_enthalpy_with_CI.py

Outputs are written directly to figures/main/.
"""
from __future__ import annotations

from pathlib import Path
import os, tempfile
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "alc-pubfig-mpl-cache"))

import matplotlib.pyplot as plt
from alc_core import publication_font_rc
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "results" / "kinetics" / "Figure4_all_regressions_with_CI.csv"
OUT = ROOT / "figures" / "main"
R = 0.00831446261815324


def main() -> None:
    df = pd.read_csv(INPUT)
    df["Tmean_K"] = df[["T5_K", "T10_K", "T20_K"]].mean(axis=1)
    df["dH_kJ_mol"] = df["Ea_kJ_mol"] - R * df["Tmean_K"]
    df["dH_SE"] = df["SE_Ea_kJ_mol"]
    df["dH_CI_low"] = df["CI95_lower_kJ_mol"] - R * df["Tmean_K"]
    df["dH_CI_high"] = df["CI95_upper_kJ_mol"] - R * df["Tmean_K"]

    kas = df[df.model.eq("KAS")].copy()
    n2 = kas[kas.atmosphere.eq("N2")].sort_values("alpha")
    air = kas[kas.atmosphere.eq("Air")].sort_values("alpha")
    air_main = air[air.alpha.le(0.7)]
    air_late = air[air.alpha.eq(0.8)].iloc[0]

    def method_env(atm: str):
        s = df[df.atmosphere.eq(atm)]
        p = s.pivot(index="alpha", columns="model", values="dH_kJ_mol").sort_index()
        return p.min(axis=1), p.max(axis=1)

    n2lo, n2hi = method_env("N2")
    alo, ahi = method_env("Air")

    plt.rcParams.update({
        **publication_font_rc(),
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })

    fig = plt.figure(figsize=(12.2, 5.684))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.30, 1], width_ratios=[1, 1],
                          left=0.075, right=0.985, top=0.91, bottom=0.20,
                          wspace=0.25, hspace=0.08)
    ax_n2 = fig.add_subplot(gs[:, 0])
    ax_at = fig.add_subplot(gs[0, 1])
    ax_a = fig.add_subplot(gs[1, 1], sharex=ax_at)

    # N2: method spread, CI whiskers, SE, KAS curve
    ax_n2.fill_between(n2.alpha, n2lo.loc[n2.alpha].to_numpy(), n2hi.loc[n2.alpha].to_numpy(), alpha=0.16)
    ci_low = n2.dH_kJ_mol - n2.dH_CI_low
    ci_high = n2.dH_CI_high - n2.dH_kJ_mol
    ax_n2.errorbar(n2.alpha, n2.dH_kJ_mol, yerr=[ci_low, ci_high], fmt="none",
                   ecolor="0.50", elinewidth=1.0, capsize=3, zorder=1)
    ax_n2.errorbar(n2.alpha, n2.dH_kJ_mol, yerr=n2.dH_SE, marker="o", lw=1.5,
                   capsize=3, zorder=3)
    ax_n2.axhline(0, color="0.75", lw=0.8)
    ax_n2.text(0.50, -46, "individual conditional 95% CIs\nbecome broad at higher α", fontsize=8)

    # Air main region
    ax_a.fill_between(air_main.alpha, alo.loc[air_main.alpha].to_numpy(), ahi.loc[air_main.alpha].to_numpy(), alpha=0.16)
    ci_low = air_main.dH_kJ_mol - air_main.dH_CI_low
    ci_high = air_main.dH_CI_high - air_main.dH_kJ_mol
    ax_a.errorbar(air_main.alpha, air_main.dH_kJ_mol, yerr=[ci_low, ci_high], fmt="none",
                  ecolor="0.50", elinewidth=1.0, capsize=3, zorder=1)
    ax_a.errorbar(air_main.alpha, air_main.dH_kJ_mol, yerr=air_main.dH_SE, marker="o", lw=1.5,
                  capsize=3, zorder=3)
    ax_a.axhline(0, color="0.75", lw=0.8)
    ax_a.text(0.205, 103, "Air α=0.2 conditional CI\nslightly includes zero", fontsize=8)

    # Air late point: SE shown; full CI disclosed in text because it is off-scale
    ax_at.errorbar([air_late.alpha], [air_late.dH_kJ_mol], yerr=[air_late.dH_SE],
                   marker="D", mfc="white", mew=1.4, lw=0, capsize=3, zorder=3)
    ax_at.annotate(
        "late-conversion oxidative regime, α=0.8\n"
        f"{air_late.dH_kJ_mol:.1f} ± {air_late.dH_SE:.1f} kJ mol$^{{-1}}$ (SE)\n"
        f"conditional 95% CI [{air_late.dH_CI_low:.0f}, {air_late.dH_CI_high:.0f}]\n"
        "qualitative only",
        xy=(air_late.alpha, air_late.dH_kJ_mol), xytext=(0.49, 0.63),
        textcoords="axes fraction", fontsize=7.6,
        arrowprops=dict(arrowstyle="-", lw=0.8), va="center")

    # Axis formatting
    ax_n2.set_title("Pyrolysis (N$_2$)", fontweight="semibold")
    ax_at.set_title("Combustion (Air)", fontweight="semibold")
    ax_n2.text(-0.11, 1.02, "(a)", transform=ax_n2.transAxes, fontweight="bold", fontsize=11)
    ax_at.text(-0.11, 1.08, "(b)", transform=ax_at.transAxes, fontweight="bold", fontsize=11)
    for ax in (ax_n2, ax_a, ax_at):
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", alpha=0.2, lw=0.5)
        ax.set_xlim(0.15, 0.85)
    ax_n2.spines["top"].set_visible(False)
    ax_a.spines["top"].set_visible(False)
    ax_n2.set_ylim(-65, 290)
    ax_a.set_ylim(-8, 118)
    ax_at.set_ylim(215, 300)
    ax_at.tick_params(axis="x", bottom=False, labelbottom=False)

    # break marks
    d = .012
    kwargs = dict(transform=ax_at.transAxes, color="k", clip_on=False, lw=0.8)
    ax_at.plot((-d, +d), (-d, +d), **kwargs)
    kwargs.update(transform=ax_a.transAxes)
    ax_a.plot((-d, +d), (1-d, 1+d), **kwargs)

    ax_n2.set_xlabel(r"Conversion, $\alpha$")
    ax_a.set_xlabel(r"Conversion, $\alpha$")
    ylabel = r"Apparent activation enthalpy, $\Delta H^{\ddagger}_{\alpha}$ (kJ mol$^{-1}$)"
    ax_n2.set_ylabel(ylabel)
    ax_a.set_ylabel(ylabel)
    ax_n2.set_xticks(np.arange(0.2, 0.9, 0.1))
    ax_a.set_xticks(np.arange(0.2, 0.9, 0.1))

    fig.legend(handles=[
        Line2D([0], [0], marker="o", lw=1.4, label="KAS estimate ± regression SE"),
        Line2D([0], [0], color="0.5", lw=1.0, label="individual conditional 95% CI (df=1)"),
        Patch(alpha=0.16, label="FWO/KAS/Starink min-max spread"),
    ], loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.53, 0.03))

    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "Figure6_activation_enthalpy.pdf", dpi=600,
                metadata={"Creator": "ALC final kinetics packaging wrapper", "CreationDate": None, "ModDate": None})
    fig.savefig(OUT / "Figure6_activation_enthalpy.png", dpi=600)
    plt.close(fig)

    # Numeric acceptance checks against frozen main Table 2 (dH) values -- formerly Table 3 before the Table 2+3 merge.
    checks = {
        "N2_a02": (42.1, 2.1), "N2_a08": (112.4, 13.0),
        "Air_a02": (27.0, 2.2), "Air_a07": (86.5, 1.6), "Air_a08": (253.1, 34.9),
    }
    obs = {
        "N2_a02": n2.loc[n2.alpha.eq(0.2), ["dH_kJ_mol", "dH_SE"]].iloc[0],
        "N2_a08": n2.loc[n2.alpha.eq(0.8), ["dH_kJ_mol", "dH_SE"]].iloc[0],
        "Air_a02": air.loc[air.alpha.eq(0.2), ["dH_kJ_mol", "dH_SE"]].iloc[0],
        "Air_a07": air.loc[air.alpha.eq(0.7), ["dH_kJ_mol", "dH_SE"]].iloc[0],
        "Air_a08": air.loc[air.alpha.eq(0.8), ["dH_kJ_mol", "dH_SE"]].iloc[0],
    }
    for key, expected in checks.items():
        got = tuple(round(float(x), 1) for x in obs[key])
        if got != expected:
            raise AssertionError(f"{key}: {got} != {expected}")
    outdata = df[["atmosphere","alpha","model","T5_K","T10_K","T20_K","Tmean_K","Ea_kJ_mol","SE_Ea_kJ_mol","CI95_lower_kJ_mol","CI95_upper_kJ_mol","dH_kJ_mol","dH_SE","dH_CI_low","dH_CI_high"]].copy()
    outdata.to_csv(ROOT / "results" / "kinetics" / "Figure5_activation_enthalpy_data.csv", index=False)

    print(f"PASS: publication Figure 5 wrapper generated from {INPUT}")


if __name__ == "__main__":
    main()
