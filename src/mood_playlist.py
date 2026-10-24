"""Mood playlist helper from the later Spotifyanalysis notebooks.

Maps a short adjective to a valence band, then ranks tracks inside that
band by the sum of z-scored danceability, energy, acousticness,
instrumentalness, and liveness. This is a heuristic, not a psychology
result.
"""

from __future__ import annotations

import pandas as pd
from scipy.stats import zscore

MOOD_MAPPING = {
    "Happy": ["happy", "excited", "proud", "nostalgic"],
    "Satisfied": ["satisfied", "calm"],
    "Frustrated": [
        "frustrated",
        "angry",
        "confused",
        "disgusted",
        "afraid",
        "ashamed",
        "awkward",
        "jealous",
    ],
    "Anxious": ["anxious", "surprised"],
    "Bored": ["bored"],
    "Sad": ["sad"],
}

VALENCE_MAPPING = {
    "Happy": (0.6, 1.0),
    "Satisfied": (0.5, 0.8),
    "Frustrated": (0.0, 0.4),
    "Anxious": (0.3, 0.5),
    "Bored": (0.2, 0.4),
    "Sad": (0.0, 0.3),
    "Unknown": (0.4, 0.6),
}

SCORE_FEATURES = [
    "danceability",
    "energy",
    "acousticness",
    "instrumentalness",
    "liveness",
]


def map_characteristics_to_mood(characteristics: str) -> str:
    text = characteristics.lower()
    for mood, words in MOOD_MAPPING.items():
        if any(word in text for word in words):
            return mood
    return "Unknown"


def create_playlist(df: pd.DataFrame, user_input: str, n: int = 20) -> pd.DataFrame:
    mood = map_characteristics_to_mood(user_input)
    low, high = VALENCE_MAPPING[mood]
    mood_data = df[df["valence"].between(low, high)].copy()
    if mood_data.empty:
        return mood_data.assign(mood=mood, score=pd.Series(dtype=float))
    mood_data[SCORE_FEATURES] = mood_data[SCORE_FEATURES].apply(zscore)
    mood_data["score"] = mood_data[SCORE_FEATURES].sum(axis=1)
    mood_data = mood_data.sort_values("score", ascending=False).head(n)
    mood_data["mood"] = mood
    return mood_data[["artist_name", "track_name", "valence", "tempo", "score", "mood"]]
