# Data and privacy

## What is in git

- `data/processed/pop_tracks_raw.csv`: Spotify audio features for public tracks (ids, titles,
  artist names, feature vector). Not listening history, not health data.
- `data/manifest.json`: download URLs and published checksums for the open physiology datasets.
- `results/tables/physio_*`: aggregate or per-test summaries derived from the open datasets. The
  per-test table carries only the dataset's own anonymous test ids.
- `tests/fixtures/synthetic_export.xml`: a synthetic Apple Health export used by the tests.

## What is not in git

- Raw physiology files. `python -m src.physio.fetch` downloads them to `data/raw/` (gitignored).
  The Malaga treadmill data is under a PhysioNet health-data license that forbids attempts to
  re-identify participants; nothing here tries to.
- Personal health records. A real `export.xml` belongs in `data/raw/apple_health/` and stays out
  of git. The parser never reads source names, device strings, or GPS routes, and its output
  (`results/tables/my_runs.csv`) should be reviewed before it is shared.
- Spotify client secrets. Use `.env` (see `.env.example`); it is gitignored.

## Claims

Nothing in this repo is a controlled study of how music affects heart rate, cadence, or mood.
The tempo-to-zone table is a cross-dataset mapping, and the mood playlist helper is a ranking rule.
