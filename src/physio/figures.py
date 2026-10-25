"""Figures for the physiology half. Every figure is written by ``python -m src.physio``."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from ..plot import ACCENT, ACCENT_2, INK, MUTED, _save, _style
from .zones import ZONE_BOUNDS, ZONE_NAMES

ZONE_COLORS = ["#c9d8cf", "#9dbcab", "#6f9f86", "#b8826b", "#b45a3c"]


def prediction_scores(scores: pd.DataFrame, dest: Path) -> None:
    order = scores[["task", "model"]].drop_duplicates()
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.6), sharey=True)
    for ax, task in zip(axes, ["6 activities", "3 running intensities", "HR zone per breath (no HR input)"]):
        sub = scores[scores["task"] == task]
        models = order[order["task"] == task]["model"].tolist()
        y = np.arange(len(models))
        grouped = sub[sub["split"] == "grouped by participant"].set_index("model").loc[models]
        ax.barh(y + 0.18, grouped["macro_f1"], height=0.34, color=ACCENT, label="grouped by participant")
        rand = sub[sub["split"] == "random rows (stratified)"]
        if not rand.empty:
            rand = rand.set_index("model").loc[models]
            ax.barh(y - 0.18, rand["macro_f1"], height=0.34, color="#c8c2b4", label="random rows (leaks wearer)")
        for yi, v in zip(y, grouped["macro_f1"]):
            ax.text(v + 0.01, yi + 0.18, f"{v:.2f}", va="center", fontsize=9, color=INK)
        ax.set_yticks(y)
        ax.set_yticklabels([m.replace(", ", ",\n") for m in models], fontsize=9)
        ax.set_xlim(0, 1)
        ax.set_xlabel("Macro F1 (5-fold CV)")
        ax.set_title(task, fontsize=11)
    axes[0].legend(frameon=False, fontsize=8, loc="lower right")
    fig.suptitle("Predicting activity, running intensity and HR zone from wearable and treadmill signals", y=1.02)
    _save(fig, dest)


def hr_vs_speed(effort: pd.DataFrame, dest: Path) -> None:
    data = effort.assign(speed_bin=effort["Speed"].round(0), frac=effort["hr_s"] / effort["hr_peak"])
    g = data.groupby("speed_bin")["frac"]
    stats = pd.DataFrame({"n": g.size(), "med": g.median(), "q25": g.quantile(0.25), "q75": g.quantile(0.75)})
    stats = stats[stats["n"] >= 200]
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    for lo, hi, color, name in zip(ZONE_BOUNDS[:-1], ZONE_BOUNDS[1:], ZONE_COLORS, ZONE_NAMES):
        ax.axhspan(lo, hi, color=color, alpha=0.35, lw=0)
        ax.text(stats.index.max() + 0.3, (lo + hi) / 2, name, va="center", fontsize=9, color=MUTED)
    ax.fill_between(stats.index, stats["q25"], stats["q75"], color=ACCENT, alpha=0.25, lw=0, label="interquartile range")
    ax.plot(stats.index, stats["med"], color=ACCENT, lw=2, marker="o", ms=4, label="median")
    ax.set_ylim(0.45, 1.02)
    ax.set_xlabel("Treadmill speed (km/h)")
    ax.set_ylabel("Heart rate / test peak HR")
    n_tests = effort["ID_test"].nunique()
    ax.set_title(f"HR rises with speed in {n_tests} graded treadmill tests (adults)")
    ax.legend(frameon=False, loc="lower right")
    _save(fig, dest)


def cadence_vs_speed(trials: pd.DataFrame, cad: dict, dest: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    for _, runner in trials.groupby("subject"):
        ax.plot(runner["speed_kmh"], runner["cadence_spm"], color="#b9b3a6", lw=0.8, alpha=0.8, marker="o", ms=2.5)
    xs = np.linspace(*cad["speed_range_kmh"], 20)
    ax.plot(xs, cad["intercept"] + cad["slope_per_kmh"] * xs, color=ACCENT_2, lw=2.4,
            label=f"mixed model: {cad['slope_per_kmh']:.2f} spm per km/h")
    ax.set_xlabel("Treadmill speed (km/h)")
    ax.set_ylabel("Cadence (steps/min, from force plate)")
    ax.set_title(f"Cadence vs speed, {trials['subject'].nunique()} runners")
    ax.legend(frameon=False, loc="upper left")
    _save(fig, dest)


def tempo_zone_map(table: pd.DataFrame, tracks: pd.DataFrame, dest: Path) -> None:
    fig, ax = plt.subplots(figsize=(9.0, 5.0))
    bins = np.arange(50, 221, 4)
    ax.hist(tracks["tempo"], bins=bins, color=ACCENT, alpha=0.75, label="Spotify track tempo")
    ax.hist(2 * tracks["tempo"], bins=bins, color="#c8c2b4", alpha=0.6, label="2 x tempo (half-time feel)")
    top = ax.get_ylim()[1]
    for (_, row), color in zip(table.iterrows(), ZONE_COLORS[1:]):
        lo, hi = (float(x) for x in row["cadence_spm_mapped"].split("-"))
        ax.axvspan(lo, hi, color=color, alpha=0.55, lw=0)
        ax.text((lo + hi) / 2, top * 0.97, row["zone"], ha="center", va="top", fontsize=9, color=INK)
    ax.set_xlabel("Beats per minute (tempo) and steps per minute (cadence band)")
    ax.set_ylabel(f"Tracks (n = {len(tracks)})")
    ax.set_title("Mapped cadence band per HR zone over the Spotify tempo distribution\n"
                 "(cross-dataset mapping, not a measured music effect)", fontsize=11)
    ax.legend(frameon=False, loc="upper left")
    _save(fig, dest)


def confusion(table: pd.DataFrame, dest: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.8))
    sns.heatmap(table, annot=True, fmt=".2f", cmap="Greens", vmin=0, vmax=1, cbar=False, ax=ax)
    ax.set_title("Apple Watch activity, random forest, participant-grouped CV")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Protocol activity")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right")
    _save(fig, dest)


def write_all(bundle: dict, dest: str | Path) -> list[Path]:
    _style()
    dest = Path(dest)
    paths = {
        "physio_prediction_scores.png": lambda p: prediction_scores(bundle["scores"], p),
        "physio_hr_vs_speed.png": lambda p: hr_vs_speed(bundle["treadmill"]["effort"], p),
        "physio_cadence_vs_speed.png": lambda p: cadence_vs_speed(bundle["cadence"]["trials"], bundle["cadence"], p),
        "physio_tempo_zone_map.png": lambda p: tempo_zone_map(bundle["tempo_table"], bundle["tracks"], p),
        "physio_activity_confusion.png": lambda p: confusion(bundle["fuller"]["confusion"], p),
    }
    out = []
    for name, draw in paths.items():
        draw(dest / name)
        out.append(dest / name)
    return out
