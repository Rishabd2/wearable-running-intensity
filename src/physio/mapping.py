"""Tempo-to-zone mapping. This is a mapping between datasets, not a measured effect.

No open dataset found for this project records music tempo together with
heart rate or cadence during runs, so nothing here measures what music does
to a runner. The table chains three measured relationships from three
different groups of people:

1. HR zone -> treadmill speed: the belt speed at which HR first reached each
   zone bound in the Malaga graded tests (population median).
2. Speed -> cadence: the mixed-model line fitted to the Fukuchi treadmill
   force data (runners at 9.0, 12.6 and 16.2 km/h).
3. Cadence -> track tempo: a track "fits" a cadence band when its Spotify
   tempo, or twice its tempo (one beat per two steps), falls in the band.
   One beat per step is the assumption; it is the usual premise of
   tempo-matched running playlists, not something tested here.

Speeds outside the cadence data range are flagged as extrapolated.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .zones import ZONE_LABELS, ZONE_NAMES


def tempo_zone_table(zone_speeds: pd.DataFrame, cadence: dict, tracks: pd.DataFrame) -> pd.DataFrame:
    medians = zone_speeds.set_index("zone")["speed_median"]
    lo_range, hi_range = cadence["speed_range_kmh"]
    runner_sd = float(np.sqrt(cadence["model"].cov_re.iloc[0, 0]))
    tempo = tracks["tempo"].to_numpy(dtype=float)
    energy = tracks["energy"].to_numpy(dtype=float)
    rows = []
    zones = ZONE_NAMES[1:]
    for i, zone in enumerate(zones):
        upper_key = zones[i + 1] if i + 1 < len(zones) else "peak"
        s_lo, s_hi = float(medians[zone]), float(medians[upper_key])
        c_lo = cadence["intercept"] + cadence["slope_per_kmh"] * s_lo
        c_hi = cadence["intercept"] + cadence["slope_per_kmh"] * s_hi
        one_to_one = (tempo >= c_lo) & (tempo <= c_hi)
        half_time = (2 * tempo >= c_lo) & (2 * tempo <= c_hi)
        match = one_to_one | half_time
        rows.append({
            "zone": zone,
            "zone_bounds": ZONE_LABELS[zone],
            "speed_kmh_measured": f"{s_lo:.1f}-{s_hi:.1f}",
            "cadence_spm_mapped": f"{c_lo:.0f}-{c_hi:.0f}",
            "runner_to_runner_sd_spm": round(runner_sd, 1),
            "extrapolated": bool(s_lo < lo_range or s_hi > hi_range),
            "tempo_bpm_1to1": f"{c_lo:.0f}-{c_hi:.0f}",
            "tempo_bpm_half_time": f"{c_lo / 2:.0f}-{c_hi / 2:.0f}",
            "n_tracks_1to1": int(one_to_one.sum()),
            "n_tracks_half_time": int(half_time.sum()),
            "n_tracks_total": int(len(tempo)),
            "median_energy_matches": float(np.median(energy[match])) if match.any() else np.nan,
        })
    return pd.DataFrame(rows)


def tempo_band_for_cadence(cadence_spm: float, tolerance: float = 0.03) -> tuple[float, float]:
    """Tempo band (1:1) for a runner's own measured cadence, plus or minus ``tolerance``."""
    return cadence_spm * (1 - tolerance), cadence_spm * (1 + tolerance)
