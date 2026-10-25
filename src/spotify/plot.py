"""Figures for the analyses that already exist in the original notebook."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from ..style import ACCENT, ACCENT_2, INK, MUTED, _save, _style
from .analyze import run_analysis
from .clean import FEATURE_COLS

def plot_correlation_heatmap(corr: pd.DataFrame, dest: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.4, 7.0))
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(
        corr,
        mask=mask,
        cmap="RdBu_r",
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.4,
        linecolor="white",
        cbar_kws={"shrink": 0.7, "label": "Pearson r"},
        ax=ax,
    )
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    ax.set_title("Audio-feature correlations, unique pop tracks")
    _save(fig, dest)


def plot_danceability_valence(df: pd.DataFrame, dest: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    palette = {"Major": ACCENT, "Minor": ACCENT_2}
    sns.scatterplot(
        data=df,
        x="valence",
        y="danceability",
        hue="Major_or_Minor",
        palette=palette,
        alpha=0.55,
        s=28,
        edgecolor="none",
        ax=ax,
    )
    sns.regplot(
        data=df,
        x="valence",
        y="danceability",
        scatter=False,
        color=INK,
        line_kws={"linewidth": 1.6},
        ax=ax,
    )
    r = df["danceability"].corr(df["valence"])
    ax.set_title(f"Danceability vs valence (r = {r:.2f})")
    ax.set_xlabel("Valence")
    ax.set_ylabel("Danceability")
    ax.legend(title="Scale", frameon=False)
    _save(fig, dest)


def plot_energy_by_mode(df: pd.DataFrame, dest: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.4, 5.0))
    order = ["Major", "Minor"]
    sns.violinplot(
        data=df,
        x="Major_or_Minor",
        y="energy",
        hue="Major_or_Minor",
        order=order,
        inner="quartile",
        palette={"Major": ACCENT, "Minor": ACCENT_2},
        cut=0,
        legend=False,
        ax=ax,
    )
    means = df.groupby("Major_or_Minor")["energy"].mean()
    for i, scale in enumerate(order):
        ax.scatter([i], [means[scale]], color=INK, zorder=5, s=28)
        ax.text(i + 0.08, means[scale], f"mean {means[scale]:.3f}", color=MUTED, va="center")
    ax.set_title("Energy by major / minor")
    ax.set_xlabel("")
    ax.set_ylabel("Energy")
    _save(fig, dest)


def plot_ols_coefs(ols, dest: Path) -> None:
    params = ols.params.drop("Intercept")
    pvalues = ols.pvalues.drop("Intercept")
    labels = [
        name.replace("key_name[T.", "key ").replace("]", "")
        for name in params.index
    ]
    table = pd.DataFrame({"coef": params.values, "pvalue": pvalues.values}, index=labels)
    table = table.sort_values("coef")
    colors = [ACCENT if p < 0.05 else "#9a9a9a" for p in table["pvalue"]]
    fig, ax = plt.subplots(figsize=(7.4, 5.6))
    ax.barh(table.index, table["coef"], color=colors)
    ax.axvline(0, color=INK, linewidth=0.8)
    ax.set_title("Energy OLS coefficients (green: p < 0.05)")
    ax.set_xlabel("Coefficient")
    _save(fig, dest)


def plot_tempo_energy(df: pd.DataFrame, dest: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    ax.scatter(df["tempo"], df["energy"], s=18, alpha=0.45, c=ACCENT, edgecolors="none")
    ax.set_title("Tempo vs energy, unique pop tracks")
    ax.set_xlabel("Tempo (BPM)")
    ax.set_ylabel("Energy")
    r = df["tempo"].corr(df["energy"])
    ax.text(0.04, 0.96, f"r = {r:.2f}", transform=ax.transAxes, va="top", color=MUTED)
    _save(fig, dest)


def write_figures(raw_path: str | Path, dest: str | Path) -> dict:
    _style()
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    bundle = run_analysis(raw_path)
    df = bundle["df"]
    plot_correlation_heatmap(bundle["corr"].loc[FEATURE_COLS, FEATURE_COLS], dest / "feature_correlations.png")
    plot_danceability_valence(df, dest / "danceability_vs_valence.png")
    plot_energy_by_mode(df, dest / "energy_by_mode.png")
    plot_ols_coefs(bundle["ols"], dest / "energy_ols_coefficients.png")
    plot_tempo_energy(df, dest / "tempo_vs_energy.png")
    return bundle


if __name__ == "__main__":
    write_figures("data/processed/pop_tracks_raw.csv", "results/figures")
