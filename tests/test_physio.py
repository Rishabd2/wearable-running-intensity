"""Unit tests for the physiology pipeline.

Inputs here are small SYNTHETIC arrays and a SYNTHETIC export.xml fixture.
They test the code paths, not any physiological claim. Checks against the
real downloaded datasets run only when ``data/raw`` has been fetched.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.physio import apple_health, cadence, mapping, treadmill
from src.physio.fetch import load_manifest, verify
from src.physio.zones import age_predicted_hrmax, karvonen_fraction, zone_of

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_export.xml"


def test_zone_boundaries():
    assert zone_of([0.45, 0.5, 0.65, 0.7, 0.85, 0.9, 1.02]).tolist() == ["Z0", "Z1", "Z2", "Z3", "Z4", "Z5", "Z5"]
    assert age_predicted_hrmax(40) == pytest.approx(180.0)
    assert karvonen_fraction(130, 60, 200) == pytest.approx(0.5)


def test_cadence_from_synthetic_force_trace():
    # SYNTHETIC: 30 s at 300 Hz, one half-sine contact every 0.35 s -> 171.4 steps/min
    fs, period = 300, 0.35
    t = np.arange(0, 30, 1 / fs)
    phase = (t % period) / period
    fy = np.where(phase < 0.4, 1500 * np.sin(np.pi * phase / 0.4), 0.0)
    fy[::97] += 40  # flight-phase noise below the onset threshold
    assert cadence.cadence_spm(fy, fs) == pytest.approx(60 / period, rel=0.01)


def test_treadmill_per_test_on_synthetic_ramp():
    # SYNTHETIC graded test: 5 km/h warm-up, ramp to 15 km/h, recovery at 5 km/h
    time = np.arange(0, 900, 3.0)
    speed = np.where(time < 120, 5.0, np.minimum(5 + (time - 120) / 60, 15.0))
    speed[time > 720] = 5.0
    hr = 80 + 7 * (speed - 5)
    hr[time > 720] = np.maximum(150 - 0.5 * (time[time > 720] - 720), 90)
    test = pd.DataFrame({"time": time, "Speed": speed, "HR": hr, "ID_test": "s_1", "ID": 1})
    test["hr_s"] = test["HR"]
    out = treadmill.per_test(test)
    assert out["hr_peak"] == pytest.approx(150)
    assert out["hr_speed_slope"] == pytest.approx(7.0, rel=1e-6)
    assert out["speed_at_Z5"] == pytest.approx(5 + (0.9 * 150 - 80) / 7, abs=0.2)
    assert out["hrr60"] == pytest.approx(30, abs=2)


def test_tempo_zone_table_counts_one_to_one_and_half_time():
    zone_speeds = pd.DataFrame({
        "zone": ["Z2", "Z3", "Z4", "Z5", "peak"],
        "speed_median": [8.0, 10.0, 12.0, 14.0, 16.0],
    })

    class FakeModel:
        cov_re = pd.DataFrame([[25.0]])

    cad = {"intercept": 130.0, "slope_per_kmh": 3.0, "speed_range_kmh": (9.0, 16.2), "model": FakeModel()}
    tracks = pd.DataFrame({"tempo": [160.0, 80.0, 175.0, 999.0], "energy": [0.5, 0.6, 0.9, 0.1]})
    table = mapping.tempo_zone_table(zone_speeds, cad, tracks).set_index("zone")
    assert table.loc["Z3", "cadence_spm_mapped"] == "160-166"
    assert table.loc["Z3", "n_tracks_1to1"] == 1
    assert table.loc["Z3", "n_tracks_half_time"] == 1
    assert bool(table.loc["Z2", "extrapolated"]) is True
    assert table.loc["Z2", "runner_to_runner_sd_spm"] == 5.0


def test_apple_health_parser_on_synthetic_fixture():
    assert "SYNTHETIC" in FIXTURE.read_text()
    export = apple_health.parse(FIXTURE)
    assert len(export.workouts) == 1  # the walking workout is ignored
    table = apple_health.summarize(export, hr_max=200.0)
    row = table.iloc[0]
    assert row["duration_min"] == pytest.approx(10.0)
    assert row["n_hr_samples"] == 10  # the 06:30 sample is outside the run
    assert row["cadence_spm"] == pytest.approx(170.0)
    assert row["speed_kmh_mean"] == pytest.approx(11.0)
    assert row["share_Z2"] == pytest.approx(0.2)
    assert row["share_Z4"] == pytest.approx(0.4)
    assert row["tempo_bpm_1to1"] == "165-175"


def test_manifest_has_a_checksum_for_every_file():
    files = load_manifest()["files"]
    assert {f["dataset"] for f in files} == {"fuller_apple_watch", "fukuchi_running", "malaga_treadmill"}
    assert all(len(f["checksum"]) in (32, 64) for f in files)


needs_data = pytest.mark.skipif(bool(verify()), reason="real datasets not fetched (python -m src.physio.fetch)")


@needs_data
def test_real_cadence_rises_with_speed():
    from src.physio.fetch import RAW

    result = cadence.run(RAW / "fukuchi_running")
    assert len(result["trials"]) == 101
    assert result["slope_per_kmh"] > 0
