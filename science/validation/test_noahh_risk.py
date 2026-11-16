import noahh_risk as n
import numpy as np


def test_group_risk_is_area_weighted_and_bounded():
    area = np.zeros(256)
    area[list(n.DC)] = 1.0
    area[4] = 99.0  # smooth bedrock (Alta) dominates its group
    groups = n.group_risk(area)
    assert sorted(groups) == [1, 2, 3, 4, 5]
    assert all(0 <= lo <= r <= hi <= 1 for r, lo, hi, _ in groups.values())
    assert groups[2][0] < 0.05  # almost the whole group is level 1 -> risk near 0
    assert np.isclose(groups[3][0], 2 / 6)  # boulder fields: a single class, local hazards
    assert np.isclose(groups[5][0], np.mean([5, 4, 6]) / 6)  # equal areas -> simple mean
