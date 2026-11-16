"""Reprojects any GeoTIFF to the region's common grid."""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject
from scipy.ndimage import distance_transform_edt

from marsdata.region import MARS_RADIUS_M, Region

# Geographic coordinates on the Mars sphere (IAU 2000). Planetocentric latitude and longitude
# do not change between spheres of different radius (3,389.5 km here and 3,396.19 km in the USGS
# mosaics): only the height changes, and it is not reprojected.
MARS_GEOGRAPHIC = f"+proj=longlat +R={MARS_RADIUS_M} +no_defs"


def geographic_crs(crs) -> str:
    """Geographic coordinates on the same body as `crs` (sphere or ellipsoid)."""
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
    """Reprojects band 1 to the region grid; NaN where the file has no data.

    By default it uses the API grid (`region.grid_bounds`). Textures pass `shape` and
    `bounds=region.bbox`, because a texture stretches from edge to edge of the mesh.
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
    """Like `warp_to_region`, for an in-memory band with its transform and CRS (NaN = no data)."""
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
    """Fraction of cells with data (HE1). It is measured before filling."""
    return float(np.isfinite(grid).mean())


def fill_nearest(grid: np.ndarray) -> np.ndarray:
    """Fills each gap with the value of the nearest cell with data."""
    holes = ~np.isfinite(grid)
    if not holes.any():
        return grid.astype(np.float32)
    if holes.all():
        raise ValueError("the grid has no cell with data")
    nearest = distance_transform_edt(holes, return_distances=False, return_indices=True)
    return grid[tuple(nearest)].astype(np.float32)


def fill_nodata(grid: np.ndarray, value: float | None = None) -> np.ndarray:
    """Fills gaps with a fixed value or with the grid median."""
    fill = np.nanmedian(grid) if value is None else value
    return np.where(np.isfinite(grid), grid, fill).astype(np.float32)
