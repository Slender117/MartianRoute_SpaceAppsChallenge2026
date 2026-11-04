"""Paradas sugeridas a lo largo de la ruta."""

import numpy as np

from app.storage import RegionGrids

SCIENCE_THRESHOLD = 0.6
ICE_THRESHOLD = 0.6
# Separación mínima entre paradas, en puntos de la ruta.
MIN_GAP = 15


def find_stops(grids: RegionGrids, path: np.ndarray) -> list[tuple[int, str, str]]:
    """Devuelve (índice en la ruta, tipo, motivo) para cada parada."""
    rows, cols = path[:, 0], path[:, 1]
    candidates: list[tuple[float, int, str, str]] = []

    minerals = grids.minerals[rows, cols]
    for i in np.nonzero(minerals >= SCIENCE_THRESHOLD)[0]:
        candidates.append(
            (
                float(minerals[i]),
                int(i),
                "science",
                f"Minerales de interés (índice {minerals[i]:.2f})",
            )
        )

    ice = grids.ice[rows, cols]
    for i in np.nonzero(ice >= ICE_THRESHOLD)[0]:
        candidates.append(
            (float(ice[i]), int(i), "ice", f"Posible hielo somero (índice {ice[i]:.2f})")
        )

    # Las de mayor valor primero, descartando las que quedan muy cerca de otra.
    stops: list[tuple[int, str, str]] = []
    for _, i, kind, reason in sorted(candidates, reverse=True):
        if all(abs(i - j) >= MIN_GAP for j, _, _ in stops):
            stops.append((i, kind, reason))
    return sorted(stops)
