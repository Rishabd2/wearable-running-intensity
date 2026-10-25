"""Cross-validation scoring shared by the Apple Watch and treadmill models."""

from __future__ import annotations

import numpy as np
from sklearn.base import clone
from sklearn.metrics import accuracy_score, f1_score


def score_folds(model, X: np.ndarray, y: np.ndarray, folds: list) -> dict:
    """Fit a fresh copy of ``model`` per fold; return mean and SD of fold accuracy and macro F1."""
    acc, f1 = [], []
    for train, test in folds:
        fitted = clone(model).fit(X[train], y[train])
        pred = fitted.predict(X[test])
        acc.append(accuracy_score(y[test], pred))
        f1.append(f1_score(y[test], pred, average="macro"))
    return {
        "accuracy": float(np.mean(acc)),
        "accuracy_sd": float(np.std(acc, ddof=1)),
        "macro_f1": float(np.mean(f1)),
        "macro_f1_sd": float(np.std(f1, ddof=1)),
        "n_folds": len(folds),
    }
