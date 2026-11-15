"""Construcción de la grilla de costo según el modo de caminata."""

import numpy as np

from app.engine.o2_model import slope_penalty
from app.schemas.route import WalkMode
from app.storage import RegionGrids, memoized

# Pesos por modo. Todas las capas llegan normalizadas a 0–1.
# La línea base tiene todos los pesos en 0: el costo queda en 1 por metro y el A* devuelve la ruta
# de mínima distancia que respeta la pendiente máxima. Sirve de referencia para HE2 y HE3.
MODE_WEIGHTS: dict[WalkMode, dict[str, float]] = {
    WalkMode.safe: {"slope": 4.0, "hazard": 4.0, "instability": 2.0, "science": 0.0},
    WalkMode.fast: {"slope": 0.5, "hazard": 1.0, "instability": 0.3, "science": 0.0},
    WalkMode.science: {"slope": 1.5, "hazard": 2.0, "instability": 1.0, "science": 0.8},
    WalkMode.baseline: {"slope": 0.0, "hazard": 0.0, "instability": 0.0, "science": 0.0},
}

# Costo mínimo por celda: evita que el bono científico vuelva gratis una celda.
MIN_CELL_COST = 0.1


def mode_free_terms(grids: RegionGrids, max_slope_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """Penalización por pendiente e inestabilidad. No dependen del modo: las cuatro rutas de una
    comparación las comparten, y se guardan por región y pendiente máxima (solo lectura)."""

    def compute() -> tuple[np.ndarray, np.ndarray]:
        # O₂ extra por pendiente (Minetti), 0 en plano y 1 en la máxima: ver engine/o2_model.py
        penalty = slope_penalty(grids.slope, max_slope_deg)
        instability = 1.0 - grids.thermal_inertia
        penalty.setflags(write=False)
        instability.setflags(write=False)
        return penalty, instability

    return memoized(grids, ("cost_terms", float(max_slope_deg)), compute)


def build_cost(grids: RegionGrids, mode: WalkMode, max_slope_deg: float) -> np.ndarray:
    """Costo de cruzar cada celda; infinito donde la pendiente supera la máxima del traje."""
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
    """Promedio de cada factor a lo largo de la ruta, para mostrar en la UI."""
    rows, cols = path[:, 0], path[:, 1]
    return {
        "slope": float(grids.slope[rows, cols].mean()),
        "hazard": float(grids.hazard[rows, cols].mean()),
        "instability": float((1.0 - grids.thermal_inertia[rows, cols]).mean()),
        "science_bonus": float(grids.minerals[rows, cols].mean()),
    }
