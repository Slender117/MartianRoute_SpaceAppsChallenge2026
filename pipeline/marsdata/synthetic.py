"""Región sintética con la forma de un cráter, para desarrollar sin datos reales.

Genera un DEM con borde de cráter y delta, capas plausibles y un recorrido falso del rover.
Sirve para que web y API trabajen en paralelo mientras el pipeline real se completa.

El piso del cráter está armado para que el escenario de demo de regions.yaml separe los tres modos:
una cresta con un solo paso obliga a todos a desviarse. Después, un campo de rocas cruza el camino
directo: Rápida lo atraviesa y Segura lo rodea. Científica se desvía hacia una franja de minerales
sobre sedimento suelto, que Segura evita. apps/api/tests/test_demo_scenario.py lo comprueba.
"""

import numpy as np
from scipy.ndimage import gaussian_filter

from marsdata.process.terrain import normalize, slope_degrees
from marsdata.region import Region

# Posiciones como fracción de la grilla: (fila, columna), con fila 0 al norte.
RIDGE_COL = 0.50
PASS = (0.62, 0.50)
ROCK_FIELD = (0.565, 0.40)
MINERAL_STRIP = ((0.50, 0.475), (0.385, 0.335))


def _noise(shape: tuple[int, int], sigma: float, rng: np.random.Generator) -> np.ndarray:
    return normalize(gaussian_filter(rng.standard_normal(shape), sigma), 0, 100)


def _blob(yy, xx, cy, cx, r) -> np.ndarray:
    return np.exp(-(((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * r**2)))


def _strip(yy, xx, a, b, width) -> np.ndarray:
    """Franja gaussiana alrededor del segmento a-b."""
    ay, ax = a
    by, bx = b
    dy, dx = by - ay, bx - ax
    t = np.clip(((yy - ay) * dy + (xx - ax) * dx) / (dy**2 + dx**2), 0, 1)
    return np.exp(-(((yy - (ay + t * dy)) ** 2 + (xx - (ax + t * dx)) ** 2) / (2 * width**2)))


def make_grids(region: Region, seed: int = 7) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    n = region.size
    yy, xx = np.mgrid[0:n, 0:n] / (n - 1)  # 0–1
    r = np.hypot(yy - 0.5, xx - 0.55)

    # Cráter: fondo plano, pared empinada y borde elevado (metros).
    floor = -2600.0
    crater = np.where(r < 0.38, floor, floor + 900 * np.clip((r - 0.38) / 0.06, 0, 1))
    rim = 350 * np.exp(-(((r - 0.45) / 0.03) ** 2))
    delta = 120 * _blob(yy, xx, 0.42, 0.25, 0.08)  # abanico deltaico al oeste
    # Cresta norte-sur de pared a pared del cráter, interrumpida solo por el paso.
    gap = np.exp(-(((yy - PASS[0]) / 0.018) ** 2))
    inside_crater = np.clip((0.42 - r) / 0.03, 0, 1)
    ridge = 240 * np.exp(-(((xx - RIDGE_COL) / 0.008) ** 2)) * (1 - 0.95 * gap) * inside_crater
    dem = crater + rim + delta + ridge + 40 * (_noise((n, n), n / 40, rng) - 0.5)
    dem = gaussian_filter(dem, 1.5).astype(np.float32)

    # Campo de rocas alargado, perpendicular al camino directo entre el paso y el objetivo.
    across = (xx - ROCK_FIELD[1]) * 0.73 + (yy - ROCK_FIELD[0]) * 0.68
    along = (xx - ROCK_FIELD[1]) * 0.68 - (yy - ROCK_FIELD[0]) * 0.73
    rock_field = np.exp(-((across / 0.016) ** 4)) * np.exp(-((along / 0.055) ** 4))

    rocks = (_noise((n, n), 2, rng) > 0.8).astype(float)
    hazard = normalize(gaussian_filter(rocks, 1.5) + 0.5 * np.exp(-(((r - 0.42) / 0.04) ** 2)))
    hazard = np.clip(hazard + rock_field, 0, 1).astype(np.float32)
    # Arena entre las rocas y sedimento suelto en la franja de minerales: baja inercia térmica.
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
    """Recorrido falso desde la base, por el paso, hacia el delta, como lista de (lat, lon)."""
    rng = np.random.default_rng(seed)
    lon_min, lat_min, lon_max, lat_max = region.bbox
    dlat, dlon = lat_max - lat_min, lon_max - lon_min
    start = np.array([region.base["lat"], region.base["lon"]])
    gap = np.array([lat_max - PASS[0] * dlat, lon_min + PASS[1] * dlon])
    target = np.array([lat_min + 0.58 * dlat, lon_min + 0.25 * dlon])

    t = np.linspace(0, 1, 60)
    pts = np.column_stack(
        [np.interp(t, [0, 0.3, 1], [start[i], gap[i], target[i]]) for i in range(2)]
    )
    # El ruido se apaga en los extremos y en el paso para no chocar con la cresta.
    fade = np.minimum(1, 8 * np.minimum(t, 1 - t, np.abs(t - 0.3)))[:, None]
    pts = pts + gaussian_filter(rng.standard_normal((60, 2)), 4, axes=0) * 0.002 * fade
    return [(float(lat), float(lon)) for lat, lon in pts]
