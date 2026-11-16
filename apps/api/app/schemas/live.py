"""Recent NASA data: space weather (DONKI), Perseverance's position and its images."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.route import Provenance


class SourceInfo(BaseModel):
    name: str
    url: str = Field(description="Public page of the source, to cite it")
    status: Literal["live", "snapshot"] = Field(
        description="live: queried from NASA while the API runs; snapshot: saved copy"
    )
    fetched_at: datetime = Field(description="When it was obtained from NASA (UTC)")
    provenance: Provenance
    error: str | None = Field(None, description="Why it could not be queried live")


class CmeArrival(BaseModel):
    simulation_id: str
    cme_id: str | None = None
    cme_start: datetime | None = None
    speed_km_s: float | None = None
    arrival_time: datetime = Field(description="Forecast arrival at Mars (UTC), per WSA-ENLIL")
    glancing_blow: bool
    minor_impact: bool
    model_completion: datetime
    link: str


class SpaceWeather(BaseModel):
    source: SourceInfo
    arrivals: list[CmeArrival] = Field(description="Forecast arrivals at Mars, most recent first")
    alert: CmeArrival | None = Field(
        None, description="Arrival inside the alert window around the current time"
    )
    alert_before_h: float = Field(description="The alert starts this many hours before arrival")
    alert_after_h: float = Field(description="The alert lasts this many hours after arrival")


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
        None, description="Straight-line distance to the base of the requested region"
    )
    in_region: bool | None = Field(None, description="Whether it is inside the region's bbox")


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
