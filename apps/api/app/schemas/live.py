"""Datos recientes de NASA: clima espacial (DONKI), posición de Perseverance y sus imágenes."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.route import Provenance


class SourceInfo(BaseModel):
    name: str
    url: str = Field(description="Página pública de la fuente, para citarla")
    status: Literal["live", "snapshot"] = Field(
        description="live: consultada a NASA mientras corre la API; snapshot: copia guardada"
    )
    fetched_at: datetime = Field(description="Cuándo se obtuvo de NASA (UTC)")
    provenance: Provenance
    error: str | None = Field(None, description="Por qué no se pudo consultar en vivo")


class CmeArrival(BaseModel):
    simulation_id: str
    cme_id: str | None = None
    cme_start: datetime | None = None
    speed_km_s: float | None = None
    arrival_time: datetime = Field(description="Llegada prevista a Marte (UTC), según WSA-ENLIL")
    glancing_blow: bool
    minor_impact: bool
    model_completion: datetime
    link: str


class SpaceWeather(BaseModel):
    source: SourceInfo
    arrivals: list[CmeArrival] = Field(
        description="Llegadas previstas a Marte, la más reciente primero"
    )
    alert: CmeArrival | None = Field(
        None, description="Llegada dentro de la ventana de alerta alrededor de la hora actual"
    )
    alert_before_h: float = Field(description="La alerta empieza estas horas antes de la llegada")
    alert_after_h: float = Field(description="La alerta sigue estas horas después de la llegada")


class RoverPosition(BaseModel):
    source: SourceInfo
    rover: str
    sol: int
    site: int
    drive: int
    lat: float
    lon: float
    elevation_m: float | None = None
    odometry_km: float | None = Field(None, description="Distancia total recorrida")
    distance_to_base_km: float | None = Field(
        None, description="Distancia en línea recta a la base de la región pedida"
    )
    in_region: bool | None = Field(None, description="Si cae dentro del bbox de la región pedida")


class RoverImage(BaseModel):
    image_id: str
    sol: int
    taken_utc: datetime
    camera: str
    thumbnail_url: str
    full_url: str | None = None
    page_url: str | None = None


class RoverImages(BaseModel):
    source: SourceInfo
    latest_sol: int | None = None
    images: list[RoverImage]


class LiveResponse(BaseModel):
    generated_at: datetime
    space_weather: SpaceWeather
    rover: RoverPosition | None
    images: RoverImages
