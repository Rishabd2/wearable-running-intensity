"""Parse an Apple Health ``export.xml`` into de-identified per-run summaries.

Drop your own export (iPhone: Health, profile picture, Export All Health
Data, then unzip) at ``data/raw/apple_health/export.xml`` and run::

    python -m src.physio.apple_health data/raw/apple_health/export.xml --age 30

The output keeps only timing, heart rate, steps and speed. Source names,
device strings, and route (GPS) files are never read. Raw exports stay in
``data/raw/`` which is gitignored.

Per running workout it reports mean and peak HR, share of HR samples in each
zone, cadence (step count inside the workout divided by its duration, when
step records exist), and the 1:1 tempo band for that cadence.
"""

from __future__ import annotations

import argparse
import bisect
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .mapping import tempo_band_for_cadence
from .zones import ZONE_NAMES, age_predicted_hrmax, zone_of

HR = "HKQuantityTypeIdentifierHeartRate"
STEPS = "HKQuantityTypeIdentifierStepCount"
SPEED = "HKQuantityTypeIdentifierRunningSpeed"
RUNNING = "HKWorkoutActivityTypeRunning"
DATE_FMT = "%Y-%m-%d %H:%M:%S %z"


def _ts(text: str) -> float:
    return datetime.strptime(text, DATE_FMT).timestamp()


@dataclass
class Export:
    workouts: list = field(default_factory=list)   # (start, end)
    hr: list = field(default_factory=list)         # (t, bpm)
    steps: list = field(default_factory=list)      # (start, end, count)
    speed: list = field(default_factory=list)      # (t, value, unit)


def parse(path: str | Path) -> Export:
    """Stream the XML so multi-GB exports do not need to fit in memory."""
    out = Export()
    for _, elem in ET.iterparse(str(path), events=("end",)):
        tag = elem.tag
        if tag == "Record":
            kind = elem.get("type")
            if kind == HR:
                out.hr.append((_ts(elem.get("startDate")), float(elem.get("value"))))
            elif kind == STEPS:
                out.steps.append((_ts(elem.get("startDate")), _ts(elem.get("endDate")), float(elem.get("value"))))
            elif kind == SPEED:
                out.speed.append((_ts(elem.get("startDate")), float(elem.get("value")), elem.get("unit", "")))
            elem.clear()
        elif tag == "Workout":
            if elem.get("workoutActivityType") == RUNNING:
                out.workouts.append((_ts(elem.get("startDate")), _ts(elem.get("endDate"))))
            elem.clear()
    out.hr.sort()
    out.workouts.sort()
    return out


def _steps_in(steps: list, start: float, end: float) -> float:
    total = 0.0
    for s, e, count in steps:
        overlap = min(e, end) - max(s, start)
        if overlap <= 0:
            continue
        total += count if e <= s else count * overlap / (e - s)
    return total


def _speed_kmh(value: float, unit: str) -> float:
    unit = unit.lower()
    if unit in ("m/s",):
        return value * 3.6
    if unit in ("km/hr", "km/h"):
        return value
    if unit in ("mi/hr", "mph"):
        return value * 1.609344
    return float("nan")


def summarize(export: Export, hr_max: float) -> pd.DataFrame:
    hr_t = [t for t, _ in export.hr]
    rows = []
    for i, (start, end) in enumerate(export.workouts, 1):
        lo, hi = bisect.bisect_left(hr_t, start), bisect.bisect_right(hr_t, end)
        bpm = np.array([v for _, v in export.hr[lo:hi]])
        minutes = (end - start) / 60.0
        row = {"workout": i, "start_utc": pd.Timestamp(start, unit="s", tz="UTC"), "duration_min": minutes,
               "n_hr_samples": int(bpm.size)}
        if bpm.size:
            zones = zone_of(bpm / hr_max).value_counts(normalize=True)
            row.update({"hr_mean": float(bpm.mean()), "hr_peak": float(bpm.max())})
            row.update({f"share_{z}": float(zones.get(z, 0.0)) for z in ["Z0"] + ZONE_NAMES})
        n_steps = _steps_in(export.steps, start, end)
        row["cadence_spm"] = n_steps / minutes if n_steps > 0 and minutes > 0 else np.nan
        speeds = [_speed_kmh(v, u) for t, v, u in export.speed if start <= t <= end]
        row["speed_kmh_mean"] = float(np.nanmean(speeds)) if speeds else np.nan
        if np.isfinite(row["cadence_spm"]):
            lo_bpm, hi_bpm = tempo_band_for_cadence(row["cadence_spm"])
            row["tempo_bpm_1to1"] = f"{lo_bpm:.0f}-{hi_bpm:.0f}"
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize running workouts from an Apple Health export.xml")
    parser.add_argument("export_xml")
    parser.add_argument("--hr-max", type=float, help="measured HRmax in bpm")
    parser.add_argument("--age", type=float, help="used for the Tanaka HRmax estimate when --hr-max is absent")
    parser.add_argument("--out", default="results/tables/my_runs.csv")
    args = parser.parse_args()
    export = parse(args.export_xml)
    if args.hr_max:
        hr_max = args.hr_max
    elif args.age:
        hr_max = float(age_predicted_hrmax(args.age))
    else:
        hr_max = max(v for _, v in export.hr)
        print(f"no --hr-max or --age; using the highest recorded HR ({hr_max:.0f} bpm) as HRmax")
    table = summarize(export, hr_max)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)
    print(table.to_string(index=False))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
