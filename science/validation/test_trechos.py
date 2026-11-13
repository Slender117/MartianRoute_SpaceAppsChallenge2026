import json
from pathlib import Path

import trechos as t


def test_counts_from_repo_traverse():
    path = Path(__file__).resolve().parents[2] / "M20_traverse_2026-11-12.json"
    tr = t.trechos(json.loads(path.read_text(encoding="utf-8"))["features"])
    assert len(tr) == 38
    assert sum(c == "calibracion" for _, c, *_ in tr) == 18
    assert all(t.inside(v[0]) and t.inside(v[-1]) for _, _, v, *_ in tr)
    assert all(500 <= d <= 1000 for *_, d, _ in tr)
