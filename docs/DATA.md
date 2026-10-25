# Data sources, licenses, and citations

Raw physiology files are not committed. `python -m src.physio.fetch` downloads them into
`data/raw/<dataset>/` (gitignored) and checks each file against the checksum the hosting repository
publishes, recorded in `data/manifest.json` (Harvard Dataverse MD5, figshare MD5, PhysioNet
`SHA256SUMS.txt`). Only derived, aggregate tables are committed under `results/tables/`.

## 1. Apple Watch and Fitbit activity data (Fuller et al.)

- What: minute-level Apple Watch Series 2 and Fitbit Charge HR2 records (heart rate, steps, distance,
  calories, and derived features) from a lab protocol of lying, sitting, self-paced walking and
  treadmill running at 3, 5 and 7 METs. Only the Apple Watch rows (3,656) are used.
- File: `aw_fb_data.csv` (1.4 MB).
- Source: Harvard Dataverse, https://doi.org/10.7910/DVN/ZS2Z2J
- License: CC0 1.0 (public domain dedication), as listed on the Dataverse record.
- Cite: Fuller D, Anaraki JR, Simango B, Rayner M, Dorani F, Bozorgi A, Luan H, A Basset F.
  Predicting lying, sitting, walking and running using Apple Watch and Fitbit data.
  *BMJ Open Sport & Exercise Medicine* 7 (2021). https://doi.org/10.1136/bmjsem-2020-001004
- Note: the file has no participant id column. See `docs/methodology.md` for how rows are grouped.

## 2. Treadmill maximal exercise tests (University of Malaga, PhysioNet)

- What: 992 graded maximal treadmill tests, one row per breath: time, speed (km/h), heart rate,
  VO2, VCO2, respiration rate, ventilation, plus age, sex, height, weight per test.
- Files: `test_measure.csv` (22 MB), `subject-info.csv`.
- Source: PhysioNet, https://doi.org/10.13026/7ezk-j442 (version 1.0.1), open access.
- License: the project page lists the PhysioNet Contributor Review Health Data License 1.5.0; the
  `LICENSE.txt` shipped with the files is CC BY-NC-SA 4.0. Both allow research use with attribution.
  This repo does not redistribute the files and commits only aggregate per-test summaries
  (`results/tables/physio_treadmill_per_test.csv`, no identifiers beyond the dataset's own test ids).
- Cite: Mongin D, García Romero J, Alvero Cruz JR. Treadmill Maximal Exercise Tests from the
  Exercise Physiology and Human Performance Lab of the University of Malaga (version 1.0.1).
  PhysioNet (2021). https://doi.org/10.13026/7ezk-j442
- Also cite: Mongin D, Chabert C, Courvoisier DS, García-Romero J, Alvero-Cruz JR. Heart rate
  recovery to assess fitness: comparison of different calculation methods in a large
  cross-sectional study. *Research in Sports Medicine* 31 (2023) 157-170.
  https://doi.org/10.1080/15438627.2021.1954513 ; and PhysioNet (Goldberger et al., *Circulation*
  101(23), 2000).

## 3. Running biomechanics at three speeds (Fukuchi et al., figshare)

- What: runners on an instrumented treadmill at 2.5, 3.5 and 4.5 m/s; 30 s of ground reaction
  force at 300 Hz per trial. The current record holds 39 runners at 3.5 m/s and 31 at the other two
  speeds (the 2017 paper describes 28 runners). Only the 101 `RBDS*runT*forces.txt` files and `RBDSinfo.txt`
  are downloaded (about 42 MB of the 770 MB record).
- Source: figshare, https://doi.org/10.6084/m9.figshare.4543435 (version 5).
- License: CC BY 4.0.
- Cite: Fukuchi RK, Fukuchi CA, Duarte M. A public dataset of running biomechanics and the effects
  of running speed on lower extremity kinematics and kinetics. *PeerJ* 5:e3298 (2017).
  https://doi.org/10.7717/peerj.3298

## 4. Spotify audio features (committed)

- What: 1,064 rows (821 unique tracks) of pop tracks released 2011-2022 with Spotify Web API audio
  features (tempo, energy, valence, and others), collected by the authors of the original trends
  study. Public track metadata, no listening history.
- File: `data/processed/pop_tracks_raw.csv` (220 KB).
- Terms: Spotify Developer Terms. The audio-features endpoint has since been restricted for new
  apps, so a fresh pull may not be possible; analyses run from the saved CSV.

## 5. Your own Apple Health export (optional, never committed)

`src/physio/apple_health.py` reads `export.xml` from the Health app export. Put it in
`data/raw/apple_health/`. The only committed export-format file is
`tests/fixtures/synthetic_export.xml`, which is synthetic and labeled as such.

## Considered and not used

- **Endomondo / FitRec workouts** (Ni, Muhlstein, McAuley, WWW 2019): HR and speed series for
  real outdoor runs, but scraped from a public fitness site with no stated license, and several GB.
  Left out because redistribution terms are unclear.
- **Running Injury Clinic kinematic dataset** (Ferber et al., *Scientific Data* 2024, CC BY 4.0):
  stride rate is only available inside a 22.7 GB archive; the small metadata CSV has speed but
  no cadence.
- **Wearable exam-stress sets** (PhysioNet): no running.
- **Music tempo linked to HR or cadence during running:** no open dataset with that link was found
  (general web search plus PhysioNet, figshare, and the MIR tempo datasets indexed by mirdata). The
  tempo-to-zone table is therefore a cross-dataset mapping, described in `docs/methodology.md`.
