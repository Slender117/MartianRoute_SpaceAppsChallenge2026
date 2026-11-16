"""Conversion between geographic coordinates and a region's grid cells.

The grids use an equirectangular projection over the region's bbox:
row 0 = lat_max, column 0 = lon_min.
"""

import math

import numpy as np

from app.schemas.region import RegionManifest
from app.schemas.route import LatLon

MARS_RADIUS_M = 3_389_500.0


class OutOfRegionError(ValueError):
    pass


def latlon_to_fractional(
    m: RegionManifest, lats: np.ndarray, lons: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Row and column with decimals, for traverses that do not fall on a cell center."""
    lon_min, lat_min, lon_max, lat_max = m.bbox
    h, w = m.shape
    rows = (lat_max - lats) / (lat_max - lat_min) * (h - 1)
    cols = (lons - lon_min) / (lon_max - lon_min) * (w - 1)
    return rows, cols


def latlon_to_cell(m: RegionManifest, lat: float, lon: float) -> tuple[int, int]:
    rows, cols = latlon_to_fractional(m, np.array(lat), np.array(lon))
    row, col = round(float(rows)), round(float(cols))
    if not (0 <= row < m.shape[0] and 0 <= col < m.shape[1]):
        raise OutOfRegionError(f"({lat}, {lon}) is outside region {m.id}")
    return row, col


def cell_to_latlon(m: RegionManifest, row: int, col: int) -> tuple[float, float]:
    lon_min, lat_min, lon_max, lat_max = m.bbox
    h, w = m.shape
    lat = lat_max - row / (h - 1) * (lat_max - lat_min)
    lon = lon_min + col / (w - 1) * (lon_max - lon_min)
    return lat, lon


def cell_size_m(m: RegionManifest) -> tuple[float, float]:
    """(height, width) of a cell: resolution_m is the north-south side; east-west is shorter."""
    lon_min, lat_min, lon_max, lat_max = m.bbox
    h, w = m.shape
    deg_per_row = (lat_max - lat_min) / (h - 1)
    deg_per_col = (lon_max - lon_min) / (w - 1)
    cos_lat = math.cos(math.radians((lat_min + lat_max) / 2))
    return m.resolution_m, m.resolution_m * deg_per_col / deg_per_row * cos_lat


def haversine_km(a: LatLon, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    lat1, lon1 = np.radians(a.lat), np.radians(a.lon)
    lat2, lon2 = np.radians(lats), np.radians(lons)
    h = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * MARS_RADIUS_M * np.arcsin(np.sqrt(h)) / 1000
