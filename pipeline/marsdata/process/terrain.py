"""DEM products: validation, slope, roughness and layer normalization."""

from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from marsdata.process.reproject import fill_nearest, warp_array_to_region
from marsdata.region import METERS_PER_DEGREE, Region

# Plausible elevation range on Mars, in meters. USGS Astropedia gives a maximum elevation of
# 22.64 km and a maximum depression of 7.55 km; a margin is left for each product's datum.
MARS_ELEVATION_RANGE_M = (-9_000.0, 23_000.0)

# Roughness for the risk layer where there is no terrain classification (Gale). With the DEM at 5 m,
# a 10 m Gaussian keeps the relief of about 10 to 50 m (scarps, ridges, ripples) that the
# slope at ~25 m per cell does not see. It is a project choice, not a published figure.
ROUGHNESS_SIGMA_M = 10.0


class ElevationError(ValueError):
    """The elevation layer is not a DEM: integer type (0 to 255 image) or impossible values."""


def validate_elevation(src_path: Path, grid: np.ndarray) -> None:
    """Fails if the file is not float or if the grid has heights outside the Mars range."""
    import rasterio

    with rasterio.open(src_path) as src:
        dtype = np.dtype(src.dtypes[0])
    if dtype.kind != "f":
        raise ElevationError(
            f"{src_path.name} is {dtype}: a DEM is Float32 or Float64 (a display image?)"
        )
    values = grid[np.isfinite(grid)]
    if values.size == 0:
        raise ElevationError(f"{src_path.name} has no data inside the region")
    lo, hi = MARS_ELEVATION_RANGE_M
    if values.min() < lo or values.max() > hi:
        raise ElevationError(
            f"{src_path.name} tiene alturas de {values.min():.0f} a {values.max():.0f} m, "
            f"outside the Mars range ({lo:.0f} to {hi:.0f} m)"
        )


def slope_degrees(dem: np.ndarray, dy_m: float, dx_m: float | None = None) -> np.ndarray:
    """Slope in degrees. `dy_m` is the north-south side of the cell and `dx_m` the east-west one."""
    dy, dx = np.gradient(dem.astype(np.float64), dy_m, dx_m if dx_m else dy_m)
    return np.degrees(np.arctan(np.hypot(dx, dy))).astype(np.float32)


def local_relief(z: np.ndarray, pixel_m: float, sigma_m: float = ROUGHNESS_SIGMA_M) -> np.ndarray:
    """Elevation minus its version smoothed with a `sigma_m` m Gaussian. NaN = no data."""
    holes = ~np.isfinite(z)
    filled = fill_nearest(z).astype(np.float64)
    smooth = gaussian_filter(filled, sigma=sigma_m / pixel_m, mode="nearest")
    relief = (filled - smooth).astype(np.float32)
    relief[holes] = np.nan
    return relief


def roughness_to_region(
    dem_path: Path, region: Region, sigma_m: float = ROUGHNESS_SIGMA_M
) -> np.ndarray:
    """RMS of the local relief in each grid cell (m), computed on the unreduced DEM."""
    import rasterio

    with rasterio.open(dem_path) as src:
        z = src.read(1, masked=True).astype(np.float32).filled(np.nan)
        pixel_m = src.res[1] * METERS_PER_DEGREE if src.crs.is_geographic else src.res[1]
        relief = local_relief(z, pixel_m, sigma_m)
        mean_square = warp_array_to_region(relief**2, src.transform, src.crs, region)
    return np.sqrt(mean_square)


def normalize(grid: np.ndarray, lo_pct: float = 2, hi_pct: float = 98) -> np.ndarray:
    """Scales to 0–1 clipping extremes by percentile (robust to outliers)."""
    lo, hi = np.nanpercentile(grid, [lo_pct, hi_pct])
    if hi <= lo:
        return np.zeros_like(grid, dtype=np.float32)
    return np.clip((grid - lo) / (hi - lo), 0, 1).astype(np.float32)
