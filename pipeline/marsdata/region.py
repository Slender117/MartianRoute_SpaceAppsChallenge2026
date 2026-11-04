"""Definición de una región y su grilla común (equirectangular sobre el bbox)."""

import math
from dataclasses import dataclass, field
from pathlib import Path

import yaml

MARS_RADIUS_M = 3_389_500.0
METERS_PER_DEGREE = math.pi * MARS_RADIUS_M / 180

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "regions.yaml"


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
    demo: dict | None = None

    def __post_init__(self) -> None:
        lon_min, lat_min, lon_max, lat_max = self.bbox
        if not (-180 <= lon_min < lon_max <= 180 and -90 <= lat_min < lat_max <= 90):
            raise ValueError(f"{self.id}: bbox fuera de la convención de -180 a 180: {self.bbox}")

    @property
    def shape(self) -> tuple[int, int]:
        return self.size, self.size

    @property
    def resolution_m(self) -> float:
        """Tamaño de celda aproximado (usa el lado norte-sur, que no depende de la latitud)."""
        _, lat_min, _, lat_max = self.bbox
        return (lat_max - lat_min) * METERS_PER_DEGREE / (self.size - 1)


def load_regions(path: Path = CONFIG_PATH) -> dict[str, Region]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))["regions"]
    return {rid: Region(id=rid, **{**cfg, "bbox": tuple(cfg["bbox"])}) for rid, cfg in raw.items()}
