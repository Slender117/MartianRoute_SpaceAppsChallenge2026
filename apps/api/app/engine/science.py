"""Suggested stops along the route."""

import numpy as np

from app.storage import RegionGrids

SCIENCE_THRESHOLD = 0.6
ICE_THRESHOLD = 0.6
# Minimum spacing between stops, in route points.
MIN_GAP = 15


def find_stops(grids: RegionGrids, path: np.ndarray) -> list[tuple[int, str, str]]:
    """Return (index along the route, type, reason) for each stop."""
    rows, cols = path[:, 0], path[:, 1]
    candidates: list[tuple[float, int, str, str]] = []

    minerals = grids.minerals[rows, cols]
    for i in np.nonzero(minerals >= SCIENCE_THRESHOLD)[0]:
        candidates.append(
            (
                float(minerals[i]),
                int(i),
                "science",
                f"Minerals of interest (index {minerals[i]:.2f})",
            )
        )

    ice = grids.ice[rows, cols]
    for i in np.nonzero(ice >= ICE_THRESHOLD)[0]:
        candidates.append(
            (float(ice[i]), int(i), "ice", f"Possible shallow ice (index {ice[i]:.2f})")
        )

    # Highest value first, dropping the ones too close to another.
    stops: list[tuple[int, str, str]] = []
    for _, i, kind, reason in sorted(candidates, reverse=True):
        if all(abs(i - j) >= MIN_GAP for j, _, _ in stops):
            stops.append((i, kind, reason))
    return sorted(stops)
