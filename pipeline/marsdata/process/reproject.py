"""Reproyección de cualquier GeoTIFF a la grilla común de la región."""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject
from scipy.ndimage import distance_transform_edt

from marsdata.region import MARS_RADIUS_M, Region

# Coordenadas geográficas sobre la esfera de Marte (IAU 2000). Latitud y longitud planetocéntricas
# no cambian entre esferas de distinto radio (3,389.5 km aquí y 3,396.19 km en los mosaicos de
# USGS): solo cambia la altura, que no se reproyecta.
MARS_GEOGRAPHIC = f"+proj=longlat +R={MARS_RADIUS_M} +no_defs"


def geographic_crs(crs) -> str:
    """Coordenadas geográficas sobre el mismo cuerpo que `crs` (esfera o elipsoide)."""
    params = crs.to_dict()
    if "R" in params:
        return f"+proj=longlat +R={params['R']} +no_defs"
    return f"+proj=longlat +a={params['a']} +b={params.get('b', params['a'])} +no_defs"


def warp_to_region(
    src_path: Path,
    region: Region,
    resampling: Resampling = Resampling.bilinear,
    shape: tuple[int, int] | None = None,
    bounds: tuple[float, float, float, float] | None = None,
) -> np.ndarray:
    """Reproyecta la banda 1 a la grilla de la región; NaN donde el archivo no tiene dato.

    Por defecto usa la grilla de la API (`region.grid_bounds`). Las texturas pasan `shape` y
    `bounds=region.bbox`, porque una textura se estira de borde a borde de la malla.
    """
    h, w = shape or region.shape
    dst = np.full((h, w), np.nan, dtype=np.float32)
    with rasterio.open(src_path) as src:
        reproject(
            source=rasterio.band(src, 1),
            destination=dst,
            dst_transform=from_bounds(*(bounds or region.grid_bounds), w, h),
            dst_crs=MARS_GEOGRAPHIC,
            dst_nodata=np.nan,
            resampling=resampling,
        )
    return dst


def warp_array_to_region(
    data: np.ndarray, transform, crs, region: Region, resampling: Resampling = Resampling.average
) -> np.ndarray:
    """Como `warp_to_region`, para una banda en memoria con su transform y CRS (NaN = sin dato)."""
    h, w = region.shape
    dst = np.full((h, w), np.nan, dtype=np.float32)
    reproject(
        source=data.astype(np.float32),
        destination=dst,
        src_transform=transform,
        src_crs=crs,
        src_nodata=np.nan,
        dst_transform=from_bounds(*region.grid_bounds, w, h),
        dst_crs=MARS_GEOGRAPHIC,
        dst_nodata=np.nan,
        resampling=resampling,
    )
    return dst


def coverage(grid: np.ndarray) -> float:
    """Fracción de celdas con dato (HE1). Se mide antes de rellenar."""
    return float(np.isfinite(grid).mean())


def fill_nearest(grid: np.ndarray) -> np.ndarray:
    """Rellena cada hueco con el valor de la celda con dato más cercana."""
    holes = ~np.isfinite(grid)
    if not holes.any():
        return grid.astype(np.float32)
    if holes.all():
        raise ValueError("la grilla no tiene ninguna celda con dato")
    nearest = distance_transform_edt(holes, return_distances=False, return_indices=True)
    return grid[tuple(nearest)].astype(np.float32)


def fill_nodata(grid: np.ndarray, value: float | None = None) -> np.ndarray:
    """Rellena huecos con un valor fijo o con la mediana de la grilla."""
    fill = np.nanmedian(grid) if value is None else value
    return np.where(np.isfinite(grid), grid, fill).astype(np.float32)
