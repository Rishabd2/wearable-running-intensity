"""Heart-rate response to running speed in graded treadmill tests (Mongin et al., 2021).

``test_measure.csv`` has one row per breath for 992 maximal tests: time (s),
treadmill speed (km/h) and heart rate (bpm), among others. Tests start with
walking at 5 km/h, speed then rises (steps of 0.5 to 1 km/h, or a ramp)
until exhaustion, and the treadmill drops back to 5 km/h for recovery.

Per test the pipeline measures:

* ``hr_peak``: highest heart rate (5-breath rolling median, to drop single
  breath artifacts). Because these are maximal tests this is used as HRmax.
* ``hr_speed_slope``: OLS slope of HR on speed during the running part of
  the effort, in bpm per km/h.
* ``speed_at_Zk``: treadmill speed when HR first reaches the lower bound of
  zone k (60, 70, 80, 90 percent of HRmax).
* ``hrr60``: heart-rate recovery, HR at the end of effort minus HR 60 s later.

HR lags a change in speed by tens of seconds, so ``speed_at_Zk`` is the
speed on the belt at the moment HR crossed the bound, not a steady state.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold

from .zones import ZONE_BOUNDS, ZONE_NAMES, zone_of

SMOOTH = 5
MIN_AGE = 18
RUN_SPEED_KMH = 7.0  # below this the belt speed is a walk for most adults


def load(measure_path: str | Path, info_path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    measure = pd.read_csv(measure_path)
    info = pd.read_csv(info_path)
    measure = measure.dropna(subset=["HR", "Speed"]).sort_values(["ID_test", "time"])
    measure["hr_s"] = measure.groupby("ID_test")["HR"].transform(
        lambda s: s.rolling(SMOOTH, center=True, min_periods=1).median()
    )
    return measure, info


def _effort_end(test: pd.DataFrame) -> int:
    """Positional index of the last sample at peak speed."""
    speed = test["Speed"].to_numpy()
    return int(np.flatnonzero(speed == speed.max())[-1])


def per_test(test: pd.DataFrame) -> dict:
    speed = test["Speed"].to_numpy()
    hr = test["hr_s"].to_numpy()
    t = test["time"].to_numpy()
    end = _effort_end(test)
    effort_hr, effort_speed = hr[: end + 1], speed[: end + 1]
    hr_peak = float(np.nanmax(hr))
    out = {
        "ID_test": test["ID_test"].iloc[0],
        "ID": test["ID"].iloc[0],
        "hr_peak": hr_peak,
        "hr_start": float(hr[0]),
        "peak_speed": float(speed.max()),
        "effort_s": float(t[end] - t[0]),
    }
    running = effort_speed >= RUN_SPEED_KMH
    if running.sum() >= 10 and np.ptp(effort_speed[running]) > 0:
        out["hr_speed_slope"] = float(np.polyfit(effort_speed[running], effort_hr[running], 1)[0])
    else:
        out["hr_speed_slope"] = np.nan
    for bound, name in zip(ZONE_BOUNDS[1:-1], ZONE_NAMES[1:]):
        hit = np.flatnonzero(effort_hr >= bound * hr_peak)
        out[f"speed_at_{name}"] = float(effort_speed[hit[0]]) if len(hit) else np.nan
    later = np.flatnonzero(t >= t[end] + 60)
    out["hrr60"] = float(hr[end] - hr[later[0]]) if len(later) and t[later[0]] - t[end] <= 75 else np.nan
    return out


def summarize_tests(measure: pd.DataFrame, info: pd.DataFrame) -> pd.DataFrame:
    rows = [per_test(test) for _, test in measure.groupby("ID_test", sort=False)]
    tests = pd.DataFrame(rows).merge(info[["ID_test", "Age", "Sex", "Weight", "Height"]], on="ID_test")
    return tests[tests["Age"] >= MIN_AGE].reset_index(drop=True)


def zone_speed_table(tests: pd.DataFrame) -> pd.DataFrame:
    """Population distribution of the belt speed at which each zone was first reached."""
    rows = []
    for name in ZONE_NAMES[1:]:
        col = tests[f"speed_at_{name}"].dropna()
        rows.append({
            "zone": name,
            "n_tests": int(col.size),
            "speed_median": float(col.median()),
            "speed_q25": float(col.quantile(0.25)),
            "speed_q75": float(col.quantile(0.75)),
        })
    peak = tests["peak_speed"]
    rows.append({"zone": "peak", "n_tests": int(peak.size), "speed_median": float(peak.median()),
                 "speed_q25": float(peak.quantile(0.25)), "speed_q75": float(peak.quantile(0.75))})
    return pd.DataFrame(rows)


def zone_samples(measure: pd.DataFrame, tests: pd.DataFrame) -> pd.DataFrame:
    """Effort-phase breaths with their measured HR zone, for the prediction task."""
    keep = measure[measure["ID_test"].isin(tests["ID_test"])]
    parts = []
    for _, test in keep.groupby("ID_test", sort=False):
        parts.append(test.iloc[: _effort_end(test) + 1])
    effort = pd.concat(parts).merge(tests[["ID_test", "hr_peak", "Age", "Sex", "Weight", "Height"]], on="ID_test")
    effort["elapsed_s"] = effort["time"] - effort.groupby("ID_test")["time"].transform("min")
    effort["zone"] = zone_of(effort["hr_s"] / effort["hr_peak"]).to_numpy()
    return effort


def predict_zone(effort: pd.DataFrame, n_splits: int = 5, seed: int = 410, every: int = 5) -> pd.DataFrame:
    """Predict the HR zone of a breath without using HR, grouped by participant.

    Every ``every``-th breath is kept (about one sample per 10 s). Neighboring
    breaths are nearly identical, so this cuts run time without changing what
    the model can learn.
    """
    effort = effort.iloc[::every]
    y = effort["zone"].to_numpy()
    groups = effort["ID"].to_numpy()
    specs = {
        "majority class": (DummyClassifier(strategy="most_frequent"), ["Speed"]),
        "logistic, speed only": (LogisticRegression(max_iter=2000), ["Speed"]),
        "gradient boosting, speed + elapsed time + age/sex/size": (
            HistGradientBoostingClassifier(random_state=seed),
            ["Speed", "elapsed_s", "Age", "Sex", "Weight", "Height"],
        ),
    }
    folds = list(GroupKFold(n_splits=n_splits).split(effort, y, groups))
    rows = []
    for name, (model, cols) in specs.items():
        X = effort[cols].to_numpy()
        preds = np.empty_like(y)
        for train, test in folds:
            model.fit(X[train], y[train])
            preds[test] = model.predict(X[test])
        rows.append({
            "split": "grouped by participant",
            "model": name,
            "n_rows": len(y),
            "n_participants": int(len(np.unique(groups))),
            "accuracy": accuracy_score(y, preds),
            "macro_f1": f1_score(y, preds, average="macro"),
        })
    return pd.DataFrame(rows)


def run(measure_path: str | Path, info_path: str | Path) -> dict:
    measure, info = load(measure_path, info_path)
    tests = summarize_tests(measure, info)
    effort = zone_samples(measure, tests)
    return {
        "tests": tests,
        "zone_speeds": zone_speed_table(tests),
        "zone_scores": predict_zone(effort).assign(task="HR zone per breath (no HR input)"),
        "effort": effort,
    }
