"""Catálogo de parámetros del modelo, con su fuente, para el panel "Supuestos y límites".

Lee las constantes del motor: no hay una segunda copia de ningún valor. docs/supuestos.md trae las
referencias completas. El marcador [__] señala un valor que sigue sin fuente abierta confirmada.
"""

from app.engine.constraints import SLOPE_WARNING_RATIO
from app.engine.consumables import (
    AUTONOMY_RESERVE,
    BASE_SPEED_KMH,
    CREW_SIZE,
    O2_KG_PER_HOUR,
    RAD_MSV_PER_DAY,
    RAD_MSV_PER_DAY_ERROR,
    SOL_HOURS,
    SOLAR_EVENT_MGY,
)
from app.engine.cost import MIN_CELL_COST, MODE_WEIGHTS
from app.engine.science import ICE_THRESHOLD, MIN_GAP, SCIENCE_THRESHOLD
from app.geo import MARS_RADIUS_M
from app.schemas.assumptions import Assumption, AssumptionsResponse
from app.schemas.route import Provenance, SuitLimits, WalkMode

PENDING_SOURCE = "[__]"
PROJECT_DECISION = "Decisión del proyecto"

LIMITS = [
    "Mientras una región tenga datos sintéticos, sus cifras no describen el terreno real de Marte.",
    "La duración de la EVA solo cuenta la caminata: no incluye el trabajo en las paradas.",
    "El regreso se calcula por el mismo camino de la ida.",
    "La tasa de radiación se midió en Gale con Curiosity, no en Jezero, y varía con el ciclo solar"
    " y con la presión atmosférica.",
    "La dosis del evento solar es absorbida (mGy) y no se suma a la dosis equivalente (mSv): falta"
    " el factor de calidad de ese evento. Un evento futuro podría ser mayor.",
    "Las distancias siguen una grilla de 8 vecinos, que las sobrestima hasta cerca de 8 %.",
    "La pendiente del pipeline asume celdas cuadradas: lejos del ecuador pierde precisión.",
    "No hay alertas de clima todavía: la API no recibe la hora de salida.",
]


def _suit_default(field: str) -> float | None:
    return SuitLimits.model_fields[field].default


def _weights(mode: WalkMode) -> str:
    w = MODE_WEIGHTS[mode]
    return (
        f"pendiente {w['slope']:g}, riesgo {w['hazard']:g},"
        f" inestabilidad {w['instability']:g}, ciencia {w['science']:g}"
    )


def build_assumptions() -> AssumptionsResponse:
    modeled, observed = Provenance.modeled, Provenance.observed
    parameters = [
        Assumption(
            id="base_speed",
            label="Velocidad con traje en terreno plano",
            value=BASE_SPEED_KMH,
            unit="km/h",
            provenance=modeled,
            source=PENDING_SOURCE,
        ),
        Assumption(
            id="tobler_coefficient",
            label="Coeficiente de la función de Tobler",
            value=3.5,
            provenance=modeled,
            source="Tobler (1993)",
            note="Función para personas a pie en la Tierra, escalada a la velocidad con traje.",
        ),
        Assumption(
            id="o2_rate",
            label="Consumo de O₂ por persona",
            value=O2_KG_PER_HOUR,
            unit="kg/h",
            provenance=modeled,
            source=PENDING_SOURCE,
        ),
        Assumption(
            id="crew_size",
            label="Integrantes de la EVA",
            value=CREW_SIZE,
            unit="personas",
            provenance=modeled,
            source=PROJECT_DECISION,
        ),
        Assumption(
            id="autonomy",
            label="Autonomía del traje",
            value=_suit_default("autonomy_h"),
            unit="h",
            provenance=modeled,
            source=PENDING_SOURCE,
        ),
        Assumption(
            id="autonomy_reserve",
            label="Reserva de autonomía",
            value=AUTONOMY_RESERVE,
            unit="fracción",
            provenance=modeled,
            source=PROJECT_DECISION,
        ),
        Assumption(
            id="max_slope",
            label="Pendiente máxima caminable",
            value=_suit_default("max_slope_deg"),
            unit="°",
            provenance=modeled,
            source=PENDING_SOURCE,
        ),
        Assumption(
            id="max_distance",
            label="Distancia máxima a la base",
            value=_suit_default("max_dist_km"),
            unit="km",
            provenance=modeled,
            source=PENDING_SOURCE,
        ),
        Assumption(
            id="max_dose",
            label="Límite de dosis por EVA",
            value=None,
            unit="mSv",
            provenance=modeled,
            source=PENDING_SOURCE,
            note="Sin valor por defecto: la dosis solo genera alerta si se pide un límite.",
        ),
        Assumption(
            id="radiation_rate",
            label="Dosis equivalente en la superficie",
            value=RAD_MSV_PER_DAY,
            unit="mSv/día",
            provenance=observed,
            source="Hassler et al. (2014)",
            note=f"Curiosity RAD, Gale, con incertidumbre de ±{RAD_MSV_PER_DAY_ERROR} mSv/día.",
        ),
        Assumption(
            id="solar_event_dose",
            label="Dosis absorbida del escenario de evento solar",
            value=SOLAR_EVENT_MGY,
            unit="mGy",
            provenance=observed,
            source="NASA JPL (2024)",
            note="Curiosity RAD, 20 de mayo de 2024. Se aplica completa como peor caso.",
        ),
        Assumption(
            id="sol_length",
            label="Duración de un sol",
            value=SOL_HOURS,
            unit="h",
            provenance=observed,
            source="NASA GISS Mars24",
        ),
        Assumption(
            id="mars_radius",
            label="Radio de Marte",
            value=MARS_RADIUS_M / 1000,
            unit="km",
            provenance=observed,
            source="Convención del proyecto (radio medio)",
        ),
        Assumption(
            id="slope_warning",
            label="Aviso de tramo empinado",
            value=SLOPE_WARNING_RATIO,
            unit="fracción de la pendiente máxima",
            provenance=modeled,
            source=PROJECT_DECISION,
        ),
        Assumption(
            id="science_threshold",
            label="Umbral de parada por minerales",
            value=SCIENCE_THRESHOLD,
            unit="índice 0-1",
            provenance=modeled,
            source=PROJECT_DECISION,
        ),
        Assumption(
            id="ice_threshold",
            label="Umbral de parada por hielo",
            value=ICE_THRESHOLD,
            unit="índice 0-1",
            provenance=modeled,
            source=PROJECT_DECISION,
        ),
        Assumption(
            id="stop_gap",
            label="Separación mínima entre paradas",
            value=MIN_GAP,
            unit="puntos de la ruta",
            provenance=modeled,
            source=PROJECT_DECISION,
        ),
        Assumption(
            id="min_cell_cost",
            label="Costo mínimo por celda",
            value=MIN_CELL_COST,
            provenance=modeled,
            source=PROJECT_DECISION,
        ),
    ]
    parameters += [
        Assumption(
            id=f"weights_{mode}",
            label=f"Pesos del modo {label}",
            value=_weights(mode),
            provenance=modeled,
            source=PROJECT_DECISION,
        )
        for mode, label in (
            (WalkMode.safe, "Segura"),
            (WalkMode.fast, "Rápida"),
            (WalkMode.science, "Científica"),
        )
    ]
    return AssumptionsResponse(parameters=parameters, limits=LIMITS)
