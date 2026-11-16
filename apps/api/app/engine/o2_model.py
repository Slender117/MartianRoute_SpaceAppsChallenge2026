"""O₂ cost of walking by slope, from the curve of Minetti et al. (2002).

It is the physical part of Edgar's model (`science/model/eva_cost.py`), copied into the engine
because the API image only ships `apps/api/`. The weight calibration (`science/model/calibrate.py`)
is not here: it is an offline script.

Two uses in the engine:

1. `slope_penalty`: the shape of the slope penalty in `engine/cost.py` (0 on flat ground,
   1 at the maximum slope). It decides the route.
2. `o2_interval_kg`: the O₂ of the whole EVA as an interval (low and high bound). It is only
   reported; it does not change the route.

Why an interval: there is no source for how the flat-ground cost changes at 0.38 g. Instead of
inventing a factor, the slope penalty is scaled between two extreme cases
(`gradient_scale_bounds`).
"""

import numpy as np

from app.engine.consumables import BASE_SPEED_KMH, O2_KG_PER_HOUR
from app.geo import MARS_RADIUS_M

G_EARTH_MS2 = 9.80665
# Mars GM (m³/s²) from the JGMRO_120f gravity field: Konopliv et al. (2020),
# https://doi.org/10.1029/2020GL090568
GM_MARS_M3_S2 = 42_828.3748574e9
# Surface gravity (m/s²) = GM / R², with the project's mean radius: about 3.73, 0.38 g.
# It does not subtract Mars' rotation, which lowers it by less than 0.5 %.
G_MARS_MS2 = GM_MARS_M3_S2 / MARS_RADIUS_M**2

# O₂ per meter on flat ground, per astronaut: hourly rate ÷ flat-ground speed (sources of both
# figures in docs/supuestos.md). It absorbs the effect of the suit.
O2_FLAT_KG_PER_M = O2_KG_PER_HOUR / (BASE_SPEED_KMH * 1000)

# Cost of walking (J/kg/m) by slope (rise ÷ run), from Minetti et al. (2002):
# 3.46 at -45 %, 0.81 at -10 %, 1.64 on flat ground and 17.33 at +45 %. Between knots it is
# interpolated linearly and saturates beyond ±45 %. Replace with the full paper's polynomial.
_GRADE_KNOTS = np.array([-0.45, -0.10, 0.0, 0.45])
_COST_KNOTS = np.array([3.46, 0.81, 1.64, 17.33])
_FLAT_COST = _COST_KNOTS[2]


def gradient_scale_bounds(g_ms2: float = G_MARS_MS2) -> tuple[float, float]:
    """Bounds of the slope-penalty scale `s` at a given gravity.

    Lifting a mass costs in proportion to gravity; the flat-ground cost is unknown. If it does not
    change with gravity, `s` = g/g_Earth (low bound); if it scales with it, `s` = 1 (high bound).
    """
    return g_ms2 / G_EARTH_MS2, 1.0


def o2_multiplier(grade: np.ndarray, s: float = 1.0) -> np.ndarray:
    """O₂ per meter relative to flat ground, for a signed slope (positive = uphill)."""
    return 1.0 + s * (np.interp(grade, _GRADE_KNOTS, _COST_KNOTS) - _FLAT_COST) / _FLAT_COST


def round_trip_multiplier(grade: np.ndarray, s: float = 1.0) -> np.ndarray:
    """Mean of going out and back along the same path: what is climbed out is descended back."""
    g = np.abs(grade)
    return 0.5 * (o2_multiplier(g, s) + o2_multiplier(-g, s))


def slope_penalty(slope_deg: np.ndarray, max_slope_deg: float) -> np.ndarray:
    """Normalized slope penalty: 0 on flat ground and 1 at the suit's maximum slope.

    It replaces (slope/max)². It is the extra round-trip O₂ relative to flat ground, divided by
    the one at the maximum slope. The scale `s` multiplies numerator and denominator and cancels,
    so gravity does not change the route: only the reported O₂.
    """

    def extra(deg: np.ndarray | float) -> np.ndarray:
        return round_trip_multiplier(np.tan(np.radians(deg))) - 1.0

    return np.clip(extra(slope_deg) / extra(max_slope_deg), 0.0, 1.0)


def route_o2_kg(
    path: np.ndarray,
    dem: np.ndarray,
    cell_m: tuple[float, float],
    s: float = 1.0,
    o2_flat_kg_per_m: float = O2_FLAT_KG_PER_M,
) -> float:
    """Round-trip O₂ along the same path, per astronaut, with the slope of each segment."""
    steps = np.diff(path, axis=0)
    horizontal = np.hypot(steps[:, 0] * cell_m[0], steps[:, 1] * cell_m[1])
    dz = np.diff(dem[path[:, 0], path[:, 1]].astype(float))
    grade = dz / horizontal  # a route never repeats a cell in a row: horizontal > 0
    dist = np.hypot(horizontal, dz)
    # Going out with `grade` and back with `-grade`, over the same distance.
    per_m = o2_multiplier(grade, s) + o2_multiplier(-grade, s)
    return float(o2_flat_kg_per_m * np.sum(dist * per_m))


def o2_interval_kg(
    path: np.ndarray,
    dem: np.ndarray,
    cell_m: tuple[float, float],
    g_ms2: float = G_MARS_MS2,
) -> tuple[float, float]:
    """O₂ of the whole EVA per astronaut, between the two gravity bounds (low, high)."""
    lo, hi = gradient_scale_bounds(g_ms2)
    return route_o2_kg(path, dem, cell_m, lo), route_o2_kg(path, dem, cell_m, hi)
