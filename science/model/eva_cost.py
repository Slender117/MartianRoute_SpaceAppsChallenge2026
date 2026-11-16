"""O₂ cost of a walking EVA by slope and gravity.

The shape of the curve comes from Minetti et al. (2002), measured at 1 g without a suit. Here it is
only used to know how much more (or less) each meter costs relative to flat ground. The absolute O₂
level on flat ground is set by the project (`o2_flat_per_m` in docs/supuestos.md), so the
model needs neither the energy-to-O₂ conversion factor nor the astronaut's mass, and it absorbs the
effect of the suit in that level.

What still has no source is how the flat-ground cost changes with gravity. Instead of inventing a
factor, the slope penalty is bounded between two extreme cases and the output is an
interval (`o2_interval_kg`).
"""

import numpy as np

G_EARTH = 9.80665  # m/s²

# Cost of walking (J/kg/m) at different slopes (rise/run). Values from the Minetti
# et al. (2002) abstract: 1.64 flat (min, at 1.0 m/s), 0.81 at -10 %, 3.46 at -45 %, 17.33 at +45 %.
# Between knots it is interpolated and beyond ±0.45 it saturates.
# ponytail: four knots from the abstract; with the full text, replace them with its polynomial.
_GRADE = np.array([-0.45, -0.10, 0.0, 0.45])
_COST = np.array([3.46, 0.81, 1.64, 17.33])


def gradient_scale_bounds(g_ms2: float) -> tuple[float, float]:
    """Bounds of the slope-penalty scale `s`; there is no source for the central value.

    The work of lifting a mass is proportional to gravity, but the flat-ground cost may not
    be: if it does not change with gravity, `s` = g/g_Earth; if it is proportional, `s` = 1.
    """
    return g_ms2 / G_EARTH, 1.0


def o2_multiplier(grade: np.ndarray, s: float = 1.0) -> np.ndarray:
    """O₂ per meter relative to flat ground, for a signed slope (positive = uphill)."""
    flat = _COST[2]
    return 1.0 + s * (np.interp(grade, _GRADE, _COST) - flat) / flat


def round_trip_multiplier(grade: np.ndarray, s: float = 1.0) -> np.ndarray:
    """Per-direction mean of an EVA that returns along the same path.

    What is climbed going out is descended coming back.
    """
    g = np.abs(grade)
    return 0.5 * (o2_multiplier(g, s) + o2_multiplier(-g, s))


def slope_penalty(slope_deg: np.ndarray, max_slope_deg: float) -> np.ndarray:
    """Slope penalty normalized to 0–1 at the maximum slope.

    It replaces (slope/max)².

    It is the minimal fit into `engine/cost.py`: it keeps the team's structure and per-mode weights.
    It does not depend on gravity: `s` multiplies the numerator and the denominator and cancels, so
    gravity only changes the reported O₂ (`o2_interval_kg`), not the route.
    """

    def extra(deg):
        return round_trip_multiplier(np.tan(np.radians(deg))) - 1.0

    return np.clip(extra(slope_deg) / extra(max_slope_deg), 0.0, 1.0)


def cell_cost(
    slope_deg: np.ndarray,
    hazard: np.ndarray,
    thermal_inertia: np.ndarray,
    w_hazard: float,
    w_instability: float,
    s: float = 1.0,
    max_slope_deg: float | None = None,
) -> np.ndarray:
    """Cost per cell in physical units.

    It is 1 on flat ground with no hazard and, on slopes, the O₂ relative to flat ground.

    It ignores the per-mode slope weights, so the three modes would only differ by hazard.
    """
    cost = (
        round_trip_multiplier(np.tan(np.radians(slope_deg)), s)
        + w_hazard * hazard
        + w_instability * (1.0 - thermal_inertia)
    )
    if max_slope_deg is not None:
        cost = np.where(slope_deg > max_slope_deg, np.inf, cost)
    return cost


def route_o2_kg(
    path: np.ndarray,
    dem: np.ndarray,
    cell_m: tuple[float, float],
    o2_flat_kg_per_m: float,
    s: float = 1.0,
) -> float:
    """Round-trip O₂ along the same path, using the real slope of each segment."""
    steps = np.diff(path, axis=0)
    horizontal = np.hypot(steps[:, 0] * cell_m[0], steps[:, 1] * cell_m[1])
    dz = np.diff(dem[path[:, 0], path[:, 1]].astype(float))
    grade = dz / horizontal
    dist = np.hypot(horizontal, dz)
    return float(
        o2_flat_kg_per_m * np.sum(dist * (o2_multiplier(grade, s) + o2_multiplier(-grade, s)))
    )


def o2_interval_kg(
    path: np.ndarray,
    dem: np.ndarray,
    cell_m: tuple[float, float],
    o2_flat_kg_per_m: float,
    g_ms2: float,
) -> tuple[float, float]:
    """O₂ interval of the whole EVA between the two gravity bounds.

    The effect of the suit is inside `o2_flat_kg_per_m`.
    """
    lo, hi = gradient_scale_bounds(g_ms2)
    return (
        route_o2_kg(path, dem, cell_m, o2_flat_kg_per_m, lo),
        route_o2_kg(path, dem, cell_m, o2_flat_kg_per_m, hi),
    )
