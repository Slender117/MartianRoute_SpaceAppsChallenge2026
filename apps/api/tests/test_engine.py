import math

import numpy as np
import pytest

from app.engine.consumables import (
    O2_KG_PER_HOUR,
    RAD_MSV_PER_DAY,
    SOLAR_EVENT_MGY,
    ascent_m,
    point_of_no_return,
    segment_profile,
    usable_autonomy_h,
)
from app.engine.cost import build_cost
from app.engine.pathfind import NoPathError, find_path
from app.engine.planner import compare_routes, plan_route
from app.engine.validation import traverse_to_cells, validate_traverse
from app.geo import cell_size_m
from app.schemas.route import AlertSeverity, LatLon, Provenance, RouteResponse, SuitLimits, WalkMode

MID = 30
NORTH_A = LatLon(lat=0.9, lon=0.1)
NORTH_B = LatLon(lat=0.9, lon=0.3)


def _types(route: RouteResponse) -> set[str]:
    return {a.type for a in route.alerts}


def test_route_goes_around_steep_wall(flat_grids):
    cost = build_cost(flat_grids, WalkMode.safe, max_slope_deg=25)
    path = find_path(cost, (5, 5), (5, 55))

    assert tuple(path[0]) == (5, 5) and tuple(path[-1]) == (5, 55)
    assert not np.any(flat_grids.slope[path[:, 0], path[:, 1]] > 25)
    # Para cruzar el muro tiene que bajar hasta el hueco.
    assert path[:, 0].max() >= 52


def test_unreachable_destination_raises(flat_grids):
    flat_grids.slope[:, MID] = 45.0
    cost = build_cost(flat_grids, WalkMode.safe, max_slope_deg=25)
    with pytest.raises(NoPathError):
        find_path(cost, (5, 5), (5, 55))


def test_same_start_and_end_raises(flat_grids):
    cost = build_cost(flat_grids, WalkMode.safe, max_slope_deg=25)
    with pytest.raises(NoPathError):
        find_path(cost, (5, 5), (5, 5))


def test_science_mode_detours_to_minerals(flat_grids):
    flat_grids.slope[:] = 0
    flat_grids.minerals[36:40, 10:50] = 1.0

    def passes_minerals(mode: WalkMode) -> bool:
        path = find_path(build_cost(flat_grids, mode, 25), (30, 5), (30, 55))
        return bool(flat_grids.minerals[path[:, 0], path[:, 1]].max() > 0)

    assert not passes_minerals(WalkMode.fast)
    assert passes_minerals(WalkMode.science)


def test_plan_route_reports_time_and_limits(flat_grids):
    route = plan_route(
        flat_grids,
        start=NORTH_A,
        end=LatLon(lat=0.9, lon=0.9),
        mode=WalkMode.safe,
        suit=SuitLimits(autonomy_h=0.5, max_slope_deg=25, max_dist_km=1),
    )

    assert route.distance_km > 0
    assert route.duration_h > 0
    assert route.path[0].t_h == 0
    assert route.point_of_no_return is not None
    assert _types(route) >= {"autonomy", "distance"}
    assert not route.feasible


def test_eva_counts_the_way_back(flat_grids):
    route = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, SuitLimits())

    assert route.distance_km == pytest.approx(2 * route.outbound_km)
    assert route.duration_h == pytest.approx(route.outbound_h + route.return_h)
    # En terreno plano la vuelta tarda lo mismo que la ida.
    assert route.return_h == pytest.approx(route.outbound_h)
    assert route.path[-1].t_h == pytest.approx(route.outbound_h)


def test_way_back_uphill_takes_longer(flat_grids):
    flat_grids.dem[:] = np.linspace(100, 0, flat_grids.dem.shape[1], dtype=np.float32)
    route = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, SuitLimits())

    assert route.return_h > route.outbound_h


def test_start_defaults_to_region_base(flat_grids):
    base = flat_grids.manifest.base
    route = plan_route(flat_grids, None, NORTH_A, WalkMode.safe, SuitLimits())

    assert route.path[0].lat == pytest.approx(base.lat, abs=0.01)
    assert route.path[0].lon == pytest.approx(base.lon, abs=0.01)


def _eva_hours(flat_grids) -> float:
    return plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, SuitLimits()).duration_h


def test_reserve_is_not_plannable(flat_grids):
    duration = _eva_hours(flat_grids)
    # Le alcanza al traje, pero solo gastando parte de la reserva.
    suit = SuitLimits(autonomy_h=duration / 0.9)
    route = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, suit)

    assert route.usable_autonomy_h == pytest.approx(usable_autonomy_h(suit.autonomy_h))
    assert route.margin_h < 0
    assert not route.feasible
    alert = next(a for a in route.alerts if a.type == "autonomy")
    assert alert.severity == AlertSeverity.critical
    assert "reserva" in alert.message


def test_eva_within_usable_autonomy_is_feasible(flat_grids):
    # La hora extra cubre la reserva aunque mande la de 30 min.
    suit = SuitLimits(autonomy_h=_eva_hours(flat_grids) / 0.7 + 1, max_dist_km=100)
    route = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, suit)

    assert route.margin_h > 0
    assert route.feasible
    assert route.point_of_no_return is None
    assert route.alerts == []


def test_point_of_no_return_on_flat_ground_is_half_of_the_budget():
    elapsed = np.linspace(0, 10, 101)
    assert point_of_no_return(elapsed, elapsed, budget_h=6.4) == 32


def test_point_of_no_return_comes_earlier_if_the_way_back_is_slower():
    elapsed = np.linspace(0, 10, 101)
    assert point_of_no_return(elapsed, 2 * elapsed, budget_h=6.4) == 22


def test_usable_autonomy_applies_the_stricter_reserve():
    # Con 8 h manda el 20 % (1.6 h); con 2 h manda la reserva mínima de 30 min.
    assert usable_autonomy_h(8.0) == pytest.approx(8.0 * 0.8)
    assert usable_autonomy_h(2.0) == pytest.approx(2.0 - 0.5)


def _autonomy_for_usable(usable_h: float) -> float:
    """Autonomía del traje cuya parte planeable es `usable_h` (inversa de usable_autonomy_h)."""
    by_percent = usable_h / 0.8
    return by_percent if 0.2 * by_percent >= 0.5 else usable_h + 0.5


def test_route_reports_the_point_of_no_return_at_the_planned_limit(flat_grids):
    duration = _eva_hours(flat_grids)
    # Autonomía planeable apenas menor que la EVA completa: el punto de no retorno cae en el
    # destino. El 1e-6 evita depender del redondeo de punto flotante en la igualdad.
    suit = SuitLimits(autonomy_h=_autonomy_for_usable(duration - 1e-6), max_dist_km=100)
    route = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, suit)

    assert route.point_of_no_return == len(route.path) - 1
    assert route.point_of_no_return_km == pytest.approx(route.outbound_km)


def test_fixed_task_time_adds_duration_and_o2(flat_grids):
    walk = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, SuitLimits())
    task = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, SuitLimits(task_h=1.0))

    assert task.duration_h == pytest.approx(walk.duration_h + 1.0)
    assert task.o2_interval_kg.low_kg == pytest.approx(walk.o2_interval_kg.low_kg + O2_KG_PER_HOUR)
    assert task.o2_interval_kg.high_kg == pytest.approx(
        walk.o2_interval_kg.high_kg + O2_KG_PER_HOUR
    )


def test_fixed_task_time_brings_the_point_of_no_return_earlier(flat_grids):
    duration = _eva_hours(flat_grids)
    usable = duration + 1.0
    no_task = SuitLimits(autonomy_h=_autonomy_for_usable(usable), max_dist_km=100)
    with_task = no_task.model_copy(update={"task_h": 1.5})

    assert (
        plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, no_task).point_of_no_return is None
    )
    route = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, with_task)
    assert route.point_of_no_return is not None
    assert not route.feasible


def test_radiation_dose_follows_duration(flat_grids):
    route = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, SuitLimits())

    assert route.radiation_msv == pytest.approx(route.duration_h / 24 * RAD_MSV_PER_DAY)
    assert route.solar_event_mgy is None
    assert "radiation" not in _types(route)


def test_dose_limit_is_checked_only_when_requested(flat_grids):
    dose = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, SuitLimits()).radiation_msv

    suit = SuitLimits(max_dose_msv=dose / 2, max_dist_km=100)
    route = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, suit)
    assert "radiation" in _types(route)
    assert not route.feasible


def test_solar_event_scenario_warns_with_time_back_to_base(flat_grids):
    suit = SuitLimits(max_dist_km=100)
    route = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, suit, solar_event=True)

    assert route.solar_event_mgy == SOLAR_EVENT_MGY
    alert = next(a for a in route.alerts if a.type == "radiation")
    assert alert.severity == AlertSeverity.warning
    assert f"{route.return_h:.1f} h" in alert.message
    # Sigue viable: un escenario no es un límite roto, y los mGy no se suman a los mSv.
    assert route.feasible
    baseline = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, suit)
    assert route.radiation_msv == baseline.radiation_msv


def test_consumables_cover_the_pair(flat_grids):
    route = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, SuitLimits())

    assert route.o2_estimate_kg == pytest.approx(route.duration_h * O2_KG_PER_HOUR)
    assert route.o2_crew_kg == pytest.approx(2 * route.o2_estimate_kg)


def test_every_figure_has_a_provenance_label(flat_grids):
    route = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, SuitLimits())

    numeric = {
        name
        for name, value in route.model_dump(mode="python").items()
        if isinstance(value, float | int) and not isinstance(value, bool)
    }
    assert numeric <= set(route.provenance)
    assert {"elev", "cost_breakdown", "solar_event_mgy"} <= set(route.provenance)
    assert set(route.provenance.values()) <= set(Provenance)


def test_compare_reports_difference_against_safe(flat_grids):
    flat_grids.slope[:] = 0
    flat_grids.minerals[:15, :] = 1.0
    routes = compare_routes(flat_grids, NORTH_A, NORTH_B, SuitLimits())

    safe, science = routes[WalkMode.safe], routes[WalkMode.science]
    assert safe.vs_safe is None
    delta = science.vs_safe
    assert delta.distance_km == pytest.approx(science.distance_km - safe.distance_km)
    assert delta.duration_h == pytest.approx(science.duration_h - safe.duration_h)
    assert delta.science_km == pytest.approx(science.science_km - safe.science_km)
    assert 0 <= delta.shared_path <= 1


def test_east_west_distance_shrinks_with_latitude(flat_grids):
    m = flat_grids.manifest.model_copy(update={"bbox": (0.0, 59.5, 1.0, 60.5)})
    dy, dx = cell_size_m(m)
    assert dy == 50.0
    assert dx == pytest.approx(25.0, abs=0.1)

    east = np.array([[10, 10], [10, 11]])
    north = np.array([[10, 10], [11, 10]])
    dist_east, _ = segment_profile(east, flat_grids.dem, (dy, dx))
    dist_north, _ = segment_profile(north, flat_grids.dem, (dy, dx))
    assert dist_east[0] == pytest.approx(dist_north[0] / 2, rel=0.01)
    assert math.isclose(cell_size_m(flat_grids.manifest)[1], 50.0, rel_tol=0.01)


def test_ascent_only_counts_going_up(flat_grids):
    flat_grids.dem[0, :4] = [0, 10, 5, 20]
    assert ascent_m(np.array([[0, 0], [0, 1], [0, 2], [0, 3]]), flat_grids.dem) == 25


def test_traverse_cells_are_continuous_and_drop_points_outside(flat_grids):
    coords = np.array([[0.1, 0.9], [0.5, 0.9], [5.0, 0.9]])
    cells, outside = traverse_to_cells(flat_grids.manifest, coords)

    assert outside == 1
    steps = np.abs(np.diff(cells, axis=0))
    assert steps.max() <= 1


def test_validation_against_a_route_identical_to_the_rover(flat_grids):
    flat_grids.slope[:] = 0
    geojson = {"geometry": {"coordinates": [[0.1, 0.9, -2500], [0.9, 0.9, -2500]]}}
    result = validate_traverse(flat_grids, "rover", geojson, SuitLimits())

    for metrics in result.routes.values():
        assert metrics.distance_ratio == pytest.approx(1.0, abs=0.01)
        assert metrics.mean_separation_m == pytest.approx(0, abs=1)


def test_validation_measures_how_far_the_route_strays(flat_grids):
    # El rover cruza el muro; las rutas no pueden y se separan para buscar el hueco.
    geojson = {"geometry": {"coordinates": [[0.3, 0.9], [0.7, 0.9]]}}
    result = validate_traverse(flat_grids, "rover", geojson, SuitLimits())

    for metrics in result.routes.values():
        assert metrics.distance_ratio > 1.5
        assert metrics.mean_separation_m > 100
        assert metrics.max_separation_m >= metrics.mean_separation_m


def test_baseline_ignores_hazard_and_takes_the_shortest_way(flat_grids):
    flat_grids.slope[:] = 0
    flat_grids.hazard[2:11, 9:15] = 1.0  # un campo de rocas justo entre los dos puntos
    safe = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, SuitLimits())
    baseline = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.baseline, SuitLimits())

    assert baseline.outbound_km < safe.outbound_km


def test_baseline_still_respects_the_max_slope(flat_grids):
    route = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.baseline, SuitLimits())
    cols = {round(p.lon * (len(flat_grids.dem) - 1)) for p in route.path if p.lat > 0.2}
    assert MID not in cols  # rodea el muro por abajo


def test_compare_reports_difference_against_baseline(flat_grids):
    routes = compare_routes(flat_grids, NORTH_A, NORTH_B, SuitLimits())

    baseline, safe = routes[WalkMode.baseline], routes[WalkMode.safe]
    assert baseline.vs_baseline is None
    assert baseline.vs_safe is not None
    delta = safe.vs_baseline
    assert delta.distance_km == pytest.approx(safe.distance_km - baseline.distance_km)
    assert delta.o2_interval_kg.high_kg == pytest.approx(
        safe.o2_interval_kg.high_kg - baseline.o2_interval_kg.high_kg
    )


def test_route_reports_an_ordered_o2_interval(flat_grids):
    route = plan_route(flat_grids, NORTH_A, NORTH_B, WalkMode.safe, SuitLimits())
    assert 0 < route.o2_interval_kg.low_kg <= route.o2_interval_kg.high_kg
