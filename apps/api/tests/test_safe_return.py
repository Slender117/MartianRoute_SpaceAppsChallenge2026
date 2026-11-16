"""Safe-return map."""

import base64

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.engine.consumables import BASE_SPEED_KMH
from app.engine.safe_return import NO_RETURN, build_safe_return, return_hours, time_per_meter_h
from app.geo import latlon_to_cell
from app.main import create_app
from app.schemas.route import SuitLimits


def _decode(body) -> np.ndarray:
    raw = base64.b64decode(body.return_minutes)
    return np.frombuffer(raw, dtype="<u2").reshape(body.shape)


def test_flat_ground_uses_the_base_speed():
    hours_per_m = time_per_meter_h(np.zeros(1), 25.0)
    assert hours_per_m[0] == pytest.approx(1 / (BASE_SPEED_KMH * 1000))


def test_steep_cells_are_impassable():
    assert np.isinf(time_per_meter_h(np.array([30.0]), 25.0)[0])


def test_return_time_is_zero_at_the_base_and_grows_with_distance(flat_grids):
    m = flat_grids.manifest
    hours = return_hours(flat_grids, m.base, 25.0)
    row, col = latlon_to_cell(m, m.base.lat, m.base.lon)
    assert hours[row, col] == 0
    assert hours[row, col + 10] > hours[row, col + 5] > 0


def test_wall_cells_have_no_return(flat_grids):
    body = build_safe_return(flat_grids, None, SuitLimits())
    minutes = _decode(body)
    assert minutes[0, 30] == NO_RETURN  # the 45° wall is impassable
    assert 0 < body.unreachable_fraction < 1


def test_limits_follow_the_suit(flat_grids):
    body = build_safe_return(flat_grids, None, SuitLimits(autonomy_h=8))
    assert body.planned_limit_min == pytest.approx(8 * 0.8 / 2 * 60)
    assert body.total_limit_min == pytest.approx(8 / 2 * 60)
    assert body.planned_area_fraction <= body.total_area_fraction


def test_fixed_task_time_shrinks_the_reachable_area(flat_grids):
    free = build_safe_return(flat_grids, None, SuitLimits(autonomy_h=8))
    busy = build_safe_return(flat_grids, None, SuitLimits(autonomy_h=8, task_h=2))
    assert busy.planned_limit_min == pytest.approx((8 * 0.8 - 2) / 2 * 60)
    assert busy.planned_area_fraction <= free.planned_area_fraction
    assert busy.max_eva_dose_msv == pytest.approx(free.max_eva_dose_msv)


def test_safe_return_endpoint(assets_dir):
    client = TestClient(create_app())
    r = client.post("/routes/safe-return", json={"region": "test"})
    assert r.status_code == 200
    body = r.json()
    assert body["shape"] == [60, 60]
    assert len(base64.b64decode(body["return_minutes"])) == 60 * 60 * 2
    assert set(body["provenance"]) >= {"return_minutes", "max_eva_dose_msv"}
