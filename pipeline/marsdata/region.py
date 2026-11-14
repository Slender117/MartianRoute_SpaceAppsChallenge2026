"""Definición de una región y su grilla común (equirectangular sobre el bbox)."""

import math
from dataclasses import dataclass, field
from pathlib import Path

import yaml

MARS_RADIUS_M = 3_389_500.0
METERS_PER_DEGREE = math.pi * MARS_RADIUS_M / 180

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "regions.yaml"
REPO_DIR = Path(__file__).resolve().parents[2]


@dataclass
class Region:
    id: str
    name: str
    bbox: tuple[float, float, float, float]  # lon_min, lat_min, lon_max, lat_max
    size: int
    base: dict[str, float]
    traverses: list[str] = field(default_factory=list)
    sources: dict[str, str] = field(default_factory=dict)
    dataset_version: str = "0.1.0"
    # Escenario de demo: `demo` para la región sintética y `demo_real` para la construida con datos
    # reales. Si falta `demo_real`, la real usa `demo`.
    demo: dict | None = None
    demo_real: dict | None = None
    # Tabla CSV de clase a riesgo de la capa `hazard` categórica (ruta desde la raíz del repo).
    hazard_table: str | None = None
    # Sin fuente `hazard`, el riesgo se deriva del DEM: "roughness" (rugosidad, process/terrain.py).
    hazard_proxy: str | None = None
    # Recorrido real de cada rover: archivo de MMGIS con una LineString por sol (desde la raíz).
    traverse_files: dict[str, str] = field(default_factory=dict)
    # Salto máximo entre puntos seguidos del recorrido; si falta, el de process/traverse.py (30 m).
    traverse_max_gap_m: float | None = None
    # Nombres para la vista 3D: [{name, lat, lon, source, only?}]; only = "synthetic" o "real".
    labels: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        lon_min, lat_min, lon_max, lat_max = self.bbox
        if not (-180 <= lon_min < lon_max <= 180 and -90 <= lat_min < lat_max <= 90):
            raise ValueError(f"{self.id}: bbox fuera de la convención de -180 a 180: {self.bbox}")
        if self.hazard_proxy not in (None, "roughness"):
            raise ValueError(f"{self.id}: hazard_proxy desconocido: {self.hazard_proxy}")

    @property
    def shape(self) -> tuple[int, int]:
        return self.size, self.size

    @property
    def resolution_m(self) -> float:
        """Tamaño de celda aproximado (usa el lado norte-sur, que no depende de la latitud)."""
        _, lat_min, _, lat_max = self.bbox
        return (lat_max - lat_min) * METERS_PER_DEGREE / (self.size - 1)

    @property
    def cell_size_m(self) -> tuple[float, float]:
        """(norte-sur, este-oeste) en metros: el lado este-oeste se acorta con cos(latitud)."""
        lon_min, lat_min, lon_max, lat_max = self.bbox
        cos_lat = math.cos(math.radians((lat_min + lat_max) / 2))
        ew = (lon_max - lon_min) * METERS_PER_DEGREE * cos_lat / (self.size - 1)
        return self.resolution_m, ew

    @property
    def grid_bounds(self) -> tuple[float, float, float, float]:
        """Bordes exteriores de la grilla, en grados.

        Como en la API (app/geo.py), la fila 0 cae sobre lat_max y la columna 0 sobre lon_min: los
        centros de las celdas de los bordes están sobre el bbox y la grilla sobresale media celda.
        """
        lon_min, lat_min, lon_max, lat_max = self.bbox
        half_lon = (lon_max - lon_min) / (self.size - 1) / 2
        half_lat = (lat_max - lat_min) / (self.size - 1) / 2
        return lon_min - half_lon, lat_min - half_lat, lon_max + half_lon, lat_max + half_lat


def load_regions(path: Path = CONFIG_PATH) -> dict[str, Region]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))["regions"]
    return {rid: Region(id=rid, **{**cfg, "bbox": tuple(cfg["bbox"])}) for rid, cfg in raw.items()}
