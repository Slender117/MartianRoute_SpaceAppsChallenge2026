"""Recorrido real de un rover en la región: el trecho continuo más largo, con la elevación del DEM.

Misma lógica que science/convert_traverse.py (Edgar): el archivo de MMGIS trae una LineString por
sol; se unen en orden, se parten donde el recorrido sale del recuadro o hay un salto mayor que
`max_gap_m` (la API uniría esos puntos con una recta e inventaría camino) y se conserva el trecho
más largo. La elevación se muestrea de la grilla de la región, la misma que usan las rutas.
"""

import json
import math
from itertools import pairwise
from pathlib import Path

import numpy as np

from marsdata.region import MARS_RADIUS_M, REPO_DIR, Region

MAX_GAP_M = 30.0  # el espaciado normal del archivo llega a 12 m

Point = tuple[float, float, int]  # lon, lat, sol


def haversine_m(a: Point, b: Point) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * MARS_RADIUS_M * math.asin(math.sqrt(h))


def load_points(path: Path) -> list[Point]:
    """(lon, lat, sol) en orden de sol, sin los puntos repetidos en las uniones de tramos."""
    features = json.loads(path.read_text(encoding="utf-8"))["features"]
    out: list[Point] = []
    for f in sorted(features, key=lambda f: f["properties"]["sol"]):
        sol = int(f["properties"]["sol"])
        for lon, lat, *_ in f["geometry"]["coordinates"]:
            if not out or (lon, lat) != out[-1][:2]:
                out.append((lon, lat, sol))
    return out


def continuous_runs(points: list[Point], bbox, max_gap_m: float = MAX_GAP_M) -> list[list[Point]]:
    """Trechos dentro del bbox y sin saltos mayores que `max_gap_m`."""
    lon_min, lat_min, lon_max, lat_max = bbox
    runs, cur = [], []
    for p in points:
        inside = lon_min <= p[0] <= lon_max and lat_min <= p[1] <= lat_max
        if not inside or (cur and haversine_m(cur[-1], p) > max_gap_m):
            if cur:
                runs.append(cur)
            cur = []
        if inside:
            cur.append(p)
    return runs + [cur] if cur else runs


def run_length_m(run: list[Point]) -> float:
    return sum(haversine_m(a, b) for a, b in pairwise(run))


def sample_grid(grid: np.ndarray, region: Region, lats, lons) -> np.ndarray:
    """Interpolación bilineal en la grilla de la región (fila 0 = lat_max, como en la API)."""
    lon_min, lat_min, lon_max, lat_max = region.bbox
    h, w = grid.shape
    rows = np.clip((lat_max - np.asarray(lats)) / (lat_max - lat_min) * (h - 1), 0, h - 1)
    cols = np.clip((np.asarray(lons) - lon_min) / (lon_max - lon_min) * (w - 1), 0, w - 1)
    r0 = np.minimum(np.floor(rows).astype(int), h - 2)
    c0 = np.minimum(np.floor(cols).astype(int), w - 2)
    fr, fc = rows - r0, cols - c0
    top = grid[r0, c0] * (1 - fc) + grid[r0, c0 + 1] * fc
    bottom = grid[r0 + 1, c0] * (1 - fc) + grid[r0 + 1, c0 + 1] * fc
    return top * (1 - fr) + bottom * fr


def build_traverse(
    region: Region, dem: np.ndarray, rover: str, max_gap_m: float = MAX_GAP_M
) -> tuple[list[tuple[float, float, float]], dict] | None:
    """[(lat, lon, elevación)] del trecho más largo y sus propiedades; None si no entra ninguno."""
    path = REPO_DIR / region.traverse_files[rover]
    runs = continuous_runs(load_points(path), region.bbox, max_gap_m)
    if not runs:
        return None
    best = max(runs, key=run_length_m)
    lons = np.array([p[0] for p in best])
    lats = np.array([p[1] for p in best])
    elev = sample_grid(dem, region, lats, lons)
    coords = [
        (float(la), float(lo), round(float(z), 2))
        for la, lo, z in zip(lats, lons, elev, strict=True)
    ]
    props = {
        "rover": rover,
        "source": path.name,
        "sol_min": best[0][2],
        "sol_max": best[-1][2],
        "length_m": round(run_length_m(best), 1),
        "max_gap_m": max_gap_m,
        "elevation_source": "dem.npy",
    }
    return coords, props
