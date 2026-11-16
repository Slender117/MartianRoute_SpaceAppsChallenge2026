from pydantic import BaseModel, Field

from app.schemas.route import Provenance, SuitLimits, WalkMode


class ValidationRequest(BaseModel):
    region: str
    rover: str
    suit: SuitLimits = SuitLimits()


class TrackMetrics(BaseModel):
    distance_km: float
    ascent_m: float = Field(description="Desnivel positivo acumulado")


class RouteValidation(TrackMetrics):
    distance_ratio: float = Field(description="Route distance divided by the rover's")
    mean_separation_m: float = Field(description="Mean separation of the route from the traverse")
    max_separation_m: float


class ValidationResponse(BaseModel):
    region: str
    rover: str
    synthetic_data: bool = Field(description="True if the traverse or the terrain are test data")
    points_outside: int = Field(description="Traverse points that fall outside the region")
    traverse: TrackMetrics
    routes: dict[WalkMode, RouteValidation]
    provenance: dict[str, Provenance]
