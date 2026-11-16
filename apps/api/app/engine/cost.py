"""Builds the cost grid for each walking mode."""

import numpy as np

from app.engine.o2_model import slope_penalty
from app.schemas.route import WalkMode
from app.storage import RegionGrids, memoized

# Weights per mode. All layers arrive normalized to 0–1.
# The baseline has every weight at 0: cost stays at 1 per meter and the search returns the
# minimum-distance route that respects the maximum slope. It is the reference for HE2 and HE3.
MODE_WEIGHTS: dict[WalkMode, dict[str, float]] = {
    WalkMode.safe: {"slope": 4.0, "hazard": 4.0, "instability": 2.0, "science": 0.0},
    WalkMode.fast: {"slope": 0.5, "hazard": 1.0, "instability": 0.3, "science": 0.0},
    WalkMode.science: {"slope": 1.5, "hazard": 2.0, "instability": 1.0, "science": 0.8},
    WalkMode.baseline: {"slope": 0.0, "hazard": 0.0, "instability": 0.0, "science": 0.0},
}

# Minimum cost per cell: keeps the science bonus from making a cell free.
MIN_CELL_COST = 0.1


def mode_free_terms(grids: RegionGrids, max_slope_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """Slope and instability penalties. They do not depend on the mode: the four routes of a
    comparison share them, and they are cached per region and maximum slope (read-only)."""

    def compute() -> tuple[np.ndarray, np.ndarray]:
        # Extra O₂ from slope (Minetti), 0 on flat ground, 1 at the maximum: see engine/o2_model.py
        penalty = slope_penalty(grids.slope, max_slope_deg)
        instability = 1.0 - grids.thermal_inertia
        penalty.setflags(write=False)
        instability.setflags(write=False)
        return penalty, instability

    return memoized(grids, ("cost_terms", float(max_slope_deg)), compute)


def build_cost(grids: RegionGrids, mode: WalkMode, max_slope_deg: float) -> np.ndarray:
    """Cost of crossing each cell; infinite where the slope exceeds the suit maximum."""
    w = MODE_WEIGHTS[mode]
    penalty, instability = mode_free_terms(grids, max_slope_deg)

    cost = (
        1.0  # distancia
        + w["slope"] * penalty
        + w["hazard"] * grids.hazard
        + w["instability"] * instability
    )
    cost *= 1.0 - w["science"] * grids.minerals
    cost = np.maximum(cost, MIN_CELL_COST).astype(np.float64)

    cost[grids.slope > max_slope_deg] = np.inf
    return cost


def cost_breakdown(grids: RegionGrids, path: np.ndarray) -> dict[str, float]:
    """Mean of each factor along the route, for the UI."""
    rows, cols = path[:, 0], path[:, 1]
    return {
        "slope": float(grids.slope[rows, cols].mean()),
        "hazard": float(grids.hazard[rows, cols].mean()),
        "instability": float((1.0 - grids.thermal_inertia[rows, cols]).mean()),
        "science_bonus": float(grids.minerals[rows, cols].mean()),
    }
