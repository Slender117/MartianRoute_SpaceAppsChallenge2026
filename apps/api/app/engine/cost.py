"""Construcción de la grilla de costo según el modo de caminata."""

import numpy as np

from app.schemas.route import WalkMode
from app.storage import RegionGrids

# Pesos por modo. Todas las capas llegan normalizadas a 0–1.
MODE_WEIGHTS: dict[WalkMode, dict[str, float]] = {
    WalkMode.safe: {"slope": 4.0, "hazard": 4.0, "instability": 2.0, "science": 0.0},
    WalkMode.fast: {"slope": 0.5, "hazard": 1.0, "instability": 0.3, "science": 0.0},
    WalkMode.science: {"slope": 1.5, "hazard": 2.0, "instability": 1.0, "science": 0.8},
}

# Costo mínimo por celda: evita que el bono científico vuelva gratis una celda.
MIN_CELL_COST = 0.1


def build_cost(grids: RegionGrids, mode: WalkMode, max_slope_deg: float) -> np.ndarray:
    w = MODE_WEIGHTS[mode]
    slope_n = np.clip(grids.slope / max_slope_deg, 0, 1)
    instability = 1.0 - grids.thermal_inertia

    cost = (
        1.0  # distancia
        + w["slope"] * slope_n**2
        + w["hazard"] * grids.hazard
        + w["instability"] * instability
    )
    cost *= 1.0 - w["science"] * grids.minerals
    cost = np.maximum(cost, MIN_CELL_COST).astype(np.float64)

    cost[grids.slope > max_slope_deg] = np.inf
    return cost


def cost_breakdown(grids: RegionGrids, path: np.ndarray) -> dict[str, float]:
    """Promedio de cada factor a lo largo de la ruta, para mostrar en la UI."""
    rows, cols = path[:, 0], path[:, 1]
    return {
        "slope": float(grids.slope[rows, cols].mean()),
        "hazard": float(grids.hazard[rows, cols].mean()),
        "instability": float((1.0 - grids.thermal_inertia[rows, cols]).mean()),
        "science_bonus": float(grids.minerals[rows, cols].mean()),
    }
