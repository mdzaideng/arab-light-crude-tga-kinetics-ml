"""Build the quantitative TG/DTG descriptors reported in article Table 1.

Sources (no value is typed by hand):
- T(alpha = 0.5): authoritative first-crossing temperatures from the
  ``Kinetic_Talpha`` sheet of ``Arab_Light_TGA_Canonical_Data.xlsx``
  (the same values as Supplementary Table S2); they are read, not recomputed.
- Principal DTG peak temperature and height: ``results/kinetics/
  Figure2_Threshold_Sensitivity.csv`` at the primary 90% ramp-onset
  threshold, i.e. the canonical cleaned curves plotted in Figure 4.
- Mass-loss interval, three candidate definitions (the article must choose one):
  (threshold) first/last plotted temperature with -dm/dT > 0.05 % K^-1 in the
  stable-ramp DTG domain (T >= max(350 K, 90% onset + 20 K)); its start is often
  the plotting limit and Air curves dip below the threshold inside the interval;
  (A) first-crossing T at whole-program alpha = 0.05 and 0.95 (canonical alpha);
  (B) first-crossing T at ramp-referenced alpha_ramp = 0.05 and 0.95, where
  alpha_ramp = (m_onset - m)/(m_onset - m_f) and m_onset is the cleaned mass at
  the 90% stable-ramp onset temperature.
- Residues: canonical cleaned mass at the 1000 K analytical boundary; for Air
  also the uncorrected instrument mass at 1000 K, which equals the constant
  terminal offset subtracted by the canonical pipeline.

Output: ``results/kinetics/Table1_TG_DTG_descriptors.csv``.
"""

from __future__ import annotations

import openpyxl
import pandas as pd

import numpy as np

from alc_core import BETAS, GRID, RESULTS_DIR, canonical_clean_curve, canonical_interpolated_mass, clean_source_path, first_crossing_T

DTG_THRESHOLD = 0.05  # % K^-1


def authoritative_t50() -> dict[tuple[str, int], float]:
    workbook = openpyxl.load_workbook(clean_source_path(), read_only=True, data_only=True)
    rows = list(workbook["Kinetic_Talpha"].iter_rows(values_only=True))
    header_index = next(i for i, row in enumerate(rows) if row and "atmosphere" in [str(v).strip() for v in row if v is not None])
    values = {}
    for row in rows[header_index + 1:]:
        if not row or row[0] not in ("N2", "Air"):
            break
        if row[1] is not None and abs(float(row[1]) - 0.5) < 1e-9:
            for beta, value in zip(BETAS, row[2:5]):
                values[(row[0], beta)] = float(value)
    return values


def main() -> None:
    t50 = authoritative_t50()
    peaks = pd.read_csv(RESULTS_DIR / "Figure2_Threshold_Sensitivity.csv")
    peaks = peaks[(peaks.threshold_fraction_nominal - 0.90).abs() < 1e-9].set_index(["atmosphere", "beta_C_per_min"])
    rows = []
    for atm in ("N2", "Air"):
        for beta in BETAS:
            clean, offset_1000 = canonical_clean_curve(atm, beta)
            interpolated, _ = canonical_interpolated_mass(atm, beta)
            uncorrected_1000 = float(interpolated[-1]) + float(offset_1000)
            peak = peaks.loc[(atm, beta)]
            start = max(350.0, float(peak.onset_temperature_K) + 20.0)
            plotted = clean[clean.temperature_K >= start]
            above = plotted[plotted.dtg_pct_per_K > DTG_THRESHOLD]
            runs = int(np.sum(np.diff(np.r_[0, (plotted.dtg_pct_per_K > DTG_THRESHOLD).astype(int).to_numpy(), 0]) == 1))
            mass = clean.mass_clean_pct.to_numpy()
            m_f = float(mass[-1])
            alpha_whole = (100.0 - mass) / (100.0 - m_f)
            m_onset = float(np.interp(float(peak.onset_temperature_K), GRID, mass))
            alpha_ramp = (m_onset - mass) / (m_onset - m_f)
            rows.append({
                "atmosphere": atm,
                "beta_C_per_min": beta,
                "T_alpha_0p5_K_authoritative": t50[(atm, beta)],
                "principal_DTG_peak_T_K": float(peak.principal_peak_temperature_K),
                "principal_DTG_peak_minus_dm_dT_pct_per_K": float(peak.principal_peak_dtg_pct_per_K),
                "interval_threshold_start_K": float(above.temperature_K.min()),
                "interval_threshold_end_K": float(above.temperature_K.max()),
                "interval_threshold_n_segments": runs,
                "interval_A_T_alpha_0p05_K": first_crossing_T(GRID, alpha_whole, 0.05),
                "interval_A_T_alpha_0p95_K": first_crossing_T(GRID, alpha_whole, 0.95),
                "interval_B_T_alpha_ramp_0p05_K": first_crossing_T(GRID, alpha_ramp, 0.05),
                "interval_B_T_alpha_ramp_0p95_K": first_crossing_T(GRID, alpha_ramp, 0.95),
                "m_onset_cleaned_pct": m_onset,
                "residue_at_1000K_cleaned_pct": float(clean.mass_clean_pct.iloc[-1]),
                "uncorrected_instrument_mass_at_1000K_pct": uncorrected_1000,
                "terminal_offset_subtracted_pct": float(offset_1000),
                "DTG_threshold_pct_per_K": DTG_THRESHOLD,
                "DTG_display_start_K": start,
            })
    table = pd.DataFrame(rows)
    table.to_csv(RESULTS_DIR / "Table1_TG_DTG_descriptors.csv", index=False)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
