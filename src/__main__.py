"""python -m src  →  clean, analyze, and write figures."""

from pathlib import Path

from .analyze import run_analysis, write_tables
from .plot import write_figures

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "processed" / "pop_tracks_raw.csv"
CLEAN = ROOT / "data" / "processed" / "pop_tracks.csv"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"


def main() -> None:
    bundle = write_figures(RAW, FIGURES)
    write_tables(bundle, TABLES)
    bundle["df"].to_csv(CLEAN, index=False)
    summary = bundle["summary"]
    print(f"n_raw={summary['n_raw']} n_unique={summary['n_unique']}")
    print(f"danceability~valence r={summary['danceability_valence_r']:.3f}")
    print(f"energy OLS R^2={summary['ols']['r_squared']:.3f}")
    print(f"figures → {FIGURES}")
    print(f"tables → {TABLES}")


if __name__ == "__main__":
    main()
