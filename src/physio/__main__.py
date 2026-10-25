"""python -m src.physio  ->  run the physiology analyses, write tables and figures.

Run ``python -m src.physio.fetch`` first.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ..spotify.clean import clean_tracks, load_raw
from . import cadence, figures, fuller, mapping, treadmill
from .fetch import RAW, verify

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
TRACKS = ROOT / "data" / "processed" / "pop_tracks_raw.csv"


def run() -> dict:
    bad = verify()
    if bad:
        raise SystemExit(f"{len(bad)} data files missing or failing checksum; run python -m src.physio.fetch")
    fu = fuller.run(RAW / "fuller_apple_watch" / "aw_fb_data.csv")
    tr = treadmill.run(RAW / "malaga_treadmill" / "test_measure.csv", RAW / "malaga_treadmill" / "subject-info.csv")
    cad = cadence.run(RAW / "fukuchi_running")
    tracks = clean_tracks(load_raw(TRACKS))
    table = mapping.tempo_zone_table(tr["zone_speeds"], cad, tracks)
    scores = pd.concat([fu["scores"], tr["zone_scores"]], ignore_index=True)
    return {"fuller": fu, "treadmill": tr, "cadence": cad, "tracks": tracks, "tempo_table": table, "scores": scores}


def write_tables(b: dict) -> dict:
    TABLES.mkdir(parents=True, exist_ok=True)
    b["scores"].to_csv(TABLES / "physio_prediction_scores.csv", index=False, float_format="%.4f")
    b["fuller"]["summary"].to_csv(TABLES / "physio_fuller_activity_summary.csv", index=False, float_format="%.4f")
    b["fuller"]["confusion"].to_csv(TABLES / "physio_fuller_confusion.csv", float_format="%.4f")
    b["treadmill"]["zone_speeds"].to_csv(TABLES / "physio_zone_entry_speeds.csv", index=False, float_format="%.3f")
    b["treadmill"]["hr_by_speed"].to_csv(TABLES / "physio_hr_by_speed.csv", index=False, float_format="%.4f")
    b["cadence"]["trials"].to_csv(TABLES / "physio_cadence_trials.csv", index=False, float_format="%.3f")
    b["cadence"]["by_speed"].to_csv(TABLES / "physio_cadence_by_speed.csv", index=False, float_format="%.3f")
    b["tempo_table"].to_csv(TABLES / "physio_tempo_zone_map.csv", index=False, float_format="%.3f")
    tests = b["treadmill"]["tests"]
    summary = {
        "fuller": {
            "rows_apple_watch": int(len(b["fuller"]["df"])),
            "inferred_participant_groups": int(b["fuller"]["df"]["participant"].nunique()),
        },
        "treadmill": {
            "adult_tests": int(len(tests)),
            "adult_participants": int(tests["ID"].nunique()),
            "hr_peak_median": float(tests["hr_peak"].median()),
            "hr_speed_slope_median_bpm_per_kmh": float(tests["hr_speed_slope"].median()),
            "hr_speed_slope_iqr": [float(tests["hr_speed_slope"].quantile(q)) for q in (0.25, 0.75)],
            "hrr60_median": float(tests["hrr60"].median()),
            "hrr60_n": int(tests["hrr60"].notna().sum()),
        },
        "cadence": {
            "trials": int(len(b["cadence"]["trials"])),
            "runners": int(b["cadence"]["trials"]["subject"].nunique()),
            "intercept": b["cadence"]["intercept"],
            "slope_spm_per_kmh": b["cadence"]["slope_per_kmh"],
            "slope_se": b["cadence"]["slope_se"],
            "speed_range_kmh": list(b["cadence"]["speed_range_kmh"]),
        },
        "spotify_tracks": int(len(b["tracks"])),
    }
    (TABLES / "physio_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    b = run()
    summary = write_tables(b)
    figures.write_all(TABLES, FIGURES, TRACKS)
    grouped = b["scores"][b["scores"]["split"] == "grouped by participant"]
    print(grouped[["task", "model", "accuracy", "macro_f1"]].to_string(index=False))
    print(b["tempo_table"].to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
