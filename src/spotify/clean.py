"""Clean the extracted Spotify pop-track table the same way the original notebook did."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

FLOAT_COLS = [
    "tempo",
    "danceability",
    "energy",
    "loudness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "mode",
    "speechiness",
    "time_signature",
]

FEATURE_COLS = [
    "tempo",
    "danceability",
    "energy",
    "loudness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "mode",
    "speechiness",
    "time_signature",
]


def load_raw(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def clean_tracks(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in FLOAT_COLS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if "key" in out.columns:
        out["key"] = pd.to_numeric(out["key"], errors="coerce")
    out = out.drop_duplicates(subset=["track_id"]).reset_index(drop=True)
    out["Major_or_Minor"] = out["mode"].map({1.0: "Major", 1: "Major"}).fillna("Minor")
    out["key_name"] = out["key"].apply(_key_name)
    return out


def _key_name(value) -> str:
    if pd.isna(value):
        return ""
    idx = int(value)
    if 0 <= idx < len(KEY_NAMES):
        return KEY_NAMES[idx]
    return str(value)


def clean_file(src: str | Path, dest: str | Path) -> pd.DataFrame:
    cleaned = clean_tracks(load_raw(src))
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(dest, index=False)
    return cleaned
