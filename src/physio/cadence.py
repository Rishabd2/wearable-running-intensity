"""Running cadence from treadmill ground reaction forces (Fukuchi et al., 2017).

Each ``RBDSxxxrunTyyforces.txt`` file holds 30 s of force-plate data at
300 Hz from an instrumented treadmill, recorded at 2.5, 3.5 or 4.5 m/s
(``T25``, ``T35``, ``T45``). Fy is the vertical force. One foot contact is
one step, so cadence in steps per minute is the contact rate times 60.

Contacts are found with a two-threshold (hysteresis) detector on Fy plus a
0.15 s refractory gap, so a noisy flight phase is not counted as an extra
step. Cadence uses the median onset-to-onset interval.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

FS_HZ = 300.0
ON_N = 100.0   # contact starts when Fy rises above this (newtons)
OFF_N = 30.0   # contact ends when Fy falls below this
REFRACTORY_S = 0.15  # a new contact cannot start sooner than this after the last one
NAME_RE = re.compile(r"RBDS(\d{3})runT(\d{2})forces\.txt")


def contact_onsets(fy: np.ndarray, on: float = ON_N, off: float = OFF_N, fs: float = FS_HZ) -> np.ndarray:
    """Sample indices where a new foot contact begins."""
    onsets = []
    gap = int(REFRACTORY_S * fs)
    in_contact = fy[0] > on
    for i, value in enumerate(fy):
        if not in_contact and value > on and (not onsets or i - onsets[-1] >= gap):
            onsets.append(i)
            in_contact = True
        elif in_contact and value < off:
            in_contact = False
    return np.asarray(onsets, dtype=int)


def cadence_spm(fy: np.ndarray, fs: float = FS_HZ) -> float:
    """Steps per minute from the median interval between successive contact onsets.

    The median keeps a missed or doubled contact from shifting the estimate.
    """
    onsets = contact_onsets(fy, fs=fs)
    if len(onsets) < 3:
        return float("nan")
    return 60.0 * fs / float(np.median(np.diff(onsets)))


def load_trials(folder: str | Path) -> pd.DataFrame:
    rows = []
    for path in sorted(Path(folder).glob("RBDS*runT*forces.txt")):
        match = NAME_RE.fullmatch(path.name)
        if not match:
            continue
        fy = pd.read_csv(path, sep="\t", usecols=["Fy"])["Fy"].to_numpy()
        onsets = contact_onsets(fy)
        rows.append({
            "subject": int(match.group(1)),
            "speed_ms": int(match.group(2)) / 10.0,
            "n_contacts": int(len(onsets)),
            "cadence_spm": cadence_spm(fy),
        })
    df = pd.DataFrame(rows)
    df["speed_kmh"] = df["speed_ms"] * 3.6
    return df


def fit_cadence_speed(trials: pd.DataFrame):
    """Mixed model: cadence ~ speed with a random intercept per runner."""
    return smf.mixedlm("cadence_spm ~ speed_kmh", trials.dropna(), groups=trials.dropna()["subject"]).fit()


def by_speed(trials: pd.DataFrame) -> pd.DataFrame:
    g = trials.groupby("speed_ms")["cadence_spm"]
    return pd.DataFrame({
        "n_runners": g.count(),
        "cadence_mean": g.mean(),
        "cadence_sd": g.std(),
        "cadence_q10": g.quantile(0.10),
        "cadence_q90": g.quantile(0.90),
    }).reset_index().assign(speed_kmh=lambda d: d["speed_ms"] * 3.6)


def run(folder: str | Path) -> dict:
    trials = load_trials(folder)
    model = fit_cadence_speed(trials)
    return {
        "trials": trials,
        "by_speed": by_speed(trials),
        "model": model,
        "intercept": float(model.fe_params["Intercept"]),
        "slope_per_kmh": float(model.fe_params["speed_kmh"]),
        "slope_se": float(model.bse_fe["speed_kmh"]),
        "speed_range_kmh": (float(trials["speed_kmh"].min()), float(trials["speed_kmh"].max())),
    }
