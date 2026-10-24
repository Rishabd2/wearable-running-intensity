# Methods

This file restates what the original notebook actually did. It does not add new tests.

## Sample

`src/extract_spotify.py` repeats the collection function from `spotify-trends-main/analysis.ipynb`.

1. Query the Spotify search endpoint with `genre:Pop year:2011-2022` plus a random letter.
2. Use a random offset in `0..899` and pick one of the ten returned tracks.
3. Pull audio features for each `track_id`.
4. Write the joined table. The saved sample in this repo is the original CSV (`n = 1064` rows).

The function is seeded, but Spotify search ranking changes, so a new pull will not match the saved table. Reproduce the numbers from `data/processed/pop_tracks_raw.csv`.

## Cleaning

`src/clean.py`:

- Cast numeric feature columns to float.
- Drop duplicate `track_id` values (`n = 821` unique tracks).
- Map `mode` 1 → Major, else Minor.
- Map integer `key` 0–11 to `C` … `B`.

## Analyses that exist

1. **Descriptive.** Pearson correlation among audio features. The original writeup followed danceability because it had the largest correlation with valence.
2. **Two-sample energy test.** Compare mean energy for Major vs Minor. The notebook used
   `sqrt(mean_major^2 / se_major + mean_minor^2 / se_minor)` as the denominator and `df = 33`. `src/analyze.py` reprints that calculation so the published `p ≈ 0.995` can be regenerated. It also stores a Welch t-test on the same two series; that is labeled separately and is not a finding from the original paper.
3. **OLS.** `energy ~ loudness + valence + liveness + key_name + acousticness + time_signature` on all 821 tracks.
4. **Logit.** `mode ~ tempo + energy + danceability + valence + time_signature` on an 80/20 split with `random_state=25`. Backward selection in the notebook left a model the authors called insufficient.

## Mood playlist

`src/mood_playlist.py` is the later notebook helper. An adjective maps to a valence interval. Tracks inside that interval are ranked by the sum of z-scored danceability, energy, acousticness, instrumentalness, and liveness. This is a ranking rule, not an experiment.

## Audio edit

`src/tune.py` is the HarmoniAI prototype: slow pitch/tempo by 5 percent, fade in, add reverb, mix generated rain. It does not read heart rate or running files.
