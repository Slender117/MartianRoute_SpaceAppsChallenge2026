"""Búsqueda de la ruta de menor costo sobre la grilla (MCP de scikit-image)."""

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
    """Devuelve la ruta como arreglo (N, 2) de (fila, columna). sampling: tamaño de celda."""
    if start == end:
        raise NoPathError("El inicio y el destino caen en la misma celda")
    for name, cell in (("inicio", start), ("destino", end)):
        if not np.isfinite(cost[cell]):
            raise NoPathError(f"El punto de {name} no es caminable (pendiente excesiva)")

    mcp = MCP_Geometric(cost, fully_connected=True, sampling=sampling)
    cumulative, _ = mcp.find_costs([start], [end])
    if not np.isfinite(cumulative[end]):
        raise NoPathError("No existe una ruta caminable entre los puntos")

    return np.asarray(mcp.traceback(end), dtype=np.int64)
