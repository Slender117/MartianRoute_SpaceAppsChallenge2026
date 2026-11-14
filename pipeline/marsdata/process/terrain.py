"""Derivados del DEM: validación, pendiente, rugosidad y normalización de capas."""

from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from marsdata.process.reproject import fill_nearest, warp_array_to_region
from marsdata.region import METERS_PER_DEGREE, Region

# Rango plausible de elevaciones en Marte, en metros. USGS Astropedia da una elevación máxima de
# 22.64 km y una depresión máxima de 7.55 km; se deja margen para el datum de cada producto.
MARS_ELEVATION_RANGE_M = (-9_000.0, 23_000.0)

# Rugosidad para la capa de riesgo donde no hay clasificación de terreno (Gale). Con el DEM a 5 m,
# una gaussiana de 10 m deja el relieve de unos 10 a 50 m (escarpes, crestas, ondulaciones) que la
# pendiente a ~25 m por celda no ve. Es una elección del proyecto, no una cifra publicada.
ROUGHNESS_SIGMA_M = 10.0


class ElevationError(ValueError):
    """La capa de elevación no es un DEM: tipo entero (imagen de 0 a 255) o valores imposibles."""


def validate_elevation(src_path: Path, grid: np.ndarray) -> None:
    """Falla si el archivo no es flotante o si la grilla tiene alturas fuera del rango de Marte."""
    import rasterio

    with rasterio.open(src_path) as src:
        dtype = np.dtype(src.dtypes[0])
    if dtype.kind != "f":
        raise ElevationError(
            f"{src_path.name} es {dtype}: un DEM es Float32 o Float64 (¿imagen de visualización?)"
        )
    values = grid[np.isfinite(grid)]
    if values.size == 0:
        raise ElevationError(f"{src_path.name} no tiene datos dentro de la región")
    lo, hi = MARS_ELEVATION_RANGE_M
    if values.min() < lo or values.max() > hi:
        raise ElevationError(
            f"{src_path.name} tiene alturas de {values.min():.0f} a {values.max():.0f} m, "
            f"fuera del rango de Marte ({lo:.0f} a {hi:.0f} m)"
        )


def slope_degrees(dem: np.ndarray, dy_m: float, dx_m: float | None = None) -> np.ndarray:
    """Pendiente en grados. `dy_m` es el lado norte-sur de la celda y `dx_m` el este-oeste."""
    dy, dx = np.gradient(dem.astype(np.float64), dy_m, dx_m if dx_m else dy_m)
    return np.degrees(np.arctan(np.hypot(dx, dy))).astype(np.float32)


def local_relief(z: np.ndarray, pixel_m: float, sigma_m: float = ROUGHNESS_SIGMA_M) -> np.ndarray:
    """Elevación menos su versión suavizada con una gaussiana de `sigma_m` m. NaN = sin dato."""
    holes = ~np.isfinite(z)
    filled = fill_nearest(z).astype(np.float64)
    smooth = gaussian_filter(filled, sigma=sigma_m / pixel_m, mode="nearest")
    relief = (filled - smooth).astype(np.float32)
    relief[holes] = np.nan
    return relief


def roughness_to_region(
    dem_path: Path, region: Region, sigma_m: float = ROUGHNESS_SIGMA_M
) -> np.ndarray:
    """RMS del relieve local en cada celda de la grilla (m), calculado sobre el DEM sin reducir."""
    import rasterio

    with rasterio.open(dem_path) as src:
        z = src.read(1, masked=True).astype(np.float32).filled(np.nan)
        pixel_m = src.res[1] * METERS_PER_DEGREE if src.crs.is_geographic else src.res[1]
        relief = local_relief(z, pixel_m, sigma_m)
        mean_square = warp_array_to_region(relief**2, src.transform, src.crs, region)
    return np.sqrt(mean_square)


def normalize(grid: np.ndarray, lo_pct: float = 2, hi_pct: float = 98) -> np.ndarray:
    """Escala a 0–1 recortando extremos por percentil (robusto a outliers)."""
    lo, hi = np.nanpercentile(grid, [lo_pct, hi_pct])
    if hi <= lo:
        return np.zeros_like(grid, dtype=np.float32)
    return np.clip((grid - lo) / (hi - lo), 0, 1).astype(np.float32)
