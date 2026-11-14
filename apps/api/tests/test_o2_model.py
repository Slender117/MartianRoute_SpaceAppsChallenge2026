"""Modelo de O₂ por pendiente (Minetti) dentro del motor."""

import numpy as np
import pytest

from app.engine.o2_model import (
    G_MARS_MS2,
    O2_FLAT_KG_PER_M,
    o2_interval_kg,
    o2_multiplier,
    slope_penalty,
)

CELL = (10.0, 10.0)
STRAIGHT = np.array([[0, c] for c in range(11)])  # 10 pasos de 10 m: 100 m


def test_curve_reproduces_minetti_knots():
    grades = np.array([-0.45, -0.10, 0.0, 0.45])
    expected = np.array([3.46, 0.81, 1.64, 17.33]) / 1.64
    assert o2_multiplier(grades) == pytest.approx(expected)


def test_slope_penalty_is_zero_on_flat_and_one_at_the_limit():
    pen = slope_penalty(np.array([0.0, 12.5, 25.0, 40.0]), 25.0)
    assert pen[0] == pytest.approx(0.0)
    assert pen[2] == pytest.approx(1.0)
    assert pen[3] == pytest.approx(1.0)  # se satura más allá de la máxima
    assert 0 < pen[1] < 1


def test_o2_interval_on_flat_ground_is_exact_and_closed():
    dem = np.zeros((1, 11))
    low, high = o2_interval_kg(STRAIGHT, dem, CELL)
    # Ida y vuelta de 100 m en plano: 200 m al costo en plano, sin importar la gravedad.
    assert low == pytest.approx(200 * O2_FLAT_KG_PER_M)
    assert high == pytest.approx(low)


def test_o2_interval_is_ordered_on_a_slope():
    dem = np.arange(11, dtype=float)[None, :] * 2.0  # 20 % de pendiente
    low, high = o2_interval_kg(STRAIGHT, dem, CELL, G_MARS_MS2)
    flat = o2_interval_kg(STRAIGHT, np.zeros((1, 11)), CELL)[0]
    assert flat < low < high
