# Methodology: running physiology and the tempo mapping

This page covers the physiology half (`src/physio/`). The Spotify feature study is in
`docs/spotify-features.md`. Dataset licenses and citations are in `docs/DATA.md`.

## What is measured and what is mapped

| Quantity | Status | Source |
| --- | --- | --- |
| Apple Watch HR, steps, derived features per activity | measured | Fuller et al. |
| Activity / running-intensity classification scores | measured (cross-validated) | Fuller et al. |
| HR vs treadmill speed, HR-speed slope, HR recovery | measured | Malaga treadmill tests |
| Speed at which HR first enters each zone | measured | Malaga treadmill tests |
| HR-zone classification from speed without HR | measured (cross-validated) | Malaga treadmill tests |
| Cadence vs speed | measured | Fukuchi force-plate data |
| Spotify tempo and energy per track | measured by Spotify's audio analysis | saved API pull |
| Cadence band per HR zone | **mapped** (zone -> speed from one cohort, speed -> cadence from another) | Malaga + Fukuchi |
| Tempo band per HR zone, track counts | **mapped** (assumes one beat per step) | all of the above |

No dataset here records a runner's HR or cadence while listening to a known track, so nothing
here estimates an effect of music on HR, cadence, or performance.

## HR zones (`src/physio/zones.py`)

Five zones as fractions of HRmax: Z1 50-60, Z2 60-70, Z3 70-80, Z4 80-90, Z5 90-100 percent;
below 50 percent is Z0. This is the common wearable convention, not a lactate or ventilatory
threshold test. In the treadmill data HRmax is the measured test peak (maximal tests). For an
Apple Health export the user passes a measured HRmax, or age for the Tanaka estimate
(208 - 0.7 x age; Tanaka, Monahan and Seals, *J Am Coll Cardiol* 37:153-156, 2001).

## 1. Apple Watch activity and intensity (`src/physio/fuller.py`)

- Rows: the 3,656 Apple Watch records. Targets: the six protocol activities, and separately the
  three running levels (3, 5, 7 METs; the MET level is the protocol target).
- Participant grouping: the CSV has no participant id. Rows are grouped by the
  (age, gender, height, weight) tuple, which gives 49 groups. The study reports 46 participants, so
  some people are split across more than one group; the file does not say why. Splitting a person in two can only leak information between folds, so the
  grouped scores are, if anything, slightly optimistic.
- Features: HR-only model uses `hear_rate`, `norm_heart` (HR minus resting HR) and
  `intensity_karvonen` (fraction of HR reserve). The full model adds steps, distance, calories,
  the dataset's entropy and HR-steps correlation features, and age, sex, height, weight.
- Models: majority class, standardized logistic regression, and a 200-tree random forest. Logistic
  regression and random forest are each fitted on the HR-only and on the full feature set, so the
  effect of the model family and of the features can be read separately.
- Validation: 5-fold `GroupKFold` by participant group is the headline. Scores are the mean and
  sample SD of accuracy and macro F1 over the 5 test folds (`src/physio/cv.py`). A stratified 5-fold split
  over rows is also reported to show how much a row split overstates accuracy: rows from the same
  person and activity share near-constant features (resting HR, entropy, demographics), so a row
  split lets the model recognize the person.
- The dataset's `steps` column does not behave like a cadence (sitting has a higher median than
  running at 3 METs), so cadence is not taken from this file.

## 2. HR response to speed (`src/physio/treadmill.py`)

- Tests from participants aged 18 or older. HR is smoothed with a centered 5-breath rolling median
  to remove single-breath artifacts.
- Effort phase: from the start of the test to the last breath at peak speed. After that the belt
  returns to 5 km/h for recovery.
- Per test: peak HR; OLS slope of HR on speed over effort breaths at 7 km/h or faster (bpm per
  km/h); the belt speed when HR first reached 60, 70, 80 and 90 percent of peak HR; and HRR60, HR
  at the end of effort minus HR 60 s later (only when a breath exists within 75 s of that mark).
  These per-test values stay in memory; only their population medians and quantiles are written.
- Zone prediction without HR: each effort breath is labeled with its measured zone. Models predict
  that label from speed alone (logistic) or from speed, elapsed time, age, sex, weight and height
  (histogram gradient boosting). Every 5th breath is used. 5-fold `GroupKFold` by participant id,
  so repeat tests by the same person stay in one fold.
- HR lags speed changes, and protocols differ (steps of 0.5 to 1 km/h, or ramps). The
  zone-entry speeds are therefore the speed on the belt when HR crossed the bound during an
  incremental test, not a steady-state speed for that zone.

## 3. Cadence vs speed (`src/physio/cadence.py`)

- Input: 101 trials of vertical ground reaction force (300 Hz, 30 s) from 39 runners at 2.5, 3.5
  and 4.5 m/s (9.0, 12.6, 16.2 km/h); 31 runners have all three speeds.
- Contact detection: a contact starts when Fy rises above 100 N after having fallen below 30 N,
  with a 0.15 s refractory gap. Cadence = 60 / median onset-to-onset interval.
- Model: `cadence ~ speed_kmh` linear mixed model with a random intercept per runner
  (statsmodels `MixedLM`). The random-intercept SD is reported as runner-to-runner spread.

## 4. Tempo-to-zone mapping (`src/physio/mapping.py`)

1. For each zone Z2 to Z5, take the population median speed at which HR entered that zone and the
   median speed at which it entered the next zone (Z5 runs to the median peak speed). That is the
   zone's speed band.
2. Convert both ends of the band to cadence with the fixed-effect line from step 3. Bands whose
   speeds fall outside 9.0-16.2 km/h are flagged as extrapolated.
3. A Spotify track fits the band when its tempo is inside it (one beat per step) or twice its tempo
   is inside it (one beat per two steps, half-time feel).
4. Report the tempo bands, the number of the 821 tracks that fit, and the median Spotify energy of
   those tracks.

The mapping is a population-level lookup. Individual cadence at a given speed varies by about the
runner-to-runner SD in the table, and individual zone speeds vary with fitness (see the
interquartile ranges in `results/tables/physio_zone_entry_speeds.csv`). For a single runner the
better input is their own cadence, which `src/physio/apple_health.py` reads from a Health export
and turns into a 1:1 tempo band (plus or minus 3 percent).

## 5. Apple Health export parser (`src/physio/apple_health.py`)

Streams `export.xml` with `iterparse`. Keeps `Workout` elements with
`workoutActivityType="HKWorkoutActivityTypeRunning"`, and `Record` elements of type
`HKQuantityTypeIdentifierHeartRate`, `HKQuantityTypeIdentifierStepCount` and
`HKQuantityTypeIdentifierRunningSpeed`. Per run: duration, HR samples inside the run, mean and peak
HR, share of HR samples in each zone, cadence as steps inside the run (pro-rated for partial
overlap) divided by duration, mean running speed, and the tempo band. Source names, devices, and
GPS routes are not read or written. The test fixture `tests/fixtures/synthetic_export.xml` is
synthetic.

## Reproduce

```bash
python -m src.physio.fetch   # downloads about 66 MB, verifies checksums
python -m src.physio         # tables in results/tables/physio_*, figures in results/figures/physio_*
```
