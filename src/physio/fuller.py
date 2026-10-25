"""Apple Watch activity and intensity prediction on Fuller et al. (2021) data.

The public CSV has one row per minute-level record for 46 participants who
wore an Apple Watch Series 2 and a Fitbit Charge HR2 through a lab protocol:
lying, sitting, self-paced walking, and treadmill running at 3, 5 and 7 METs
(the MET level is the protocol target, set with indirect calorimetry).

The file has no participant id column. Rows are grouped into participants
by the (age, gender, height, weight) tuple, which is constant within a
person in this file. Grouped cross-validation keeps every row of a person
in one fold, so the score reflects a new wearer rather than a new minute
of a wearer the model has already seen.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .cv import score_folds

HR_FEATURES = ["hear_rate", "norm_heart", "intensity_karvonen"]
ALL_FEATURES = [
    "age", "gender", "height", "weight",
    "steps", "hear_rate", "calories", "distance",
    "entropy_heart", "entropy_setps", "resting_heart", "corr_heart_steps",
    "norm_heart", "intensity_karvonen", "sd_norm_heart", "steps_times_distance",
]
ACTIVITY_ORDER = ["Lying", "Sitting", "Self Pace walk", "Running 3 METs", "Running 5 METs", "Running 7 METs"]
RUN_LEVELS = ["Running 3 METs", "Running 5 METs", "Running 7 METs"]
SEED = 410


def load(path: str | Path, device: str = "apple watch") -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.drop(columns=[c for c in ("Unnamed: 0", "X1") if c in df.columns])
    df = df[df["device"] == device].copy()
    key = df[["age", "gender", "height", "weight"]].astype(str).agg("|".join, axis=1)
    df["participant"] = pd.factorize(key)[0]
    df["activity"] = pd.Categorical(df["activity"], categories=ACTIVITY_ORDER, ordered=True)
    return df.reset_index(drop=True)


def _logistic():
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))


def _forest():
    return RandomForestClassifier(n_estimators=200, random_state=SEED, n_jobs=-1)


def models() -> dict:
    """Each model family on both feature sets, so model and features are not confounded."""
    return {
        "majority class": (DummyClassifier(strategy="most_frequent"), HR_FEATURES),
        "logistic, HR features only": (_logistic(), HR_FEATURES),
        "logistic, all features": (_logistic(), ALL_FEATURES),
        "random forest, HR features only": (_forest(), HR_FEATURES),
        "random forest, all features": (_forest(), ALL_FEATURES),
    }


def evaluate(df: pd.DataFrame, target_rows: pd.Series | None = None, n_splits: int = 5) -> pd.DataFrame:
    """Score each model with grouped (by participant) and plain stratified K-fold.

    Scores are the mean and SD over the 5 test folds.
    """
    data = df if target_rows is None else df[target_rows]
    y = data["activity"].astype(str).to_numpy()
    groups = data["participant"].to_numpy()
    splitters = {
        "grouped by participant": GroupKFold(n_splits=n_splits).split(data, y, groups),
        "random rows (stratified)": StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=SEED).split(data, y),
    }
    rows = []
    for split_name, split in splitters.items():
        folds = list(split)
        for model_name, (model, cols) in models().items():
            X = data[cols].to_numpy()
            rows.append({
                "split": split_name,
                "model": model_name,
                "n_rows": len(y),
                "n_participants": int(len(np.unique(groups))),
                **score_folds(model, X, y, folds),
            })
    return pd.DataFrame(rows)


def grouped_confusion(df: pd.DataFrame, n_splits: int = 5) -> pd.DataFrame:
    """Row-normalized confusion matrix for the random forest, participant-grouped folds."""
    y = df["activity"].astype(str).to_numpy()
    X = df[ALL_FEATURES].to_numpy()
    preds = np.empty_like(y)
    for train, test in GroupKFold(n_splits=n_splits).split(X, y, df["participant"]):
        model = _forest()
        model.fit(X[train], y[train])
        preds[test] = model.predict(X[test])
    table = pd.crosstab(pd.Series(y, name="true"), pd.Series(preds, name="predicted"), normalize="index")
    return table.reindex(index=ACTIVITY_ORDER, columns=ACTIVITY_ORDER, fill_value=0.0)


def activity_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Measured HR and Karvonen intensity by protocol activity (Apple Watch)."""
    g = df.groupby("activity", observed=True)
    out = pd.DataFrame({
        "n_rows": g.size(),
        "n_participants": g["participant"].nunique(),
        "hr_median": g["hear_rate"].median(),
        "hr_q25": g["hear_rate"].quantile(0.25),
        "hr_q75": g["hear_rate"].quantile(0.75),
        "karvonen_median": g["intensity_karvonen"].median(),
        "steps_median": g["steps"].median(),
    })
    return out.reset_index()


def run(path: str | Path) -> dict:
    df = load(path)
    all_scores = evaluate(df).assign(task="6 activities")
    run_scores = evaluate(df, df["activity"].isin(RUN_LEVELS)).assign(task="3 running intensities")
    return {
        "df": df,
        "scores": pd.concat([all_scores, run_scores], ignore_index=True),
        "confusion": grouped_confusion(df),
        "summary": activity_summary(df),
    }
