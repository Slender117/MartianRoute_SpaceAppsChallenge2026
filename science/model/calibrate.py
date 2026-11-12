"""Calibración offline de los pesos de terreno contra un recorrido real. No va a la API."""

import numpy as np
from scipy.spatial import cKDTree

WEIGHT_GRID = np.geomspace(0.1, 10, 7)


def route(
    cost: np.ndarray, start: tuple[int, int], goal: tuple[int, int], cell_m: tuple[float, float]
) -> np.ndarray:
    """Camino de costo mínimo, con el mismo MCP_Geometric que usa el motor del equipo."""
    from skimage.graph import MCP_Geometric

    mcp = MCP_Geometric(cost, fully_connected=True, sampling=cell_m)
    mcp.find_costs([start], [goal])
    return np.array(mcp.traceback(goal))


def separation_m(path: np.ndarray, ref: np.ndarray, cell_m: tuple[float, float]) -> float:
    """Separación media simétrica entre una ruta y un recorrido, en metros."""
    scale = np.array(cell_m)
    d_ref = cKDTree(path * scale).query(ref * scale)[0]
    d_path = cKDTree(ref * scale).query(path * scale)[0]
    return float((d_ref.mean() + d_path.mean()) / 2)


def fit_weights(
    cost_fn,
    segments: list[np.ndarray],
    cell_m: tuple[float, float],
    grid: np.ndarray = WEIGHT_GRID,
) -> tuple[tuple[float, float], np.ndarray]:
    """Pesos (riesgo, inestabilidad) que acercan la ruta de costo mínimo a cada tramo real.

    `cost_fn(w_hazard, w_instability)` devuelve la grilla de costo. Es una búsqueda en rejilla: el
    resultado incluye la superficie de la pérdida, y un valle plano indica pesos que el recorrido
    no distingue.
    """
    loss = np.zeros((len(grid), len(grid)))
    for i, wh in enumerate(grid):
        for j, wi in enumerate(grid):
            cost = cost_fn(wh, wi)
            loss[i, j] = np.mean(
                [
                    separation_m(route(cost, tuple(seg[0]), tuple(seg[-1]), cell_m), seg, cell_m)
                    for seg in segments
                ]
            )
    i, j = np.unravel_index(loss.argmin(), loss.shape)
    return (float(grid[i]), float(grid[j])), loss
