"""Definition of a region and its common grid (equirectangular over the bbox)."""

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
    # Demo scenario: `demo` for the synthetic region and `demo_real` for the one built with real
    # data. If `demo_real` is missing, the real one uses `demo`.
    demo: dict | None = None
    demo_real: dict | None = None
    # Class-to-risk CSV table for the categorical `hazard` layer (path from the repo root).
    hazard_table: str | None = None
    # Without a `hazard` source, risk is derived from the DEM: "roughness" (process/terrain.py).
    hazard_proxy: str | None = None
    # Real traverse of each rover: MMGIS file with one LineString per sol (from the root).
    traverse_files: dict[str, str] = field(default_factory=dict)
    # Maximum jump between consecutive traverse points; if missing, process/traverse.py's (30 m).
    traverse_max_gap_m: float | None = None
    # Names for the 3D view: [{name, lat, lon, source, only?}]; only = "synthetic" or "real".
    labels: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        lon_min, lat_min, lon_max, lat_max = self.bbox
        if not (-180 <= lon_min < lon_max <= 180 and -90 <= lat_min < lat_max <= 90):
            raise ValueError(f"{self.id}: bbox outside the -180 to 180 convention: {self.bbox}")
        if self.hazard_proxy not in (None, "roughness"):
            raise ValueError(f"{self.id}: hazard_proxy desconocido: {self.hazard_proxy}")

    @property
    def shape(self) -> tuple[int, int]:
        return self.size, self.size

    @property
    def resolution_m(self) -> float:
        """Approximate cell size (uses the north-south side, which does not depend on latitude)."""
        _, lat_min, _, lat_max = self.bbox
        return (lat_max - lat_min) * METERS_PER_DEGREE / (self.size - 1)

    @property
    def cell_size_m(self) -> tuple[float, float]:
        """(north-south, east-west) in meters: the east-west side shrinks with cos(latitude)."""
        lon_min, lat_min, lon_max, lat_max = self.bbox
        cos_lat = math.cos(math.radians((lat_min + lat_max) / 2))
        ew = (lon_max - lon_min) * METERS_PER_DEGREE * cos_lat / (self.size - 1)
        return self.resolution_m, ew

    @property
    def grid_bounds(self) -> tuple[float, float, float, float]:
        """Outer edges of the grid, in degrees.

        As in the API (app/geo.py), row 0 falls on lat_max and column 0 on lon_min: the
        centers of the edge cells are on the bbox and the grid sticks out half a cell.
        """
        lon_min, lat_min, lon_max, lat_max = self.bbox
        half_lon = (lon_max - lon_min) / (self.size - 1) / 2
        half_lat = (lat_max - lat_min) / (self.size - 1) / 2
        return lon_min - half_lon, lat_min - half_lat, lon_max + half_lon, lat_max + half_lat


def load_regions(path: Path = CONFIG_PATH) -> dict[str, Region]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))["regions"]
    return {rid: Region(id=rid, **{**cfg, "bbox": tuple(cfg["bbox"])}) for rid, cfg in raw.items()}
