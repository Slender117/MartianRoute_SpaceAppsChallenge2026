"""El escenario de demo tiene que separar los tres modos.

Corre sobre la salida de `marsdata synthetic` en data/regions, no sobre una grilla armada para la
prueba: si un cambio en los pesos o en synthetic.py vuelve iguales las rutas, esta prueba falla.

Para correrla sobre Jezero real, apunta DEMO_ASSETS_DIR a la carpeta de `marsdata build` (por
ejemplo `DEMO_ASSETS_DIR=../../data/regions-real pytest tests/test_demo_scenario.py`). Las pruebas
que solo tienen sentido con el terreno armado de la sintética se saltan con datos reales.
"""

import os
from itertools import combinations
from pathlib import Path

import numpy as np
import pytest

from app.config import get_settings
from app.engine.planner import compare_routes
from app.engine.validation import validate_traverse
from app.geo import latlon_to_cell
from app.schemas.route import PLANNING_MODES, LatLon, RouteResponse, SuitLimits, WalkMode
from app.storage import RegionGrids, load_manifest, load_region, load_traverse

# Ruta relativa a apps/api, como ASSETS_DIR en .env.
API_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = (API_DIR / os.getenv("DEMO_ASSETS_DIR", "../../data/regions")).resolve()
ROCK_FIELD = 0.5
# Destino de la etiqueta "Ahorro de O₂ por pendiente" de regions.yaml (análisis de Edgar sobre
# Jezero real): la ruta corta sube pendientes y Segura las rodea gastando menos O₂.
O2_SAVINGS_END = LatLon(lat=18.5223, lon=77.4289)


@pytest.fixture
def grids(monkeypatch) -> RegionGrids:
    if not (DATA_DIR / "jezero" / "manifest.json").exists():
        message = "Falta la región de demo: corre `marsdata synthetic`"
        if os.getenv("CI"):
            pytest.fail(message)
        pytest.skip(message)

    monkeypatch.setenv("ASSETS_DIR", str(DATA_DIR))
    for cached in (get_settings, load_manifest, load_region):
        cached.cache_clear()
    yield load_region("jezero")
    for cached in (get_settings, load_manifest, load_region):
        cached.cache_clear()


@pytest.fixture
def routes(grids) -> dict[WalkMode, RouteResponse]:
    demo = grids.manifest.demo
    assert demo is not None, "regions.yaml debe definir el escenario de demo"
    return compare_routes(grids, demo.start, demo.end, SuitLimits())


def _cells(grids: RegionGrids, route: RouteResponse) -> np.ndarray:
    m = grids.manifest
    return np.array([latlon_to_cell(m, p.lat, p.lon) for p in route.path])


def test_modes_take_different_paths(grids, routes):
    for a, b in combinations(PLANNING_MODES, 2):
        cells_a = {tuple(c) for c in _cells(grids, routes[a])}
        cells_b = {tuple(c) for c in _cells(grids, routes[b])}
        shared = len(cells_a & cells_b) / min(len(cells_a), len(cells_b))
        assert shared < 0.7, f"{a} y {b} comparten {shared:.0%} de la ruta"


def test_modes_have_different_distances(grids, routes):
    # Con datos reales los modos pueden rodear por caminos distintos de largo parecido: ahí manda
    # HE2 (caminos distintos), no la distancia.
    if not grids.manifest.synthetic:
        pytest.skip("Solo la región sintética está armada para separar distancias")
    for a, b in combinations(PLANNING_MODES, 2):
        gap = abs(routes[a].distance_km - routes[b].distance_km) / routes[a].distance_km
        assert gap >= 0.05, f"{a} y {b} difieren solo {gap:.1%} en distancia"


def test_each_mode_does_what_its_name_says(grids, routes):
    def hazard_along(mode: WalkMode) -> np.ndarray:
        c = _cells(grids, routes[mode])
        return grids.hazard[c[:, 0], c[:, 1]]

    fast, safe, science = routes[WalkMode.fast], routes[WalkMode.safe], routes[WalkMode.science]
    assert fast.distance_km < safe.distance_km
    assert hazard_along(WalkMode.fast).max() > ROCK_FIELD
    assert hazard_along(WalkMode.safe).max() < ROCK_FIELD
    # Jezero real no tiene capa de minerales todavía: sin ella no hay ciencia que buscar.
    if "minerals" in grids.manifest.layers:
        assert science.science_km > safe.science_km
        assert science.stops


def test_all_modes_fit_the_suit_limits(routes):
    for mode, route in routes.items():
        assert route.feasible, f"{mode}: {[a.message for a in route.alerts]}"


def test_routes_carry_the_synthetic_label_of_the_region(grids, routes):
    synthetic = grids.manifest.synthetic
    assert all(route.synthetic_data == synthetic for route in routes.values())
    if synthetic:
        assert grids.manifest.layer_meta["dem"].provenance == "modeled"


def test_he2_three_modes_differ_on_real_jezero(grids, routes):
    """HE2: sobre el Jezero real, los tres modos dan rutas distintas.

    Con datos sintéticos se salta: las pruebas de arriba ya cubren la región sintética. Cuando el
    pipeline publique Jezero real (`synthetic: false`), esta prueba corre sola. Si falla, el plan B
    es cambiar los puntos de demo en regions.yaml antes de tocar los pesos.
    """
    if grids.manifest.synthetic:
        pytest.skip("Jezero sigue siendo sintético: HE2 se mide al publicar los datos reales")

    for a, b in combinations(PLANNING_MODES, 2):
        cells_a = {tuple(c) for c in _cells(grids, routes[a])}
        cells_b = {tuple(c) for c in _cells(grids, routes[b])}
        shared = len(cells_a & cells_b) / min(len(cells_a), len(cells_b))
        assert shared < 0.7, f"HE2: {a} y {b} comparten {shared:.0%} de la ruta"


def test_jezero_base_follows_the_coordinate_convention(grids):
    m = grids.manifest
    assert m.base.lat == pytest.approx(18.4447)
    assert m.base.lon == pytest.approx(77.4508)
    row, col = latlon_to_cell(m, m.base.lat, m.base.lon)
    assert 0 <= row < m.shape[0] and 0 <= col < m.shape[1]


def test_rover_traverse_can_be_validated(grids):
    result = validate_traverse(
        grids, "perseverance", load_traverse("jezero", "perseverance"), SuitLimits()
    )
    assert result.synthetic_data == grids.manifest.synthetic
    assert result.points_outside == 0
    assert result.traverse.distance_km > 0


def test_baseline_is_the_shortest_route(routes):
    baseline = routes[WalkMode.baseline]
    for mode in PLANNING_MODES:
        assert baseline.outbound_km <= routes[mode].outbound_km + 1e-9, mode
        assert routes[mode].vs_baseline.distance_km >= -1e-9


def test_safe_saves_o2_on_slopes_on_real_jezero(grids):
    """En el destino de "Ahorro de O₂ por pendiente", Segura gasta menos O₂ y corre menos riesgo
    que la ruta más corta, en las dos cotas del intervalo."""
    if grids.manifest.synthetic:
        pytest.skip("El destino de ahorro de O₂ se eligió sobre Jezero real")

    routes = compare_routes(grids, grids.manifest.base, O2_SAVINGS_END, SuitLimits())
    safe, short = routes[WalkMode.safe], routes[WalkMode.baseline]
    assert safe.o2_interval_kg.low_kg < short.o2_interval_kg.low_kg
    assert safe.o2_interval_kg.high_kg < short.o2_interval_kg.high_kg
    assert safe.cost_breakdown.hazard < short.cost_breakdown.hazard
