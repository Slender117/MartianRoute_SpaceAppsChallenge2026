from enum import StrEnum

from pydantic import BaseModel, Field


class Provenance(StrEnum):
    """De dónde sale una capa o una cifra."""

    observed = "observed"  # medida directa de un instrumento
    derived = "derived"  # calculada a partir de datos medidos
    modeled = "modeled"  # sale de un modelo o de un supuesto


class LatLon(BaseModel):
    """Planetocéntrico, longitud este, de -180 a 180 en toda la app."""

    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class WalkMode(StrEnum):
    safe = "safe"
    fast = "fast"
    science = "science"


class SuitLimits(BaseModel):
    autonomy_h: float = Field(8.0, gt=0, description="Autonomía del traje en horas")
    max_slope_deg: float = Field(20.0, gt=0, le=60, description="Pendiente máxima caminable")
    max_dist_km: float = Field(10.0, gt=0, description="Distancia máxima a la base")
    max_dose_msv: float | None = Field(
        None,
        gt=0,
        description="Límite de dosis por EVA en mSv; sin valor, solo se reporta la dosis",
    )


class CompareRequest(BaseModel):
    region: str
    start: LatLon | None = Field(
        None, description="Nodo base de la EVA; si falta, se usa la base de la región"
    )
    end: LatLon
    suit: SuitLimits = SuitLimits()
    solar_event: bool = Field(False, description="Escenario: evento solar durante la EVA")


class RouteRequest(CompareRequest):
    mode: WalkMode = WalkMode.safe


class PathPoint(LatLon):
    elev: float
    t_h: float = Field(description="Tiempo transcurrido en la ida al llegar a este punto, en horas")


class Stop(LatLon):
    type: str  # "science" | "ice"
    reason: str


class AlertSeverity(StrEnum):
    warning = "warning"  # conviene revisarlo, pero la EVA sigue dentro de los límites
    critical = "critical"  # rompe un límite: la EVA no es viable tal como está planeada


class Alert(BaseModel):
    at: int = Field(description="Índice del punto de la ruta de ida donde aplica")
    type: str  # "slope" | "autonomy" | "distance" | "radiation" | "climate"
    severity: AlertSeverity = AlertSeverity.warning
    message: str


class CostBreakdown(BaseModel):
    slope: float
    hazard: float
    instability: float
    science_bonus: float


class RouteDelta(BaseModel):
    """Diferencia de una ruta contra la ruta segura (esta ruta menos la segura)."""

    distance_km: float
    duration_h: float
    duration_sols: float
    o2_estimate_kg: float
    radiation_msv: float
    science_km: float
    shared_path: float = Field(description="Fracción de esta ruta que coincide con la segura (0-1)")


class RouteResponse(BaseModel):
    mode: WalkMode
    path: list[PathPoint] = Field(description="Ruta de ida; el regreso va por el mismo camino")
    distance_km: float = Field(description="Distancia de la EVA completa, ida y vuelta")
    duration_h: float = Field(description="Duración de la EVA completa, ida y vuelta")
    duration_sols: float
    outbound_km: float
    outbound_h: float
    return_h: float
    usable_autonomy_h: float = Field(description="Autonomía del traje menos la reserva")
    margin_h: float = Field(
        description="Autonomía utilizable menos duración; negativo si no alcanza"
    )
    o2_estimate_kg: float = Field(description="O₂ de la EVA por astronauta")
    o2_crew_kg: float = Field(description="O₂ de la EVA para toda la pareja")
    radiation_msv: float = Field(description="Dosis equivalente de fondo durante la EVA")
    solar_event_mgy: float | None = Field(
        description="Dosis absorbida del escenario de evento solar; no se suma a radiation_msv"
    )
    science_km: float = Field(
        description="Kilómetros de la ida sobre terreno de interés científico"
    )
    point_of_no_return: int | None
    stops: list[Stop]
    alerts: list[Alert]
    feasible: bool = Field(description="Falso si alguna alerta crítica rompe un límite")
    cost_breakdown: CostBreakdown
    vs_safe: RouteDelta | None = None
    synthetic_data: bool = Field(description="Verdadero si la región usa datos de prueba")
    provenance: dict[str, Provenance] = Field(description="Etiqueta de cada cifra de la respuesta")
