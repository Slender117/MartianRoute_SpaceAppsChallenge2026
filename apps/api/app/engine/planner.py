"""Orquesta el cálculo de una EVA: costo → A* → tiempos de ida y vuelta → paradas → alertas."""

import numpy as np

from app.engine.constraints import check_limits
from app.engine.consumables import (
    CREW_SIZE,
    O2_KG_PER_HOUR,
    SOL_HOURS,
    SOLAR_EVENT_MGY,
    point_of_no_return,
    radiation_dose_msv,
    segment_profile,
    usable_autonomy_h,
)
from app.engine.cost import build_cost, cost_breakdown
from app.engine.o2_model import o2_interval_kg
from app.engine.pathfind import find_path
from app.engine.science import SCIENCE_THRESHOLD, find_stops
from app.geo import cell_size_m, cell_to_latlon, haversine_km, latlon_to_cell
from app.schemas.route import (
    AlertSeverity,
    CostBreakdown,
    LatLon,
    O2Interval,
    PathPoint,
    Provenance,
    RouteDelta,
    RouteResponse,
    Stop,
    SuitLimits,
    WalkMode,
)
from app.storage import RegionGrids

ROUTE_PROVENANCE: dict[str, Provenance] = {
    "distance_km": Provenance.derived,
    "outbound_km": Provenance.derived,
    "science_km": Provenance.derived,
    "cost_breakdown": Provenance.derived,
    "duration_h": Provenance.modeled,
    "duration_sols": Provenance.modeled,
    "outbound_h": Provenance.modeled,
    "return_h": Provenance.modeled,
    "usable_autonomy_h": Provenance.modeled,
    "margin_h": Provenance.modeled,
    "point_of_no_return": Provenance.modeled,
    "point_of_no_return_km": Provenance.modeled,
    "o2_estimate_kg": Provenance.modeled,
    "o2_crew_kg": Provenance.modeled,
    "o2_interval_kg": Provenance.modeled,
    # La tasa se midió en Gale; aplicarla a otra EVA ya es un modelo.
    "radiation_msv": Provenance.modeled,
    "solar_event_mgy": Provenance.observed,
}


def plan_route(
    grids: RegionGrids,
    start: LatLon | None,
    end: LatLon,
    mode: WalkMode,
    suit: SuitLimits,
    solar_event: bool = False,
) -> RouteResponse:
    m = grids.manifest
    node = start or m.base
    cell_m = cell_size_m(m)
    cost = build_cost(grids, mode, suit.max_slope_deg)
    path = find_path(
        cost,
        latlon_to_cell(m, node.lat, node.lon),
        latlon_to_cell(m, end.lat, end.lon),
        sampling=cell_m,
    )

    dist_m, hours = segment_profile(path, grids.dem, cell_m)
    _, back_hours = segment_profile(path[::-1], grids.dem, cell_m)
    elapsed = np.concatenate([[0.0], np.cumsum(hours)])
    # back[i] = tiempo de regresar desde el punto i hasta la base, por el mismo camino.
    back = np.concatenate([[0.0], np.cumsum(back_hours[::-1])])

    coords = np.array([cell_to_latlon(m, int(r), int(c)) for r, c in path])
    elev = grids.dem[path[:, 0], path[:, 1]]
    points = [
        PathPoint(lat=float(lat), lon=float(lon), elev=float(z), t_h=float(t))
        for (lat, lon), z, t in zip(coords, elev, elapsed, strict=True)
    ]

    stops = [
        Stop(lat=points[i].lat, lon=points[i].lon, type=kind, reason=reason)
        for i, kind, reason in find_stops(grids, path)
    ]

    outbound_h, return_h = float(elapsed[-1]), float(back[-1])
    outbound_km = float(dist_m.sum() / 1000)
    duration_h = outbound_h + return_h + suit.task_h
    usable_h = usable_autonomy_h(suit.autonomy_h)
    dose_msv = radiation_dose_msv(duration_h)
    from_base = haversine_km(node, coords[:, 0], coords[:, 1])
    alerts = check_limits(
        grids.slope[path[:, 0], path[:, 1]], elapsed, back, from_base, dose_msv, suit, solar_event
    )
    interesting = grids.minerals[path[1:, 0], path[1:, 1]] >= SCIENCE_THRESHOLD
    o2_kg = duration_h * O2_KG_PER_HOUR
    # Caminata según la pendiente (Minetti) más el trabajo fijo a la tasa por hora.
    o2_task = suit.task_h * O2_KG_PER_HOUR
    o2_low, o2_high = (o2 + o2_task for o2 in o2_interval_kg(path, grids.dem, cell_m))
    pnr = point_of_no_return(elapsed, back, usable_h - suit.task_h)

    dem_meta = m.layer_meta.get("dem")
    return RouteResponse(
        mode=mode,
        path=points,
        distance_km=2 * outbound_km,
        duration_h=duration_h,
        duration_sols=duration_h / SOL_HOURS,
        outbound_km=outbound_km,
        outbound_h=outbound_h,
        return_h=return_h,
        usable_autonomy_h=usable_h,
        margin_h=usable_h - duration_h,
        o2_estimate_kg=o2_kg,
        o2_crew_kg=o2_kg * CREW_SIZE,
        o2_interval_kg=O2Interval(low_kg=o2_low, high_kg=o2_high),
        radiation_msv=dose_msv,
        solar_event_mgy=SOLAR_EVENT_MGY if solar_event else None,
        science_km=float(dist_m[interesting].sum() / 1000),
        point_of_no_return=pnr,
        point_of_no_return_km=None if pnr is None else float(dist_m[:pnr].sum() / 1000),
        stops=stops,
        alerts=alerts,
        feasible=all(a.severity != AlertSeverity.critical for a in alerts),
        cost_breakdown=CostBreakdown(**cost_breakdown(grids, path)),
        synthetic_data=m.synthetic,
        provenance={
            **ROUTE_PROVENANCE,
            "elev": dem_meta.provenance if dem_meta else Provenance.derived,
        },
    )


def route_delta(route: RouteResponse, ref: RouteResponse) -> RouteDelta:
    """Diferencia de `route` menos `ref`, con la fracción de camino que comparten."""
    ref_points = {(p.lat, p.lon) for p in ref.path}
    shared = sum((p.lat, p.lon) in ref_points for p in route.path)
    return RouteDelta(
        distance_km=route.distance_km - ref.distance_km,
        duration_h=route.duration_h - ref.duration_h,
        duration_sols=route.duration_sols - ref.duration_sols,
        o2_estimate_kg=route.o2_estimate_kg - ref.o2_estimate_kg,
        o2_interval_kg=O2Interval(
            low_kg=route.o2_interval_kg.low_kg - ref.o2_interval_kg.low_kg,
            high_kg=route.o2_interval_kg.high_kg - ref.o2_interval_kg.high_kg,
        ),
        radiation_msv=route.radiation_msv - ref.radiation_msv,
        science_km=route.science_km - ref.science_km,
        shared_path=shared / len(route.path),
    )


def compare_routes(
    grids: RegionGrids,
    start: LatLon | None,
    end: LatLon,
    suit: SuitLimits,
    solar_event: bool = False,
) -> dict[WalkMode, RouteResponse]:
    """Los tres modos y la línea base, cada uno con su diferencia contra la Segura y la base."""
    routes = {mode: plan_route(grids, start, end, mode, suit, solar_event) for mode in WalkMode}

    safe, baseline = routes[WalkMode.safe], routes[WalkMode.baseline]
    for mode, route in routes.items():
        if mode != WalkMode.safe:
            route.vs_safe = route_delta(route, safe)
        if mode != WalkMode.baseline:
            route.vs_baseline = route_delta(route, baseline)
    return routes
