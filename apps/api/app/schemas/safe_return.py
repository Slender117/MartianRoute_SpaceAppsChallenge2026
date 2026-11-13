from pydantic import BaseModel, Field

from app.schemas.route import LatLon, Provenance, SuitLimits


class SafeReturnRequest(BaseModel):
    region: str
    base: LatLon | None = Field(
        None, description="Nodo base; si falta, se usa la base de la región"
    )
    suit: SuitLimits = SuitLimits()


class SafeReturnResponse(BaseModel):
    """Tiempo de regreso a pie a la base desde cada celda de la región."""

    region: str
    base: LatLon
    shape: tuple[int, int] = Field(description="(filas, columnas) de la grilla, como el manifest")
    bbox: tuple[float, float, float, float]
    return_minutes: str = Field(
        description="Minutos de regreso por celda: uint16 little-endian en base64, fila por fila,"
        " empezando por la fila norte (lat_max), igual que las grillas de la región"
    )
    no_return_value: int = Field(description="Valor de las celdas sin regreso posible")
    planned_limit_min: float = Field(
        description="Regreso máximo para que ida, trabajo fijo y regreso quepan en la autonomía"
        " planeable (autonomía menos la reserva más estricta: 20 % o 30 min)"
    )
    total_limit_min: float = Field(
        description="Regreso máximo gastando toda la autonomía, reserva incluida. Entre este"
        " límite y el planeable solo se vuelve consumiendo la reserva"
    )
    planned_area_fraction: float = Field(description="Fracción de la región dentro del límite")
    total_area_fraction: float = Field(description="Fracción dentro del límite total")
    unreachable_fraction: float = Field(description="Fracción sin camino de regreso")
    max_eva_dose_msv: float = Field(
        description="Dosis de fondo de una EVA que usa toda la autonomía planeable"
    )
    synthetic_data: bool
    provenance: dict[str, Provenance] = {
        "return_minutes": Provenance.modeled,
        "planned_limit_min": Provenance.modeled,
        "total_limit_min": Provenance.modeled,
        "planned_area_fraction": Provenance.modeled,
        "total_area_fraction": Provenance.modeled,
        "unreachable_fraction": Provenance.derived,
        "max_eva_dose_msv": Provenance.modeled,
    }
