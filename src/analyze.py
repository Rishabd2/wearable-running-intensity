"""Reproduce the statistical models from the original Spotify trends notebook.

The two-sample energy test is stored twice: as the notebook computed it,
and as a standard two-sample t-test on the same means. The notebook SE
formula and df=33 are kept so the published p=0.995 can be regenerated.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import t, ttest_ind
from sklearn.model_selection import train_test_split

from .clean import FEATURE_COLS, clean_tracks, load_raw

OLS_FORMULA = "energy ~ loudness + valence + liveness + key_name + acousticness + time_signature"
LOGIT_FORMULA = "mode ~ tempo + energy + danceability + valence + time_signature"


def notebook_energy_test(major: pd.Series, minor: pd.Series) -> dict:
    mean_major = float(major.mean())
    mean_minor = float(minor.mean())
    se_major = float(major.std() / np.sqrt(len(major)))
    se_minor = float(minor.std() / np.sqrt(len(minor)))
    diff = mean_major - mean_minor
    # Formula as written in analysis.ipynb (not the usual SE of a difference).
    denom = float(
        np.sqrt(mean_major**2 / se_major + mean_minor**2 / se_minor)
    )
    test_stat = diff / denom
    p_value = float(2 * (1 - t.cdf(abs(test_stat), df=33)))
    return {
        "n_major": int(len(major)),
        "n_minor": int(len(minor)),
        "mean_major": mean_major,
        "mean_minor": mean_minor,
        "se_major": se_major,
        "se_minor": se_minor,
        "diff": diff,
        "test_stat": float(test_stat),
        "df": 33,
        "p_value": p_value,
    }


def run_analysis(raw_path: str | Path) -> dict:
    raw = load_raw(raw_path)
    df = clean_tracks(raw)
    df = df.assign(key_name=df["key_name"].astype("category"))

    corr = df[FEATURE_COLS].corr()
    dance_corr = corr["danceability"].drop("danceability").sort_values(key=lambda s: s.abs(), ascending=False)

    major = df.loc[df["Major_or_Minor"] == "Major", "energy"]
    minor = df.loc[df["Major_or_Minor"] == "Minor", "energy"]
    notebook_test = notebook_energy_test(major, minor)
    welch = ttest_ind(major, minor, equal_var=False)

    ols = smf.ols(OLS_FORMULA, data=df).fit()
    train, _ = train_test_split(df, test_size=0.2, random_state=25)
    logit = smf.logit(LOGIT_FORMULA, data=train).fit(disp=False)

    results = {
        "n_raw": int(len(raw)),
        "n_unique": int(len(df)),
        "danceability_correlations": {k: float(v) for k, v in dance_corr.items()},
        "danceability_valence_r": float(corr.loc["danceability", "valence"]),
        "energy_by_mode_notebook": notebook_test,
        "energy_by_mode_welch": {
            "statistic": float(welch.statistic),
            "p_value": float(welch.pvalue),
        },
        "ols": {
            "formula": OLS_FORMULA,
            "r_squared": float(ols.rsquared),
            "adj_r_squared": float(ols.rsquared_adj),
            "params": {k: float(v) for k, v in ols.params.items()},
            "pvalues": {k: float(v) for k, v in ols.pvalues.items()},
        },
        "logit": {
            "formula": LOGIT_FORMULA,
            "llr_pvalue": float(logit.llr_pvalue),
            "pseudo_r_squared": float(logit.prsquared),
            "params": {k: float(v) for k, v in logit.params.items()},
            "pvalues": {k: float(v) for k, v in logit.pvalues.items()},
        },
    }
    return {"df": df, "corr": corr, "ols": ols, "logit": logit, "summary": results}


def write_tables(bundle: dict, dest: str | Path) -> None:
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    bundle["corr"].to_csv(dest / "feature_correlations.csv")
    ols_table = pd.DataFrame(
        {
            "term": bundle["ols"].params.index,
            "coef": bundle["ols"].params.values,
            "pvalue": bundle["ols"].pvalues.values,
        }
    )
    ols_table.to_csv(dest / "energy_ols.csv", index=False)
    logit_table = pd.DataFrame(
        {
            "term": bundle["logit"].params.index,
            "coef": bundle["logit"].params.values,
            "pvalue": bundle["logit"].pvalues.values,
        }
    )
    logit_table.to_csv(dest / "mode_logit.csv", index=False)
    (dest / "analysis_summary.json").write_text(
        json.dumps(bundle["summary"], indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    bundle = run_analysis("data/processed/pop_tracks_raw.csv")
    write_tables(bundle, "results/tables")
    bundle["df"].to_csv("data/processed/pop_tracks.csv", index=False)
    print(json.dumps(bundle["summary"], indent=2))
