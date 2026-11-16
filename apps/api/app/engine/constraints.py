"""Alerts for the Marswalk limits."""

import numpy as np

from app.engine.consumables import (
    SOL_HOURS,
    SOLAR_EVENT_MGY,
    usable_autonomy_h,
)
from app.schemas.route import Alert, AlertSeverity, SuitLimits

SLOPE_WARNING_RATIO = 0.8


def _hours(h: float) -> str:
    return f"{h:.1f} h ({h / SOL_HOURS:.2f} sols)"


def check_limits(
    slope_along: np.ndarray,
    elapsed_h: np.ndarray,
    back_h: np.ndarray,
    dist_from_base_km: np.ndarray,
    dose_msv: float,
    suit: SuitLimits,
    solar_event: bool = False,
) -> list[Alert]:
    """Return one alert for each limit that is close or exceeded."""
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
                message=f"Steep segment: {slope_along[i]:.0f}°",
            )
        )

    # The fixed task is done at the destination: it counts for the whole EVA.
    round_trip = elapsed_h + back_h + suit.task_h
    total = float(round_trip[-1])
    usable = usable_autonomy_h(suit.autonomy_h)
    if total > usable:
        over_suit = total > suit.autonomy_h
        limit = suit.autonomy_h if over_suit else usable
        message = (
            f"The round-trip EVA ({_hours(total)}) exceeds the suit autonomy"
            f" ({_hours(suit.autonomy_h)})"
            if over_suit
            else f"The round-trip EVA ({_hours(total)}) uses the reserve"
            f" ({_hours(suit.autonomy_h - usable)}): the plannable limit is {_hours(usable)}"
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
                message=f"More than {suit.max_dist_km:g} km from base",
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
                message=f"Estimated dose of {dose_msv:.2f} mSv, above the"
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
                message=f"Solar event scenario: up to {SOLAR_EVENT_MGY:g} mGy of absorbed"
                " dose (May 2024, the largest measured by RAD up to that date). From the"
                f" destination, the way back to base takes {_hours(float(back_h[-1]))}",
            )
        )

    return alerts
