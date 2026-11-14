import numpy as np
from scipy.ndimage import gaussian_filter

import calibrate as c
import eva_cost as m

CELL = (10.0, 10.0)


def _field(rng, n, sigma):
    f = gaussian_filter(rng.standard_normal((n, n)), sigma)
    return (f - f.min()) / (f.max() - f.min())


def _world(seed=0, n=96):
    rng = np.random.default_rng(seed)
    dem = 150 * _field(rng, n, 8)
    gy, gx = np.gradient(dem, *CELL)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    return dem, slope, _field(rng, n, 3), _field(rng, n, 5)


def test_multiplier_reproduces_paper_points():
    assert m.o2_multiplier(0.0) == 1.0
    assert np.isclose(m.o2_multiplier(0.45), 17.33 / 1.64)
    assert np.isclose(m.o2_multiplier(-0.10), 0.81 / 1.64)
    assert m.o2_multiplier(0.3, s=0.0) == 1.0


def test_round_trip_grows_with_grade():
    g = np.linspace(0, 0.45, 20)
    assert np.all(np.diff(m.round_trip_multiplier(g)) > 0)


def test_slope_penalty_is_zero_flat_and_one_at_the_limit():
    deg = np.array([0.0, 5.0, 10.0, 25.0, 40.0])
    p = m.slope_penalty(deg, 25.0)
    assert p[0] == 0.0 and np.isclose(p[3], 1.0) and p[4] == 1.0
    assert np.all(np.diff(p[:4]) > 0)


def test_slope_penalty_does_not_depend_on_gravity():
    deg = np.array([3.0, 10.0, 20.0])

    def extra(d, s):
        return m.round_trip_multiplier(np.tan(np.radians(d)), s) - 1.0

    for s in (0.38, 1.0):
        assert np.allclose(m.slope_penalty(deg, 25.0), extra(deg, s) / extra(25.0, s))


def test_interval_is_ordered_and_flat_is_exact():
    lo, hi = m.gradient_scale_bounds(0.38 * m.G_EARTH)
    assert np.isclose(lo, 0.38) and hi == 1.0
    dem, *_ = _world()
    slope_path = np.array([[0, i] for i in range(40)])
    flat_path = np.array([[0, i] for i in range(40)])
    flat_dem = np.zeros_like(dem)
    a, b = m.o2_interval_kg(slope_path, dem, CELL, 3.5e-5, 0.38 * m.G_EARTH)
    assert a < b
    a, b = m.o2_interval_kg(flat_path, flat_dem, CELL, 3.5e-5, 0.38 * m.G_EARTH)
    assert np.isclose(a, b) and np.isclose(a, 2 * 3.5e-5 * 390)


def test_fit_recovers_the_route_on_held_out_pairs():
    dem, slope, hazard, ti = _world()
    rng = np.random.default_rng(1)

    def cost_fn(wh, wi):
        return m.cell_cost(slope, hazard, ti, wh, wi)

    truth = cost_fn(3.0, 1.0)
    corners = [(5, 5), (90, 90), (5, 90), (90, 5), (50, 5), (50, 90), (5, 50), (90, 50)]
    demos = []
    for k in range(0, len(corners), 2):
        noisy = truth * (1 + 0.1 * rng.standard_normal(truth.shape))
        demos.append(c.route(np.maximum(noisy, 0.1), corners[k], corners[k + 1], CELL))
    train, test = demos[:2], demos[2:]

    (wh, wi), loss = c.fit_weights(cost_fn, train, CELL)
    default = m.cell_cost(slope, hazard, ti, 0.1, 0.1)

    def held(cost):
        return np.mean(
            [c.separation_m(c.route(cost, tuple(d[0]), tuple(d[-1]), CELL), d, CELL) for d in test]
        )

    print(
        f"pesos ajustados ({wh:.2f}, {wi:.2f}); separación en tramos no vistos: "
        f"{held(cost_fn(wh, wi)):.1f} m ajustado, {held(default):.1f} m con pesos por defecto"
    )
    assert held(cost_fn(wh, wi)) < held(default)
