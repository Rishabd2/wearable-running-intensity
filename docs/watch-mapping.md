# Intended Watch mapping (no run data in this repo)

The user described a second thread: map Spotify song features onto Apple Watch running physiology (tempo and related features to heart rate or cadence) in order to pick or edit a tune and look at psychological effect.

A search of Downloads found no Watch export and no script that joins HR or cadence to a track. This page records the join that the existing files imply, so it can be filled later without inventing results.

## Spotify side (present)

| Field | Source | Notes |
| --- | --- | --- |
| `track_id` | Web API | Join key for audio features |
| `tempo` | audio features | BPM |
| `energy` | audio features | 0–1 |
| `danceability` | audio features | includes tempo, beat strength |
| `valence` | audio features | musical positiveness |
| `loudness` | audio features | dB |

## Watch side (absent)

Typical Apple Health / HealthKit workout export fields that would be needed:

| Field | HealthKit type | Use |
| --- | --- | --- |
| workout start / end | `HKWorkout` | align to the song window |
| activity type | running | filter to outdoor/indoor run |
| heart rate series | `HKQuantityTypeIdentifierHeartRate` | compare to song tempo |
| step cadence or running speed | `HKQuantityTypeIdentifierStepCount` / running speed | compare to BPM |
| duration, distance | workout stats | context only |

## Planned join (not executed)

1. Export workouts from the Health app (see recipe below).
2. Keep only running workouts.
3. If song timestamps exist (Spotify recently played or a manual playlist log), overlap each track with the HR series in that window.
4. Per overlap, store mean/median HR, mean cadence if present, and the song `tempo` / `energy` / `valence`.
5. Plot tempo vs HR or cadence. Do not claim an effect until that table exists.

## Export recipe

1. iPhone: Health → profile → Export All Health Data.
2. Unzip `export.zip`. The payload is `apple_health_export/export.xml`.
3. Parse `Workout` nodes with `workoutActivityType` containing `Running`.
4. Parse `Record` nodes of type `HKQuantityTypeIdentifierHeartRate` whose dates fall inside those workouts.
5. Write a de-identified CSV with columns `workout_id`, `elapsed_s`, `heart_rate_bpm`, `cadence_spm` (if available). Drop name, source device UDID, and GPS.

No sample of that CSV is committed because no real export was available.
