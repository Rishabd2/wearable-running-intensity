"""Figures for the physiology half, drawn from the tables in ``results/tables``.

``python -m src.physio`` writes the tables and then calls this module.
``python -m src.physio.figures`` redraws the figures from the committed
tables alone, without the raw data.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from ..clean import clean_tracks, load_raw
from ..plot import ACCENT, ACCENT_2, INK, MUTED, _save, _style
from .zones import ZONE_BOUNDS, ZONE_NAMES

ZONE_COLORS = ["#c9d8cf", "#9dbcab", "#6f9f86", "#b8826b", "#b45a3c"]
TASKS = ["6 activities", "3 running intensities", "HR zone per breath (no HR input)"]
TASK_TITLES = {
    "6 activities": "Apple Watch: 6 activities",
    "3 running intensities": "Apple Watch: 3 running intensities",
    "HR zone per breath (no HR input)": "Treadmill: HR zone without HR",
}


def prediction_scores(scores: pd.DataFrame, dest: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.6))
    for ax, task in zip(axes, TASKS):
        sub = scores[scores["task"] == task]
        grouped = sub[sub["split"] == "grouped by participant"].reset_index(drop=True)
        models = grouped["model"].tolist()
        y = np.arange(len(models))
        ax.barh(y + 0.18, grouped["macro_f1"], height=0.34, color=ACCENT, label="grouped by participant",
                xerr=grouped["macro_f1_sd"], error_kw={"ecolor": INK, "lw": 0.8, "capsize": 2})
        rand = sub[sub["split"] == "random rows (stratified)"]
        if not rand.empty:
            rand = rand.set_index("model").loc[models]
            ax.barh(y - 0.18, rand["macro_f1"], height=0.34, color="#c8c2b4",
                    label="random rows (same wearer in train and test)")
        for yi, v, sd in zip(y, grouped["macro_f1"], grouped["macro_f1_sd"]):
            ax.text(v + sd + 0.015, yi + 0.18, f"{v:.2f}", va="center", fontsize=9, color=INK)
        ax.set_yticks(y)
        ax.set_yticklabels([m.replace(", ", ",\n") for m in models], fontsize=8.5)
        ax.set_xlim(0, 1)
        ax.set_xlabel("Macro F1, mean of 5 folds (bar: fold SD)")
        ax.set_title(TASK_TITLES[task], fontsize=11)
    axes[0].legend(frameon=False, fontsize=8, loc="lower right")
    fig.suptitle("Participant-held-out scores (green) are the headline; random-row splits shown for contrast", y=1.02)
    fig.tight_layout()
    _save(fig, dest)


def hr_vs_speed(stats: pd.DataFrame, n_tests: int, dest: Path) -> None:
    x = stats["speed_bin"]
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    for lo, hi, color, name in zip(ZONE_BOUNDS[:-1], ZONE_BOUNDS[1:], ZONE_COLORS, ZONE_NAMES):
        ax.axhspan(lo, hi, color=color, alpha=0.35, lw=0)
        ax.text(x.max() + 0.4, (lo + hi) / 2, name, va="center", fontsize=9, color=MUTED)
    ax.fill_between(x, stats["frac_hrmax_q25"], stats["frac_hrmax_q75"], color=ACCENT, alpha=0.25, lw=0,
                    label="interquartile range")
    ax.plot(x, stats["frac_hrmax_median"], color=ACCENT, lw=2, marker="o", ms=4, label="median")
    ax.set_ylim(0.45, 1.02)
    ax.set_xlim(x.min() - 0.5, x.max() + 1.2)
    ax.set_xlabel("Treadmill speed (km/h)")
    ax.set_ylabel("Heart rate / test peak HR")
    ax.set_title(f"HR vs speed during the effort phase, {n_tests} adult treadmill tests")
    ax.legend(frameon=False, loc="lower right")
    _save(fig, dest)


def cadence_vs_speed(trials: pd.DataFrame, summary: dict, dest: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    for _, runner in trials.groupby("subject"):
        ax.plot(runner["speed_kmh"], runner["cadence_spm"], color="#b9b3a6", lw=0.8, alpha=0.8, marker="o", ms=2.5)
    xs = np.linspace(*summary["speed_range_kmh"], 20)
    ax.plot(xs, summary["intercept"] + summary["slope_spm_per_kmh"] * xs, color=ACCENT_2, lw=2.4,
            label=f"mixed model: {summary['slope_spm_per_kmh']:.2f} steps/min per km/h")
    ax.set_xlabel("Treadmill speed (km/h)")
    ax.set_ylabel("Cadence (steps/min, from vertical force)")
    ax.set_title(f"Cadence vs speed, {trials['subject'].nunique()} runners, {len(trials)} trials")
    ax.legend(frameon=False, loc="upper left")
    _save(fig, dest)


def tempo_zone_map(table: pd.DataFrame, tracks: pd.DataFrame, dest: Path) -> None:
    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    bins = np.arange(50, 221, 4)
    ax.hist(tracks["tempo"], bins=bins, color=ACCENT, alpha=0.75, label="Spotify track tempo")
    ax.hist(2 * tracks["tempo"], bins=bins, color="#c8c2b4", alpha=0.6, label="2 x tempo (one beat per two steps)")
    top = ax.get_ylim()[1]
    for k, ((_, row), color) in enumerate(zip(table.iterrows(), ZONE_COLORS[1:])):
        lo, hi = (float(v) for v in row["cadence_spm_mapped"].split("-"))
        hatch = "//" if bool(row["extrapolated"]) else None
        ax.axvspan(lo, hi, facecolor=color, alpha=0.55, lw=0, hatch=hatch, edgecolor="white")
        label = row["zone"] + ("*" if bool(row["extrapolated"]) else "")
        ax.text((lo + hi) / 2, top * (0.97 if k % 2 == 0 else 0.90), label, ha="center", va="top",
                fontsize=9, color=INK)
    ax.set_xlabel("Beats per minute (tempo) and steps per minute (mapped cadence band)")
    ax.set_ylabel(f"Tracks (n = {len(tracks)})")
    ax.set_title("Mapped cadence band per HR zone over the Spotify tempo distribution\n"
                 "(cross-dataset mapping, not a measured effect of music)", fontsize=11)
    ax.text(0.99, 0.62, "* hatched: zone speed band extends\noutside the 9.0-16.2 km/h cadence data",
            transform=ax.transAxes, ha="right", fontsize=8, color=MUTED)
    ax.legend(frameon=False, loc="upper left")
    _save(fig, dest)


def confusion(table: pd.DataFrame, dest: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.8))
    sns.heatmap(table, annot=True, fmt=".2f", cmap="Greens", vmin=0, vmax=1, cbar=False, ax=ax)
    ax.set_title("Apple Watch activity, random forest, participant-grouped CV\n(row-normalized)")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Protocol activity")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right")
    _save(fig, dest)


def write_all(tables: str | Path, dest: str | Path, tracks_csv: str | Path) -> list[Path]:
    _style()
    tables, dest = Path(tables), Path(dest)
    summary = json.loads((tables / "physio_summary.json").read_text(encoding="utf-8"))
    scores = pd.read_csv(tables / "physio_prediction_scores.csv")
    outputs = {
        "physio_prediction_scores.png": lambda p: prediction_scores(scores, p),
        "physio_hr_vs_speed.png": lambda p: hr_vs_speed(
            pd.read_csv(tables / "physio_hr_by_speed.csv"), summary["treadmill"]["adult_tests"], p),
        "physio_cadence_vs_speed.png": lambda p: cadence_vs_speed(
            pd.read_csv(tables / "physio_cadence_trials.csv"), summary["cadence"], p),
        "physio_tempo_zone_map.png": lambda p: tempo_zone_map(
            pd.read_csv(tables / "physio_tempo_zone_map.csv"), clean_tracks(load_raw(tracks_csv)), p),
        "physio_activity_confusion.png": lambda p: confusion(
            pd.read_csv(tables / "physio_fuller_confusion.csv", index_col=0), p),
    }
    written = []
    for name, draw in outputs.items():
        draw(dest / name)
        written.append(dest / name)
    return written


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    for path in write_all(root / "results" / "tables", root / "results" / "figures",
                          root / "data" / "processed" / "pop_tracks_raw.csv"):
        print(path)
