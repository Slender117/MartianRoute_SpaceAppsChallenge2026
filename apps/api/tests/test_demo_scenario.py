"""El escenario de demo tiene que separar los tres modos.

Corre sobre la salida real de `marsdata synthetic`, no sobre una grilla armada para la prueba: si un
cambio en los pesos o en synthetic.py vuelve iguales las rutas, esta prueba falla.
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
from app.schemas.route import RouteResponse, SuitLimits, WalkMode
from app.storage import RegionGrids, load_manifest, load_region, load_traverse

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "regions"
ROCK_FIELD = 0.5


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
    for a, b in combinations(WalkMode, 2):
        cells_a = {tuple(c) for c in _cells(grids, routes[a])}
        cells_b = {tuple(c) for c in _cells(grids, routes[b])}
        shared = len(cells_a & cells_b) / min(len(cells_a), len(cells_b))
        assert shared < 0.7, f"{a} y {b} comparten {shared:.0%} de la ruta"


def test_modes_have_different_distances(routes):
    for a, b in combinations(WalkMode, 2):
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
    assert science.science_km > safe.science_km
    assert science.stops


def test_all_modes_fit_the_suit_limits(routes):
    for mode, route in routes.items():
        assert route.feasible, f"{mode}: {[a.message for a in route.alerts]}"


def test_demo_region_is_labeled_as_synthetic(grids, routes):
    assert grids.manifest.synthetic
    assert all(route.synthetic_data for route in routes.values())
    assert grids.manifest.layer_meta["dem"].provenance == "modeled"


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
    assert result.synthetic_data
    assert result.points_outside == 0
    assert result.traverse.distance_km > 0
