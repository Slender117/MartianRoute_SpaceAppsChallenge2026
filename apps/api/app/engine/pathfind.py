"""Least-cost route search on the grid (scikit-image MCP)."""

import numpy as np
from skimage.graph import MCP_Geometric


class NoPathError(Exception):
    pass


def find_path(
    cost: np.ndarray,
    start: tuple[int, int],
    end: tuple[int, int],
    sampling: tuple[float, float] | None = None,
) -> np.ndarray:
    """Return the route as an (N, 2) array of (row, col). sampling: cell size."""
    if start == end:
        raise NoPathError("Start and destination fall in the same cell")
    for name, cell in (("inicio", start), ("destino", end)):
        if not np.isfinite(cost[cell]):
            raise NoPathError(f"The {name} point is not walkable (slope too steep)")

    mcp = MCP_Geometric(cost, fully_connected=True, sampling=sampling)
    cumulative, _ = mcp.find_costs([start], [end])
    if not np.isfinite(cumulative[end]):
        raise NoPathError("There is no walkable route between the points")

    return np.asarray(mcp.traceback(end), dtype=np.int64)
