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
    baseline = "baseline"  # mínima distancia: la referencia contra la que se miden los modos


# Los modos que elige el astronauta. La línea base no es uno: solo sirve para comparar.
PLANNING_MODES = (WalkMode.safe, WalkMode.fast, WalkMode.science)


class SuitLimits(BaseModel):
    autonomy_h: float = Field(8.0, gt=0, description="Autonomía del traje en horas")
    max_slope_deg: float = Field(20.0, gt=0, le=60, description="Pendiente máxima caminable")
    max_dist_km: float = Field(10.0, gt=0, description="Distancia máxima a la base")
    task_h: float = Field(
        0.0,
        ge=0,
        description="Horas de trabajo fijo de la EVA, sin caminar (paradas, muestreo); se suman"
        " en el destino. Sin valor por defecto con fuente: 0 hasta que el equipo lo fije",
    )
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
    value: float = Field(description="Índice de minerales o de hielo en la parada (0-1)")


class AlertSeverity(StrEnum):
    warning = "warning"  # conviene revisarlo, pero la EVA sigue dentro de los límites
    critical = "critical"  # rompe un límite: la EVA no es viable tal como está planeada


class Alert(BaseModel):
    at: int = Field(description="Índice del punto de la ruta de ida donde aplica")
    type: str  # "slope" | "autonomy" | "distance" | "radiation" | "climate"
    severity: AlertSeverity = AlertSeverity.warning
    message: str = Field(description="Texto en español; la web arma el de otros idiomas con code")
    code: str = Field(
        description="Variante de la alerta: steep_segment, autonomy_over_suit, autonomy_reserve,"
        " too_far, dose_over_limit o solar_event"
    )
    values: dict[str, float] = Field(
        default_factory=dict, description="Cifras del mensaje, para traducirlo sin la API"
    )


class CostBreakdown(BaseModel):
    slope: float
    hazard: float
    instability: float
    science_bonus: float


class O2Interval(BaseModel):
    """O₂ por astronauta entre las dos cotas de gravedad del modelo de Minetti.

    No hay valor central: falta la fuente de cómo cambia el costo en plano con la gravedad.
    """

    low_kg: float = Field(description="Cota baja: el costo en plano no cambia con la gravedad")
    high_kg: float = Field(description="Cota alta: el costo en plano escala con la gravedad")


class RouteDelta(BaseModel):
    """Diferencia de una ruta contra otra de referencia (esta ruta menos la de referencia)."""

    distance_km: float
    duration_h: float
    duration_sols: float
    o2_estimate_kg: float
    o2_interval_kg: O2Interval = Field(description="Diferencia en cada cota del intervalo de O₂")
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
    o2_estimate_kg: float = Field(
        description="Referencia: O₂ por tiempo (duración × tasa), sin efecto de la pendiente. La"
        " cifra oficial es o2_interval_kg; esta no se muestra en la interfaz"
    )
    o2_crew_kg: float = Field(description="O₂ de la EVA para toda la pareja")
    o2_interval_kg: O2Interval = Field(
        description="Cifra oficial de O₂ de la EVA por astronauta: caminata según la pendiente de"
        " cada tramo (Minetti) más el trabajo fijo a la tasa por hora"
    )
    radiation_msv: float = Field(description="Dosis equivalente de fondo durante la EVA")
    solar_event_mgy: float | None = Field(
        description="Dosis absorbida del escenario de evento solar; no se suma a radiation_msv"
    )
    science_km: float = Field(
        description="Kilómetros de la ida sobre terreno de interés científico"
    )
    point_of_no_return: int | None = Field(
        description="Índice del primer punto de la ida desde donde el regreso a pie ya no cabe en"
        " la autonomía planeable (la autonomía menos la reserva más estricta)"
    )
    point_of_no_return_km: float | None = Field(
        description="Kilómetros de la ida hasta el punto de no retorno"
    )
    stops: list[Stop]
    alerts: list[Alert]
    feasible: bool = Field(description="Falso si alguna alerta crítica rompe un límite")
    cost_breakdown: CostBreakdown
    vs_safe: RouteDelta | None = Field(None, description="Diferencia contra la ruta Segura")
    vs_baseline: RouteDelta | None = Field(
        None, description="Diferencia contra la línea base de mínima distancia"
    )
    synthetic_data: bool = Field(description="Verdadero si la región usa datos de prueba")
    provenance: dict[str, Provenance] = Field(description="Etiqueta de cada cifra de la respuesta")
