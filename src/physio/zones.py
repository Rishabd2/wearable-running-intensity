"""Heart-rate zone definitions shared by every dataset in the pipeline.

Five zones as fractions of maximal heart rate (HRmax). The bounds follow
the common 50/60/70/80/90 percent convention used by consumer wearables.
They are a labeling convention, not a physiological threshold test.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ZONE_BOUNDS = [0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
ZONE_NAMES = ["Z1", "Z2", "Z3", "Z4", "Z5"]
ZONE_LABELS = {
    "Z1": "50-60% HRmax",
    "Z2": "60-70% HRmax",
    "Z3": "70-80% HRmax",
    "Z4": "80-90% HRmax",
    "Z5": "90-100% HRmax",
}


def zone_of(frac_hrmax) -> pd.Series:
    """Map a fraction of HRmax to Z0..Z5. Below 50 percent is Z0 (rest)."""
    frac = pd.Series(np.asarray(frac_hrmax, dtype=float))
    bins = [-np.inf] + ZONE_BOUNDS[:-1] + [np.inf]
    return pd.cut(frac, bins=bins, labels=["Z0"] + ZONE_NAMES, right=False).astype(str)


def age_predicted_hrmax(age) -> np.ndarray:
    """Tanaka et al. (2001) estimate, 208 - 0.7 * age. Used only when no measured max exists."""
    return 208.0 - 0.7 * np.asarray(age, dtype=float)


def karvonen_fraction(hr, resting_hr, hr_max) -> np.ndarray:
    """Fraction of heart-rate reserve, (HR - rest) / (HRmax - rest)."""
    hr = np.asarray(hr, dtype=float)
    return (hr - resting_hr) / (np.asarray(hr_max, dtype=float) - resting_hr)
