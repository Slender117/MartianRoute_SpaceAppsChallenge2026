"""Derivados del DEM: pendiente y normalización de capas."""

import numpy as np


def slope_degrees(dem: np.ndarray, resolution_m: float) -> np.ndarray:
    dy, dx = np.gradient(dem.astype(np.float64), resolution_m)
    return np.degrees(np.arctan(np.hypot(dx, dy))).astype(np.float32)


def normalize(grid: np.ndarray, lo_pct: float = 2, hi_pct: float = 98) -> np.ndarray:
    """Escala a 0–1 recortando extremos por percentil (robusto a outliers)."""
    lo, hi = np.nanpercentile(grid, [lo_pct, hi_pct])
    if hi <= lo:
        return np.zeros_like(grid, dtype=np.float32)
    return np.clip((grid - lo) / (hi - lo), 0, 1).astype(np.float32)
