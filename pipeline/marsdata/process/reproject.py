"""Reproyección de cualquier GeoTIFF a la grilla común de la región."""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject

from marsdata.region import MARS_RADIUS_M, Region

# Coordenadas geográficas sobre la esfera de Marte (IAU 2000).
MARS_GEOGRAPHIC = f"+proj=longlat +R={MARS_RADIUS_M} +no_defs"


def warp_to_region(
    src_path: Path, region: Region, resampling: Resampling = Resampling.bilinear
) -> np.ndarray:
    h, w = region.shape
    dst = np.full((h, w), np.nan, dtype=np.float32)
    with rasterio.open(src_path) as src:
        reproject(
            source=rasterio.band(src, 1),
            destination=dst,
            dst_transform=from_bounds(*region.bbox, w, h),
            dst_crs=MARS_GEOGRAPHIC,
            dst_nodata=np.nan,
            resampling=resampling,
        )
    return dst


def fill_nodata(grid: np.ndarray, value: float | None = None) -> np.ndarray:
    """Rellena huecos con un valor fijo o con la mediana de la grilla."""
    fill = np.nanmedian(grid) if value is None else value
    return np.where(np.isfinite(grid), grid, fill).astype(np.float32)
