"""Alertas por límites de la Marswalk."""

import numpy as np

from app.engine.consumables import (
    SOL_HOURS,
    SOLAR_EVENT_MGY,
    usable_autonomy_h,
)
from app.schemas.route import Alert, AlertSeverity, SuitLimits

SLOPE_WARNING_RATIO = 0.8


def _hours(h: float) -> str:
    return f"{h:.1f} h ({h / SOL_HOURS:.2f} soles)"


def check_limits(
    slope_along: np.ndarray,
    elapsed_h: np.ndarray,
    back_h: np.ndarray,
    dist_from_base_km: np.ndarray,
    dose_msv: float,
    suit: SuitLimits,
    solar_event: bool = False,
) -> list[Alert]:
    """Devuelve una alerta por cada límite cercano o superado."""
    alerts: list[Alert] = []

    steep = np.nonzero(slope_along >= SLOPE_WARNING_RATIO * suit.max_slope_deg)[0]
    if steep.size:
        i = int(steep[0])
        alerts.append(
            Alert(
                at=i,
                type="slope",
                code="steep_segment",
                values={"slope_deg": round(float(slope_along[i]))},
                message=f"Tramo empinado: {slope_along[i]:.0f}°",
            )
        )

    # El trabajo fijo se hace en el destino: cuenta para la EVA completa.
    round_trip = elapsed_h + back_h + suit.task_h
    total = float(round_trip[-1])
    usable = usable_autonomy_h(suit.autonomy_h)
    if total > usable:
        over_suit = total > suit.autonomy_h
        limit = suit.autonomy_h if over_suit else usable
        message = (
            f"La EVA de ida y vuelta ({_hours(total)}) supera la autonomía del traje"
            f" ({_hours(suit.autonomy_h)})"
            if over_suit
            else f"La EVA de ida y vuelta ({_hours(total)}) consume la reserva"
            f" ({_hours(suit.autonomy_h - usable)}): el límite planeable es {_hours(usable)}"
        )
        alerts.append(
            Alert(
                at=int(np.nonzero(round_trip > limit)[0][0]),
                type="autonomy",
                severity=AlertSeverity.critical,
                code="autonomy_over_suit" if over_suit else "autonomy_reserve",
                values={
                    "total_h": total,
                    "autonomy_h": suit.autonomy_h,
                    "reserve_h": suit.autonomy_h - usable,
                    "usable_h": usable,
                },
                message=message,
            )
        )

    too_far = np.nonzero(dist_from_base_km > suit.max_dist_km)[0]
    if too_far.size:
        alerts.append(
            Alert(
                at=int(too_far[0]),
                type="distance",
                severity=AlertSeverity.critical,
                code="too_far",
                values={"max_dist_km": suit.max_dist_km},
                message=f"Más de {suit.max_dist_km:g} km de la base",
            )
        )

    if suit.max_dose_msv is not None and dose_msv > suit.max_dose_msv:
        alerts.append(
            Alert(
                at=len(elapsed_h) - 1,
                type="radiation",
                severity=AlertSeverity.critical,
                code="dose_over_limit",
                values={"dose_msv": dose_msv, "limit_msv": suit.max_dose_msv},
                message=f"Dosis estimada de {dose_msv:.2f} mSv, sobre el límite de"
                f" {suit.max_dose_msv:g} mSv",
            )
        )

    if solar_event:
        alerts.append(
            Alert(
                at=len(elapsed_h) - 1,
                type="radiation",
                code="solar_event",
                values={"dose_mgy": SOLAR_EVENT_MGY, "return_h": float(back_h[-1])},
                message=f"Escenario de evento solar: hasta {SOLAR_EVENT_MGY:g} mGy de dosis"
                " absorbida (mayo de 2024, el mayor medido por RAD hasta esa fecha). Desde el"
                f" destino, el regreso a la base toma {_hours(float(back_h[-1]))}",
            )
        )

    return alerts
