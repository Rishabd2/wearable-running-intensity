# Data and privacy

## What is in git

`data/processed/pop_tracks_raw.csv` is a Spotify audio-feature table: public track IDs, titles, artist names, and the API feature vector (tempo, danceability, energy, and so on). It is not personal listening history and it is not health data.

Spotify client secrets are not in the repo. Use `.env.example`. Older notebooks in Downloads had a dummy client id/secret in source; those strings were not copied here.

## What is not in git

No Apple Watch export, HealthKit XML, workout CSV, or heart-rate series was found under `/Users/rishabdoshi/Downloads` or in nearby project folders. Those files are personal health records.

If a Watch export shows up later:

- Keep the raw file out of git (`data/raw/` is gitignored).
- Strip name, email, device serial, GPS, and any other identifier before analysis.
- Commit only aggregated per-run summaries (mean HR, cadence, duration, song tempo) or a synthetic schema example.

## Psychological claims

The CS410 milestone and the mood-playlist helper talk about emotion and valence. Neither file is a controlled study of psychological effect. Do not treat playlist output or the HarmoniAI pitch as clinical evidence.
