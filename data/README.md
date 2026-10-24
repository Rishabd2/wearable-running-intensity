# Data

| File | What it is |
| --- | --- |
| `processed/pop_tracks_raw.csv` | Original Spotify pull (`n = 1064`), copied from `spotify-trends-main/extracted_uncleaned_data.csv`. |
| `processed/pop_tracks.csv` | Same table after `src.clean` (unique `track_id`, key name, Major/Minor). Written by `python -m src.analyze`. |

`raw/` is gitignored. Put any Apple Health export there. See `docs/watch-mapping.md` and `docs/data-ethics.md`.
