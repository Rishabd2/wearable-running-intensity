# Spotify trends and running physiology

Statistical study of Spotify audio features for pop tracks (2011-2022), plus the leftover pieces of a Watch-linked "better tune" idea. Only the Spotify analysis has data and results. No Apple Watch export was found on disk, so this repo does not claim a tempo-heart-rate finding.

Three threads, kept separate:

1. **Spotify trends.** Pseudo-random pop sample via the Web API. Correlation, a two-sample energy test, OLS for energy, logistic regression for major/minor. Source: `spotify-trends-main/analysis.ipynb`.
2. **Song features to running / HR.** Described as a mapping from tempo (and related features) onto Watch run data. No HealthKit file, workout CSV, or join script turned up. The intended join is in `docs/watch-mapping.md`.
3. **Psychological-effect question.** CS 410 milestone (`paper/CS410_Personalized_Spotify_Milestone.pdf`) matches journal sentiment to playlists. A later notebook ranks tracks by valence bands (`src/mood_playlist.py`). HarmoniAI (`paper/HarmoniAI_Submission.pdf`, `src/tune.py`) edits a song's tempo and adds rain. None of those files is a psychology experiment.

## Research question

The completed study asks how danceability, valence, energy, and mode relate in pop tracks pulled from Spotify. The Watch / psychology questions stay open.

## Data

| Source | What we have | In git? |
| --- | --- | --- |
| Spotify Web API | 1,064 pop rows, 821 unique `track_id`s after de-dupe. Features: tempo, danceability, energy, key, loudness, acousticness, instrumentalness, liveness, valence, mode, speechiness, time_signature. | `data/processed/pop_tracks_raw.csv` (public track metadata, not personal health) |
| Apple Watch / HealthKit | Nothing local | No. Recipe only: `docs/watch-mapping.md` |

A new API pull will not match this table. Spotify search ranking changes. Reproduce from the saved CSV.

## Methods

Collection, cleaning, and the four models are written out in `docs/methods.md`. Short version:

- Search `genre:Pop year:2011-2022` with a random letter and offset, then request audio features.
- Drop duplicate tracks. Map `mode` 1 → Major.
- Pearson correlations. OLS: `energy ~ loudness + valence + liveness + key + acousticness + time_signature`.
- Logit for `mode` on an 80/20 split (`random_state=25`).
- The notebook's energy two-sample p-value used a nonstandard denominator and `df = 33`. `src/analyze.py` reprints that calculation so `p ≈ 0.995` can be regenerated. It does not replace the original claim.

## Results that exist

Regenerated from the saved CSV (`python -m src`). Same numbers as the original notebook.

- Danceability's largest correlation is valence, **r = 0.42**. Other danceability correlations: acousticness −0.27, loudness 0.23, energy 0.20, tempo −0.10.
- Mean energy: Major 0.606 (n = 469), Minor 0.660 (n = 352). The notebook reported p = 0.995 and concluded there was not enough evidence of an association with scale.
- Energy OLS **R² = 0.722** (adj. 0.716). Loudness, valence, liveness, acousticness, and time signature have p < 0.05. Most key dummies do not. Key F does (p = 0.003).
- Major/minor logit: McFadden pseudo-R² = 0.020. The original writeup called the model insufficient.

Figures:

- `results/figures/feature_correlations.png`
- `results/figures/danceability_vs_valence.png`
- `results/figures/energy_by_mode.png`
- `results/figures/energy_ols_coefficients.png`
- `results/figures/tempo_vs_energy.png` (tempo vs Spotify energy only; no heart-rate series)

Tables: `results/tables/`.

Not present: a Watch-joined table, a tempo–HR plot, or a test of psychological effect.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional, only if you re-pull tracks: copy `.env.example` to `.env` and set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`. `src/tune.py` needs `ffmpeg`.

## Usage

```bash
python -m src
```

Writes `data/processed/pop_tracks.csv`, `results/tables/`, and `results/figures/`.

```bash
python -c "from src.analyze import run_analysis; from src.mood_playlist import create_playlist; b=run_analysis('data/processed/pop_tracks_raw.csv'); print(create_playlist(b['df'], 'excited'))"
```

Notebook: `notebooks/01_spotify_trends.ipynb`.

## Reproduce

1. Clone this repo.
2. Install requirements as above.
3. Run `python -m src`.
4. Compare `results/tables/analysis_summary.json` to the values in Results.
5. Do not expect `python -m src.extract_spotify` to recreate the same 821 tracks.

## Ethics

Spotify client secrets stay out of git. Watch / HealthKit dumps stay out of git. See `docs/data-ethics.md`.

## License

MIT. See `LICENSE`. The CS 410 milestone is a course report by Rishab Doshi, Kavin Jindel, and Adit Agarwal. HarmoniAI is a pitch document, not a license grant from a third party.
