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
    distance_ratio: float = Field(description="Distancia de la ruta dividida entre la del rover")
    mean_separation_m: float = Field(description="Separación media de la ruta al recorrido real")
    max_separation_m: float


class ValidationResponse(BaseModel):
    region: str
    rover: str
    synthetic_data: bool = Field(description="Verdadero si el recorrido o el terreno son de prueba")
    points_outside: int = Field(description="Puntos del recorrido que quedan fuera de la región")
    traverse: TrackMetrics
    routes: dict[WalkMode, RouteValidation]
    provenance: dict[str, Provenance]
