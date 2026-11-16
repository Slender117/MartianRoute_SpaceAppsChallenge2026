"""Estimated walking time, consumables and dose along the route.

The source of each constant is in docs/supuestos.md and in GET /assumptions.
"""

import numpy as np

SOL_HOURS = 24.6598
# Base speed of a suited astronaut on flat ground (km/h): lunar pace on regolith
# that is almost flat, from Coan (2020), applied to Mars.
BASE_SPEED_KMH = 2.0
# Metabolic O₂ use during an active EVA (kg/h per person): the mean of the Apollo lunar EVAs
# (234 kcal/h, Waligora and Horrigan, 1975) gives 0.066 to 0.071 kg/h with Weir (1949).
O2_KG_PER_HOUR = 0.07
# The EVA is done in pairs.
CREW_SIZE = 2
# Fraction of the suit autonomy that is not planned to be used.
AUTONOMY_RESERVE = 0.20
# Minimum reserve when returning to base (30 min, team plan decision). The stricter of this
# and AUTONOMY_RESERVE applies: see usable_autonomy_h.
WALKBACK_RESERVE_H = 0.5
# Surface dose equivalent measured by Curiosity RAD, in mSv per Earth day.
RAD_MSV_PER_DAY = 0.64
RAD_MSV_PER_DAY_ERROR = 0.12
# Absorbed dose of the largest solar event measured by RAD up to 2024 (mGy). It is not added to
# the background dose equivalent: converting it to mSv needs that event's quality factor.
SOLAR_EVENT_MGY = 8.1
# Career effective dose limit from NASA-STD-3001 Vol. 1 Rev. C [V1 4030] (mSv). There is no
# per-EVA limit: this value is only reported, it does not trigger alerts.
CAREER_DOSE_LIMIT_MSV = 600.0


def walking_speed_kmh(grade: np.ndarray) -> np.ndarray:
    """Tobler's function scaled so that flat ground gives the base speed."""
    return BASE_SPEED_KMH * np.exp(-3.5 * (np.abs(grade + 0.05) - 0.05))


def segment_profile(
    path: np.ndarray, dem: np.ndarray, cell_m: tuple[float, float]
) -> tuple[np.ndarray, np.ndarray]:
    """Distance (m) and time (h) of each route segment, in the direction it is walked."""
    steps = np.diff(path, axis=0)
    horizontal = np.hypot(steps[:, 0] * cell_m[0], steps[:, 1] * cell_m[1])
    elev = dem[path[:, 0], path[:, 1]].astype(float)
    dz = np.diff(elev)
    grade = np.divide(dz, horizontal, out=np.zeros_like(dz), where=horizontal > 0)
    dist = np.hypot(horizontal, dz)
    hours = (dist / 1000.0) / walking_speed_kmh(grade)
    return dist, hours


def ascent_m(path: np.ndarray, dem: np.ndarray) -> float:
    """Cumulative elevation gain along the route."""
    dz = np.diff(dem[path[:, 0], path[:, 1]].astype(float))
    return float(dz[dz > 0].sum())


def usable_autonomy_h(autonomy_h: float) -> float:
    """Plannable autonomy: the autonomy minus the stricter reserve (20 % or 30 min).

    With 8 h the 20 % rules (1.6 h); with less than 2.5 h of suit time the 30 min reserve rules.
    One rule feeds feasibility, the point of no return and the safe-return map.
    """
    return autonomy_h - max(AUTONOMY_RESERVE * autonomy_h, WALKBACK_RESERVE_H)


def point_of_no_return(elapsed_h: np.ndarray, back_h: np.ndarray, budget_h: float) -> int | None:
    """First index where what was spent plus the walk back no longer fits the budget.

    `budget_h` is the plannable autonomy minus the fixed task. On flat ground it falls at half
    the budget; on slopes the real return time is used, because
    climbing back up what was walked down takes longer.
    """
    idx = np.nonzero(elapsed_h + back_h >= budget_h)[0]
    return int(idx[0]) if idx.size else None


def radiation_dose_msv(duration_h: float) -> float:
    return duration_h / 24.0 * RAD_MSV_PER_DAY
