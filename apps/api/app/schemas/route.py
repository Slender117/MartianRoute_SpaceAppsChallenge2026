from enum import StrEnum

from pydantic import BaseModel, Field


class Provenance(StrEnum):
    """Where a layer or a figure comes from."""

    observed = "observed"  # direct measurement by an instrument
    derived = "derived"  # computed from measured data
    modeled = "modeled"  # comes from a model or an assumption


class LatLon(BaseModel):
    """Planetocentric, east longitude, -180 to 180 across the app."""

    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class WalkMode(StrEnum):
    safe = "safe"
    fast = "fast"
    science = "science"
    baseline = "baseline"  # minimum distance: the reference the modes are measured against


# The modes the astronaut picks. The baseline is not one: it is only for comparison.
PLANNING_MODES = (WalkMode.safe, WalkMode.fast, WalkMode.science)


class SuitLimits(BaseModel):
    autonomy_h: float = Field(8.0, gt=0, description="Suit autonomy in hours")
    max_slope_deg: float = Field(20.0, gt=0, le=60, description="Maximum walkable slope")
    max_dist_km: float = Field(10.0, gt=0, description="Maximum distance to base")
    task_h: float = Field(
        0.0,
        ge=0,
        description="Hours of fixed EVA work without walking (stops, sampling); added"
        " at the destination. No sourced default: 0 until the team sets it",
    )
    max_dose_msv: float | None = Field(
        None,
        gt=0,
        description="Per-EVA dose limit in mSv; without a value, the dose is only reported",
    )


class CompareRequest(BaseModel):
    region: str
    start: LatLon | None = Field(
        None, description="EVA base node; if missing, the region's base is used"
    )
    end: LatLon
    suit: SuitLimits = SuitLimits()
    solar_event: bool = Field(False, description="Scenario: solar event during the EVA")


class RouteRequest(CompareRequest):
    mode: WalkMode = WalkMode.safe


class PathPoint(LatLon):
    elev: float
    t_h: float = Field(description="Elapsed time on the way out when reaching this point, in hours")


class Stop(LatLon):
    type: str  # "science" | "ice"
    reason: str
    value: float = Field(description="Mineral or ice index at the stop (0-1)")


class AlertSeverity(StrEnum):
    warning = "warning"  # worth checking, but the EVA stays within the limits
    critical = "critical"  # breaks a limit: the EVA is not viable as planned


class Alert(BaseModel):
    at: int = Field(description="Index of the outbound route point where it applies")
    type: str  # "slope" | "autonomy" | "distance" | "radiation" | "climate"
    severity: AlertSeverity = AlertSeverity.warning
    message: str = Field(description="Text in English; the web builds other languages from code")
    code: str = Field(
        description="Alert variant: steep_segment, autonomy_over_suit, autonomy_reserve,"
        " too_far, dose_over_limit o solar_event"
    )
    values: dict[str, float] = Field(
        default_factory=dict, description="Figures in the message, to translate it without the API"
    )


class CostBreakdown(BaseModel):
    slope: float
    hazard: float
    instability: float
    science_bonus: float


class O2Interval(BaseModel):
    """O₂ per astronaut between the two gravity bounds of the Minetti model.

    There is no central value: the source for how flat-ground cost changes with gravity is missing.
    """

    low_kg: float = Field(description="Low bound: flat-ground cost does not change with gravity")
    high_kg: float = Field(description="High bound: flat-ground cost scales with gravity")


class RouteDelta(BaseModel):
    """Difference of a route against a reference (this route minus the reference)."""

    distance_km: float
    duration_h: float
    duration_sols: float
    o2_estimate_kg: float
    o2_interval_kg: O2Interval = Field(description="Difference at each bound of the O₂ interval")
    radiation_msv: float
    science_km: float
    shared_path: float = Field(description="Fraction of this route shared with the safe one (0-1)")


class RouteResponse(BaseModel):
    mode: WalkMode
    path: list[PathPoint] = Field(description="Outbound route; the return uses the same path")
    distance_km: float = Field(description="Distance of the whole EVA, out and back")
    duration_h: float = Field(description="Duration of the whole EVA, out and back")
    duration_sols: float
    outbound_km: float
    outbound_h: float
    return_h: float
    usable_autonomy_h: float = Field(description="Suit autonomy minus the reserve")
    margin_h: float = Field(
        description="Usable autonomy minus duration; negative if it is not enough"
    )
    o2_estimate_kg: float = Field(
        description="Reference: O₂ by time (duration × rate), without the slope effect. The"
        " official figure is o2_interval_kg; this one is not shown in the interface"
    )
    o2_crew_kg: float = Field(description="EVA O₂ for the whole pair")
    o2_interval_kg: O2Interval = Field(
        description="Official EVA O₂ per astronaut: walking by the slope of"
        " each segment (Minetti) plus the fixed task at the hourly rate"
    )
    radiation_msv: float = Field(description="Background dose equivalent during the EVA")
    solar_event_mgy: float | None = Field(
        description="Absorbed dose of the solar event scenario; not added to radiation_msv"
    )
    science_km: float = Field(description="Outbound kilometers over terrain of scientific interest")
    point_of_no_return: int | None = Field(
        description="Index of the first outbound point from which the walk back no longer fits"
        " the plannable autonomy (the autonomy minus the stricter reserve)"
    )
    point_of_no_return_km: float | None = Field(
        description="Outbound kilometers up to the point of no return"
    )
    stops: list[Stop]
    alerts: list[Alert]
    feasible: bool = Field(description="False if a critical alert breaks a limit")
    cost_breakdown: CostBreakdown
    vs_safe: RouteDelta | None = Field(None, description="Difference against the Safe route")
    vs_baseline: RouteDelta | None = Field(
        None, description="Difference against the minimum-distance baseline"
    )
    synthetic_data: bool = Field(description="True if the region uses test data")
    provenance: dict[str, Provenance] = Field(description="Label of each figure in the response")
