"""Pull a pseudo-random pop-track sample from the Spotify Web API.

The original collection used genre=Pop, years 2011-2022, and wrote
`extracted_uncleaned_data.csv`. Credentials come from the environment,
never from source.
"""

from __future__ import annotations

import os
import random
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def make_client():
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials

    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env")
    return spotipy.Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret,
        )
    )


def get_random_songs(sp, number_of_songs=900, genre="Pop", year_range="2011-2022", random_state=100):
    random.seed(random_state)
    random_offset = random.sample(range(0, 900), number_of_songs)
    chars = "abcdefghijklmnopqrstuvwxyz"
    random_char = random.choices(chars, k=number_of_songs)
    random_id = random.choices(range(0, 10), k=number_of_songs)

    rows = []
    for i in range(number_of_songs):
        results = sp.search(
            q=f"genre:{genre} year:{year_range} {random_char[i]}",
            type="track",
            offset=random_offset[i],
        )
        items = results["tracks"]["items"]
        if not items:
            continue
        track = items[min(random_id[i], len(items) - 1)]
        rows.append(
            {
                "track_id": track["id"],
                "track_name": track["name"],
                "artist_id": track["artists"][0]["id"],
                "artist_name": track["artists"][0]["name"],
                "album_id": track["album"]["id"],
                "album_name": track["album"]["name"],
                "release_date": track["album"]["release_date"],
            }
        )
    return pd.DataFrame(rows)


def get_song_info(sp, track_id: str) -> dict:
    features = sp.audio_features(track_id)[0]
    if not features:
        return {}
    return {
        "track_id": track_id,
        "tempo": features["tempo"],
        "danceability": features["danceability"],
        "energy": features["energy"],
        "key": features["key"],
        "loudness": features["loudness"],
        "acousticness": features["acousticness"],
        "instrumentalness": features["instrumentalness"],
        "liveness": features["liveness"],
        "valence": features["valence"],
        "mode": features["mode"],
        "speechiness": features["speechiness"],
        "type": features["type"],
        "time_signature": features["time_signature"],
    }


def extract(dest: str | Path, number_of_songs: int = 900) -> pd.DataFrame:
    sp = make_client()
    tracks = get_random_songs(sp, number_of_songs=number_of_songs)
    feature_rows = [get_song_info(sp, tid) for tid in tracks["track_id"]]
    features = pd.DataFrame([row for row in feature_rows if row])
    merged = tracks.merge(features, on="track_id", how="left")
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(dest, index=False)
    return merged


if __name__ == "__main__":
    extract("data/processed/pop_tracks_raw.csv")
