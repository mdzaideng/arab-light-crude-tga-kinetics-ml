"""Shared portable utilities for the Arab Light Crude kinetics v6.1 package.

The active scientific preprocessing path is the validated canonical pipeline:
raw time order -> cumulative-max temperature -> 1 K grid (323-1000 K) ->
Air constant terminal offset anchored at 1000 K -> SG smoothing -> N2-only
isotonic monotonicity -> DTG. Air is never isotonic-constrained and no local
artifact bridging is used in kinetic extraction.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from sklearn.isotonic import IsotonicRegression

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data" / "private"
RESULTS_DIR = PACKAGE_ROOT / "results" / "kinetics"
FIG_MAIN_DIR = PACKAGE_ROOT / "figures" / "main"
FIG_SUPP_DIR = PACKAGE_ROOT / "figures" / "supplementary"

RAW_SOURCE_NAME = "Arab_Light_Kinetics_Source_FWO_KAS_Starink.xlsx"
CLEAN_SOURCE_NAME = "Arab_Light_TGA_Canonical_Data.xlsx"

BETAS = (5, 10, 20)
COL_OFFSETS = {5: 0, 10: 11, 20: 22}
GRID = np.arange(323.0, 1001.0, 1.0)
SG_WINDOW_K_DEFAULT = 21
SG_POLYORDER = 3

PDF_METADATA = {
    "Creator": "ALC Kinetics v6.1 reproducible pipeline",
    "CreationDate": None,
    "ModDate": None,
}


def raw_source_path() -> Path:
    path = DATA_DIR / RAW_SOURCE_NAME
    if not path.is_file():
        raise FileNotFoundError(f"Raw source workbook not found at {path}")
    return path


def clean_source_path() -> Path:
    path = DATA_DIR / CLEAN_SOURCE_NAME
    if not path.is_file():
        raise FileNotFoundError(f"Canonical source workbook not found at {path}")
    return path


def load_raw_curve(atmosphere: str, beta: int) -> pd.DataFrame:
    """Load one instrument-recorded time/temperature/mass curve in time order."""
    raw = pd.read_excel(raw_source_path(), sheet_name=atmosphere, header=None)
    data = raw.iloc[2:].reset_index(drop=True).apply(pd.to_numeric, errors="coerce")
    offset = COL_OFFSETS[beta]
    sub = data.iloc[:, [offset, offset + 1, offset + 2, offset + 4]].copy()
    sub.columns = ["temp_C", "temp_K", "time_s", "mass_pct"]
    return sub.dropna(subset=["temp_K", "time_s", "mass_pct"]).reset_index(drop=True)


def canonical_interpolated_mass(atmosphere: str, beta: int) -> tuple[np.ndarray, float]:
    """Steps 1-4 of the validated canonical preprocessing pipeline.

    Returns mass on the fixed 323-1000 K grid and, for Air, the additive
    terminal offset measured at the 1000 K grid boundary before correction.
    For N2 the offset is zero.
    """
    raw = load_raw_curve(atmosphere, beta)
    temperature = np.maximum.accumulate(raw.temp_K.to_numpy(float))
    mass = raw.mass_pct.to_numpy(float)
    grouped = pd.DataFrame({"T": temperature, "m": mass}).groupby("T", as_index=False).m.mean()
    interpolated = np.interp(GRID, grouped["T"].to_numpy(float), grouped["m"].to_numpy(float))

    offset_1000 = 0.0
    if atmosphere == "Air":
        offset_1000 = float(interpolated[-1])
        interpolated = interpolated - offset_1000
    return interpolated, offset_1000


def canonical_clean_curve(
    atmosphere: str,
    beta: int,
    sg_window: int = SG_WINDOW_K_DEFAULT,
    baseline_mode: str = "constant_1000K",
) -> tuple[pd.DataFrame, float]:
    """Validated canonical mass/DTG preprocessing on the fixed 323-1000 K grid.

    baseline_mode is exposed for sensitivity analysis only. The authoritative
    analysis uses ``constant_1000K``. Air remains unconstrained; N2 alone uses
    a non-increasing isotonic constraint after SG smoothing.
    """
    raw = load_raw_curve(atmosphere, beta)
    temperature = np.maximum.accumulate(raw.temp_K.to_numpy(float))
    mass = raw.mass_pct.to_numpy(float)
    grouped = pd.DataFrame({"T": temperature, "m": mass}).groupby("T", as_index=False).m.mean()
    interpolated = np.interp(GRID, grouped["T"].to_numpy(float), grouped["m"].to_numpy(float))

    terminal_offset = 0.0
    if atmosphere == "Air":
        if baseline_mode == "constant_1000K":
            terminal_offset = float(interpolated[-1])
            interpolated = interpolated - terminal_offset
        elif baseline_mode == "none":
            terminal_offset = 0.0
        elif baseline_mode == "mean_last_20":
            terminal_offset = float(interpolated[-20:].mean())
            interpolated = interpolated - terminal_offset
        else:
            raise ValueError(f"Unsupported baseline_mode: {baseline_mode}")

    if sg_window % 2 == 0 or sg_window <= SG_POLYORDER:
        raise ValueError("Savitzky-Golay window must be odd and greater than the polynomial order")
    smoothed = savgol_filter(interpolated, window_length=sg_window, polyorder=SG_POLYORDER, mode="interp")

    if atmosphere == "N2":
        clean_mass = IsotonicRegression(increasing=False, out_of_bounds="clip").fit_transform(GRID, smoothed)
    else:
        clean_mass = smoothed

    dtg = -np.gradient(clean_mass, GRID)
    return pd.DataFrame(
        {
            "temperature_K": GRID,
            "mass_clean_pct": clean_mass,
            "dtg_pct_per_K": dtg,
        }
    ), terminal_offset


def rolling_temperature_slope(raw: pd.DataFrame, slope_window_s: float = 60.0) -> np.ndarray:
    """Centered least-squares dT/dt over a fixed elapsed-time window."""
    time_s = raw.time_s.to_numpy(float)
    temperature_K = raw.temp_K.to_numpy(float)
    slopes = np.full(len(raw), np.nan, dtype=float)
    half = slope_window_s / 2.0
    for i, center in enumerate(time_s):
        mask = (time_s >= center - half) & (time_s <= center + half)
        if mask.sum() < 3:
            continue
        x = time_s[mask]
        y = temperature_K[mask]
        xc = x - x.mean()
        denom = float(np.dot(xc, xc))
        if denom > 0:
            slopes[i] = float(np.dot(xc, y - y.mean()) / denom)
    return slopes


def stable_ramp_onset(
    raw: pd.DataFrame,
    beta: int,
    fraction: float = 0.90,
    min_duration_s: float = 60.0,
    slope_window_s: float = 60.0,
    search_after_s: float = 1800.0,
) -> dict:
    """First post-dwell interval sustained above a fraction of nominal beta."""
    t = raw.time_s.to_numpy(float)
    T = raw.temp_K.to_numpy(float)
    dTdt = rolling_temperature_slope(raw, slope_window_s)
    normalized = dTdt / (beta / 60.0)
    start_idx = int(np.searchsorted(t, search_after_s, side="left"))
    for i in range(start_idx, len(t)):
        if not np.isfinite(normalized[i]) or normalized[i] < fraction:
            continue
        j = i
        while j < len(t) and np.isfinite(normalized[j]) and normalized[j] >= fraction:
            if t[j] - t[i] >= min_duration_s:
                return {
                    "index": i,
                    "onset_time_s": float(t[i]),
                    "onset_temperature_K": float(T[i]),
                    "normalized_rate": float(normalized[i]),
                    "verified_duration_s": float(t[j] - t[i]),
                }
            j += 1
    raise RuntimeError(f"No sustained stable-ramp onset found for beta={beta}, fraction={fraction}")


def first_crossing_T(grid: np.ndarray, alpha: np.ndarray, target: float) -> float:
    """First crossing in forward temperature/time order, with local linear interpolation."""
    for i in range(1, len(alpha)):
        if alpha[i - 1] < target <= alpha[i]:
            fraction = (target - alpha[i - 1]) / (alpha[i] - alpha[i - 1])
            return float(grid[i - 1] + fraction * (grid[i] - grid[i - 1]))
    if alpha[0] >= target:
        return float(grid[0])
    return float("nan")


def save_figure(fig, png_path: Path, pdf_path: Path, dpi: int = 400) -> None:
    """Save publication figures with deterministic PDF metadata and TrueType fonts."""
    fig.savefig(png_path, dpi=dpi, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight", metadata=PDF_METADATA)


PUBLICATION_SERIF = ["Times New Roman", "Liberation Serif", "DejaVu Serif"]


def publication_font_rc() -> dict:
    """Times New Roman (as in the archived kinetics figures), STIX for mathtext.

    Raises RuntimeError when Times New Roman is not installed, so that final
    publication images cannot be produced with a substitute font by mistake.
    Set ALC_ALLOW_FONT_FALLBACK=1 to allow previews with the metric-compatible
    fallbacks (Liberation Serif, then DejaVu Serif); a warning is then printed.
    """
    import os
    from matplotlib import font_manager
    available = {f.name for f in font_manager.fontManager.ttflist}
    if "Times New Roman" not in available:
        if os.environ.get("ALC_ALLOW_FONT_FALLBACK") != "1":
            raise RuntimeError("Times New Roman is not installed. Install it for final figures, "
                               "or set ALC_ALLOW_FONT_FALLBACK=1 for a preview with a fallback font.")
        print("WARNING: Times New Roman not installed; preview uses",
              next((f for f in PUBLICATION_SERIF if f in available), "the Matplotlib default"))
    return {"font.family": "serif", "font.serif": PUBLICATION_SERIF, "mathtext.fontset": "stix"}
