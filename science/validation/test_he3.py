"""Solo la mecánica de HE3, sobre una grilla armada: los resultados nunca salen de aquí."""

from types import SimpleNamespace

import he3
import numpy as np

CELL = (10.0, 10.0)


def _world(n=30):
    """Plano con un bloque de riesgo en medio; el 'rover' lo rodea por el sur."""
    hazard = np.zeros((n, n))
    hazard[8:22, 12:18] = 1.0
    g = SimpleNamespace(slope=np.zeros((n, n)), hazard=hazard, thermal_inertia=np.ones((n, n)))
    detour = [(15, c) for c in range(2, 10)] + [(r, 10) for r in range(16, 24)]
    detour += [(23, c) for c in range(11, 20)] + [(r, 20) for r in range(22, 14, -1)]
    detour += [(15, c) for c in range(21, 28)]
    return g, np.array(detour)


def test_calibration_picks_the_hazard_layer_when_the_track_avoids_it():
    g, track = _world()
    cost = he3.layers(g, max_slope_deg=20.0, w_slope=4.0)
    w_h, _, w_i_b, loss = he3.calibrate(cost, [track], CELL)
    assert w_h > 0
    assert loss.min() < loss[0].min()  # sin la capa (w_riesgo = 0) se aleja más del recorrido
    assert w_i_b in he3.GRID


def test_one_sided_wilcoxon():
    p, z, r, n = he3.one_sided(-np.arange(1, 19, dtype=float))
    assert p < he3.ALPHA and z < 0 and r >= he3.R_MIN and n == 18
    assert he3.one_sided(np.zeros(5)) == (1.0, 0.0, 0.0, 0)  # todo empate: sin evidencia
