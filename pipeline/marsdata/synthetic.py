"""Synthetic crater-shaped region, to develop without real data.

It generates a DEM with a crater rim and a delta, plausible layers and a fake rover traverse.
It lets the web and the API work in parallel while the real pipeline is completed.

The crater floor is shaped so the regions.yaml demo scenario separates the three modes:
a ridge with a single pass forces all of them to detour. Then a boulder field crosses the direct
path: Fast goes through it and Safe goes around. Science detours toward a mineral strip on
loose sediment, which Safe avoids. apps/api/tests/test_demo_scenario.py checks it.

Positions are fractions of a fixed geographic frame per region (FRAMES), not of the bbox: that way,
cropping or moving the bbox does not shift the terrain against the demo points, given in lat/lon.
"""

import numpy as np
from scipy.ndimage import gaussian_filter

from marsdata.process.terrain import normalize, slope_degrees
from marsdata.region import Region

# Scenario frame (lon_min, lat_min, lon_max, lat_max): the bbox it was designed with. A region
# without a frame uses its own bbox.
FRAMES = {"jezero": (77.25, 18.30, 77.60, 18.65)}

# Positions as a fraction of the frame: (row, column), with row 0 to the north.
RIDGE_COL = 0.50
PASS = (0.62, 0.50)
ROCK_FIELD = (0.565, 0.40)
MINERAL_STRIP = ((0.50, 0.475), (0.385, 0.335))


def _noise(shape: tuple[int, int], sigma: float, rng: np.random.Generator) -> np.ndarray:
    return normalize(gaussian_filter(rng.standard_normal(shape), sigma), 0, 100)


def _blob(yy, xx, cy, cx, r) -> np.ndarray:
    return np.exp(-(((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * r**2)))


def _strip(yy, xx, a, b, width) -> np.ndarray:
    """Gaussian strip around the a-b segment."""
    ay, ax = a
    by, bx = b
    dy, dx = by - ay, bx - ax
    t = np.clip(((yy - ay) * dy + (xx - ax) * dx) / (dy**2 + dx**2), 0, 1)
    return np.exp(-(((yy - (ay + t * dy)) ** 2 + (xx - (ax + t * dx)) ** 2) / (2 * width**2)))


def _frame(region: Region) -> tuple[float, float, float, float]:
    return FRAMES.get(region.id, region.bbox)


def _frame_coords(region: Region) -> tuple[np.ndarray, np.ndarray]:
    """(row, column) of each cell as a fraction of the frame; 0–1 when the bbox is the frame."""
    lon_min, lat_min, lon_max, lat_max = region.bbox
    f_lon_min, f_lat_min, f_lon_max, f_lat_max = _frame(region)
    t = np.arange(region.size) / (region.size - 1)
    lat = lat_max - t * (lat_max - lat_min)
    lon = lon_min + t * (lon_max - lon_min)
    yy = (f_lat_max - lat) / (f_lat_max - f_lat_min)
    xx = (lon - f_lon_min) / (f_lon_max - f_lon_min)
    return np.meshgrid(yy, xx, indexing="ij")


def make_grids(region: Region, seed: int = 7) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    n = region.size
    yy, xx = _frame_coords(region)
    r = np.hypot(yy - 0.5, xx - 0.55)

    # Crater: flat floor, steep wall and raised rim (meters).
    floor = -2600.0
    crater = np.where(r < 0.38, floor, floor + 900 * np.clip((r - 0.38) / 0.06, 0, 1))
    rim = 350 * np.exp(-(((r - 0.45) / 0.03) ** 2))
    delta = 120 * _blob(yy, xx, 0.42, 0.25, 0.08)  # delta fan to the west
    # North-south ridge from wall to wall of the crater, broken only by the pass.
    gap = np.exp(-(((yy - PASS[0]) / 0.018) ** 2))
    inside_crater = np.clip((0.42 - r) / 0.03, 0, 1)
    ridge = 240 * np.exp(-(((xx - RIDGE_COL) / 0.008) ** 2)) * (1 - 0.95 * gap) * inside_crater
    dem = crater + rim + delta + ridge + 40 * (_noise((n, n), n / 40, rng) - 0.5)
    dem = gaussian_filter(dem, 1.5).astype(np.float32)

    # Elongated boulder field, perpendicular to the direct path between the pass and the target.
    across = (xx - ROCK_FIELD[1]) * 0.73 + (yy - ROCK_FIELD[0]) * 0.68
    along = (xx - ROCK_FIELD[1]) * 0.68 - (yy - ROCK_FIELD[0]) * 0.73
    rock_field = np.exp(-((across / 0.016) ** 4)) * np.exp(-((along / 0.055) ** 4))

    rocks = (_noise((n, n), 2, rng) > 0.8).astype(float)
    hazard = normalize(gaussian_filter(rocks, 1.5) + 0.5 * np.exp(-(((r - 0.42) / 0.04) ** 2)))
    hazard = np.clip(hazard + rock_field, 0, 1).astype(np.float32)
    # Sand between the boulders and loose sediment on the mineral strip: low thermal inertia.
    strip = _strip(yy, xx, *MINERAL_STRIP, 0.012)
    thermal_inertia = (0.5 + 0.3 * _noise((n, n), n / 25, rng)) * (1 - 0.7 * rock_field)
    thermal_inertia *= 1 - 0.7 * np.exp(-(((1 - strip) / 0.5) ** 2))

    minerals = normalize(
        _blob(yy, xx, 0.42, 0.25, 0.05)  # delta
        + 0.8 * _blob(yy, xx, 0.2, 0.7, 0.04)  # carbonatos
        + 0.9 * strip
    )
    ice = normalize(np.clip(0.3 - yy, 0, None) + 0.2 * _noise((n, n), n / 30, rng))

    return {
        "dem": dem,
        "slope": slope_degrees(dem, region.resolution_m),
        "hazard": hazard,
        "thermal_inertia": thermal_inertia.astype(np.float32),
        "ice": ice,
        "minerals": minerals,
    }


def make_traverse(region: Region, seed: int = 7) -> list[tuple[float, float]]:
    """Fake traverse from the base, through the pass, toward the delta, as a list of (lat, lon)."""
    rng = np.random.default_rng(seed)
    lon_min, lat_min, lon_max, lat_max = _frame(region)
    dlat, dlon = lat_max - lat_min, lon_max - lon_min
    start = np.array([region.base["lat"], region.base["lon"]])
    gap = np.array([lat_max - PASS[0] * dlat, lon_min + PASS[1] * dlon])
    target = np.array([lat_min + 0.58 * dlat, lon_min + 0.25 * dlon])

    t = np.linspace(0, 1, 60)
    pts = np.column_stack(
        [np.interp(t, [0, 0.3, 1], [start[i], gap[i], target[i]]) for i in range(2)]
    )
    # The noise fades at the ends and at the pass so it does not hit the ridge.
    fade = np.minimum(1, 8 * np.minimum(t, 1 - t, np.abs(t - 0.3)))[:, None]
    pts = pts + gaussian_filter(rng.standard_normal((60, 2)), 4, axes=0) * 0.002 * fade
    return [(float(lat), float(lon)) for lat, lon in pts]
