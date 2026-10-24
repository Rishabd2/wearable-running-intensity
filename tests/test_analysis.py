from pathlib import Path

from src.analyze import run_analysis
from src.clean import clean_tracks, load_raw
from src.mood_playlist import create_playlist, map_characteristics_to_mood

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "processed" / "pop_tracks_raw.csv"


def test_clean_unique_count():
    raw = load_raw(RAW)
    cleaned = clean_tracks(raw)
    assert len(raw) == 1064
    assert len(cleaned) == 821
    assert set(cleaned["Major_or_Minor"]) <= {"Major", "Minor"}


def test_original_correlation_and_ols():
    summary = run_analysis(RAW)["summary"]
    assert abs(summary["danceability_valence_r"] - 0.420) < 0.005
    assert abs(summary["ols"]["r_squared"] - 0.722) < 0.005
    assert summary["energy_by_mode_notebook"]["n_major"] == 469
    assert summary["energy_by_mode_notebook"]["n_minor"] == 352
    assert abs(summary["energy_by_mode_notebook"]["p_value"] - 0.995) < 0.01


def test_mood_mapping():
    assert map_characteristics_to_mood("excited") == "Happy"
    assert map_characteristics_to_mood("xyz") == "Unknown"
    playlist = create_playlist(clean_tracks(load_raw(RAW)), "sad", n=5)
    assert len(playlist) <= 5
    assert playlist["mood"].eq("Sad").all()
