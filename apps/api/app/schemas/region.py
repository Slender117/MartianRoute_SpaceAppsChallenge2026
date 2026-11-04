from typing import Self

from pydantic import BaseModel, Field, model_validator

from app.schemas.route import LatLon, Provenance


class LayerMeta(BaseModel):
    provenance: Provenance
    source: str = Field(description="ID del producto de origen")


class DemoScenario(BaseModel):
    label: str
    start: LatLon
    end: LatLon


class RegionManifest(BaseModel):
    id: str
    name: str
    # [lon_min, lat_min, lon_max, lat_max] en grados (planetocéntrico, este positivo)
    bbox: tuple[float, float, float, float]
    shape: tuple[int, int]  # (filas, columnas)
    resolution_m: float
    elevation_range: tuple[float, float]  # (min, max) en metros
    base: LatLon
    layers: list[str]
    traverses: list[str] = []

    dataset_version: str = "0.0.0"
    pipeline_commit: str | None = None
    crs: str | None = None
    synthetic: bool = False
    layer_meta: dict[str, LayerMeta] = {}
    checksums: dict[str, str] = Field(default={}, description="SHA-256 por archivo de la región")
    demo: DemoScenario | None = None

    @model_validator(mode="after")
    def _check_coordinates(self) -> Self:
        lon_min, lat_min, lon_max, lat_max = self.bbox
        if not (-180 <= lon_min < lon_max <= 180 and -90 <= lat_min < lat_max <= 90):
            raise ValueError(f"bbox fuera de la convención de -180 a 180: {self.bbox}")
        points = [self.base] + ([self.demo.start, self.demo.end] if self.demo else [])
        for p in points:
            if not (lat_min <= p.lat <= lat_max and lon_min <= p.lon <= lon_max):
                raise ValueError(f"({p.lat}, {p.lon}) queda fuera del bbox de {self.id}")
        return self


class RegionSummary(BaseModel):
    id: str
    name: str
    bbox: tuple[float, float, float, float]
    base: LatLon
