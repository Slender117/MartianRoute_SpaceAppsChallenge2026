"""Offline calibration of the terrain weights against a real traverse. Not part of the API."""

import numpy as np
from scipy.spatial import cKDTree

WEIGHT_GRID = np.geomspace(0.1, 10, 7)


def route(
    cost: np.ndarray, start: tuple[int, int], goal: tuple[int, int], cell_m: tuple[float, float]
) -> np.ndarray:
    """Minimum-cost path, with the same MCP_Geometric the team's engine uses."""
    from skimage.graph import MCP_Geometric

    mcp = MCP_Geometric(cost, fully_connected=True, sampling=cell_m)
    mcp.find_costs([start], [goal])
    return np.array(mcp.traceback(goal))


def separation_m(path: np.ndarray, ref: np.ndarray, cell_m: tuple[float, float]) -> float:
    """Symmetric mean separation between a route and a traverse, in meters."""
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
    """Weights (hazard, instability) that bring the minimum-cost route closest to each real segment.

    `cost_fn(w_hazard, w_instability)` returns the cost grid. It is a grid search: the
    result includes the loss surface, and a flat valley flags weights that the traverse
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
