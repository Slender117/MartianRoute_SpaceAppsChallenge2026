"""Exploratory HE3: three variants that do not replace the result fixed in advance (he3.py).

They were run after seeing that HE3 does not hold, so any p here is exploratory: it helps
decide what to measure next time, not to claim the hypothesis. Each variant calibrates
only on calibration stretches (sol ≤ 606) and measures on the measurement ones, like he3.py.

- largos: stretches of 1 to 3 km instead of 0.5 to 1 km (more cells so routes can separate).
- intransitable: NOAH-H as the fraction of large ripples per cell instead of the mean risk.
- pendiente: the slope weight is calibrated too (fixed at 4.0 in he3.py).

    python science/validation/he3_exploratorio.py --assets ../regions_real
"""

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import he3
import numpy as np
import trechos as tr

OUT = Path(__file__).with_name("he3_exploratorio.json")


def stretches(m, items):
    """{id: (set, cells)} with the stretches that fall entirely inside the region."""
    from app.engine.pathfind import NoPathError
    from app.engine.validation import traverse_to_cells

    out = {}
    for tid, conjunto, lonlat in items:
        try:
            cells, outside = traverse_to_cells(m, np.array(lonlat))
        except NoPathError:
            continue
        if not outside:
            out[tid] = (conjunto, cells)
    return out


def fit(layer, segments, cell_m, max_slope, slopes):
    """Best weights of A (with the layer) and of B (layer at 0), sweeping the slope weights."""
    a = b = None
    for ws in slopes:
        w_h, w_i, w_i_b, loss = he3.calibrate(he3.layers(layer, max_slope, ws), segments, cell_m)
        if a is None or loss.min() < a["perdida_m"]:
            a = {"w_pendiente": ws, "w_capa": w_h, "w_inestabilidad": w_i, "perdida_m": loss.min()}
        if b is None or loss[0].min() < b["perdida_m"]:
            b = {"w_pendiente": ws, "w_capa": 0.0, "w_inestabilidad": w_i_b,
                 "perdida_m": loss[0].min()}  # fmt: skip
    return a, b


def measure(layer, g, med, cell_m, max_slope, a, b):
    from app.engine.cost import build_cost
    from app.engine.pathfind import find_path
    from app.schemas.route import WalkMode

    costs = {
        "A": he3.layers(layer, max_slope, a["w_pendiente"])(a["w_capa"], a["w_inestabilidad"]),
        "B": he3.layers(layer, max_slope, b["w_pendiente"])(0.0, b["w_inestabilidad"]),
        "C": build_cost(g, WalkMode.baseline, max_slope),
    }
    sep = {k: [] for k in costs}
    for track in med:
        for k, c in costs.items():
            path = find_path(c, tuple(map(int, track[0])), tuple(map(int, track[-1])), cell_m)
            sep[k].append(he3.separation_m(path, track, cell_m))
    sa, sb, sc = (np.array(sep[k]) for k in "ABC")
    tests = {}
    for name, d in (("A<B", sa - sb), ("B<C", sb - sc)):
        p, z, r, n = he3.one_sided(d)
        tests[name] = {
            "p": p, "r": r, "n_sin_empate": n, "gana": int(np.sum(d < 0)),
            "pierde": int(np.sum(d > 0)), "mediana_pareada_m": float(np.median(d)),
        }  # fmt: skip
    return {k: float(np.median(v)) for k, v in sep.items()}, tests


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--assets", required=True)
    args = ap.parse_args()
    g, cell_m, max_slope = he3._region(args.assets)
    m = g.manifest

    with open(he3.TRECHOS.parents[2] / "M20_traverse_2026-11-12.json", encoding="utf-8") as f:
        features = json.load(f)["features"]
    short = stretches(m, [(t, c, [v[:2] for v in vs]) for t, c, vs, *_ in tr.trechos(features)])
    long_ = stretches(
        m, [(t, c, [v[:2] for v in vs]) for t, c, vs, *_ in tr.trechos(features, 1000, 3000)]
    )
    impassable = np.load(Path(args.assets) / m.id / "layers" / "impassable_fraction.npy")

    variants = {
        "largos": (g, long_, [4.0]),
        "intransitable": (
            SimpleNamespace(slope=g.slope, hazard=impassable, thermal_inertia=g.thermal_inertia),
            short,
            [4.0],
        ),
        "pendiente": (g, short, he3.GRID.tolist()),
    }
    results = {}
    for name, (layer, sets, slopes) in variants.items():
        cal = [c for k, c in sets.values() if k == "calibracion"]
        med = [c for k, c in sets.values() if k == "medicion"]
        a, b = fit(layer, cal, cell_m, max_slope, slopes)
        medians, tests = measure(layer, g, med, cell_m, max_slope, a, b)
        results[name] = {"n_calibracion": len(cal), "n_medicion": len(med), "A": a, "B": b,
                         "separacion_mediana_m": medians, "pruebas": tests}  # fmt: skip
        print(f"\n{name}: calibration {len(cal)}, measurement {len(med)}")
        print(f"  A {a} · B {b}")
        rounded = {k: round(v, 1) for k, v in medians.items()}
        print(f"  medianas {rounded}")
        for t, v in tests.items():
            print(
                f"  {t}: gana {v['gana']}, pierde {v['pierde']}, p = {v['p']:.3f}, "
                f"r = {v['r']:.2f}, diferencia pareada mediana {v['mediana_pareada_m']:+.1f} m"
            )
    text = json.dumps(results, indent=2, ensure_ascii=False, default=float)
    OUT.write_text(text, encoding="utf-8")
    print(f"\n{OUT.name} escrito")


if __name__ == "__main__":
    main()
