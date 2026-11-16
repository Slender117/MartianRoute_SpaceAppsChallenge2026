"""Per-region result cache: same numbers, without repeating the computation."""

import dataclasses

import numpy as np
import pytest

from app.engine.cost import build_cost, mode_free_terms
from app.engine.planner import compare_routes
from app.engine.safe_return import build_safe_return, return_hours
from app.schemas.route import LatLon, SuitLimits, WalkMode
from app.storage import GridMemo, load_region


def test_memo_keeps_the_most_recent_results():
    memo = GridMemo(size=2)
    calls = []

    def compute(key):
        calls.append(key)
        return key

    for key in ("a", "b", "a", "c", "a", "b"):
        memo.get(key, lambda k=key: compute(k))
    # "b" left when "c" came in (it was the least used) and was recomputed at the end.
    assert calls == ["a", "b", "c", "b"]


def test_grids_built_by_hand_do_not_cache(flat_grids):
    assert flat_grids.memo is None
    first = mode_free_terms(flat_grids, 25)
    assert mode_free_terms(flat_grids, 25)[0] is not first[0]


def test_loaded_regions_reuse_the_cost_terms(assets_dir):
    grids = load_region("test")
    penalty, _ = mode_free_terms(grids, 25)
    assert mode_free_terms(grids, 25)[0] is penalty
    assert mode_free_terms(grids, 30)[0] is not penalty
    # What is stored is read-only: nobody can alter it for the next request.
    with pytest.raises(ValueError):
        penalty[0, 0] = 1.0


def test_cached_cost_matches_a_fresh_one(assets_dir):
    grids = load_region("test")
    fresh = dataclasses.replace(grids, memo=None)
    for mode in WalkMode:
        build_cost(grids, mode, 25)  # fills the cache
        np.testing.assert_array_equal(build_cost(grids, mode, 25), build_cost(fresh, mode, 25))


def test_cached_routes_match_fresh_ones(assets_dir):
    grids = load_region("test")
    fresh = dataclasses.replace(grids, memo=None)
    end = LatLon(lat=0.2, lon=0.9)
    cached = compare_routes(grids, None, end, SuitLimits())
    cached_again = compare_routes(grids, None, end, SuitLimits())
    direct = compare_routes(fresh, None, end, SuitLimits())
    for mode in WalkMode:
        assert cached[mode].model_dump() == direct[mode].model_dump()
        assert cached_again[mode].model_dump() == direct[mode].model_dump()


def test_safe_return_reuses_the_map_when_only_the_autonomy_changes(assets_dir):
    grids = load_region("test")
    base = grids.manifest.base
    hours = return_hours(grids, base, 25)
    assert return_hours(grids, base, 25) is hours
    assert return_hours(grids, base, 30) is not hours

    fresh = dataclasses.replace(grids, memo=None)
    for autonomy in (4.0, 8.0):
        suit = SuitLimits(autonomy_h=autonomy, max_slope_deg=25)
        assert build_safe_return(grids, None, suit) == build_safe_return(fresh, None, suit)
