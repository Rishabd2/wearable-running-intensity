# Data

| Path | What it is | In git |
| --- | --- | --- |
| `processed/pop_tracks_raw.csv` | Spotify pop-track audio features (`n = 1064` rows, 821 unique tracks). | yes |
| `processed/pop_tracks.csv` | Same table after `src.clean`. Written by `python -m src`. | yes |
| `manifest.json` | URLs and published checksums for the physiology downloads. | yes |
| `raw/fuller_apple_watch/` | Fuller et al. Apple Watch / Fitbit CSV (CC0). | no, fetched |
| `raw/malaga_treadmill/` | Malaga treadmill maximal tests (PhysioNet). | no, fetched |
| `raw/fukuchi_running/` | Fukuchi running force-plate trials (CC BY 4.0). | no, fetched |
| `raw/apple_health/export.xml` | Your own Apple Health export, if you add one. | never |

Fetch with `python -m src.physio.fetch`. Sources and licenses: `docs/DATA.md`.
