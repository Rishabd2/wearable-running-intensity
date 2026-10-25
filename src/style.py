"""Shared plot style for the physiology figures and the Spotify appendix figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

INK = "#1b1b1b"
MUTED = "#5c5c5c"
ACCENT = "#2f5d50"
ACCENT_2 = "#b45a3c"
GRID = "#e6e2d8"
PAPER = "#f7f4ee"


def _style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica Neue", "Helvetica", "DejaVu Sans"],
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "axes.titlepad": 10,
        "axes.facecolor": PAPER,
        "figure.facecolor": "white",
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "grid.color": GRID,
    })
    sns.set_theme(style="whitegrid", rc=plt.rcParams)


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
