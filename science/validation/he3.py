"""HE3: la ruta segura con la capa NOAH-H queda más cerca de la traza real de Perseverance.

Tres brazos sobre la región real de Jezero, con la pendiente del modo Segura y la pendiente máxima
del traje fijas:

- A: Segura con NOAH-H; `w_riesgo` y `w_inestabilidad` calibrados.
- B: Segura sin NOAH-H (`w_riesgo` = 0); `w_inestabilidad` calibrado solo (fila 0 de la misma
  superficie de pérdida, porque la rejilla incluye el 0).
- C: línea base de mínima distancia (`WalkMode.baseline` del motor).

Dos comparaciones fijadas de antemano, unilaterales, con Wilcoxon pareada aproximada: A < B y B < C
en separación media simétrica (`calibrate.separation_m`), α = 0.025 cada una y r = |z|/√n ≥ 0.3,
con n los pares sin empate. La Segura sin calibrar (pesos de la app) sale como descriptivo.

En dos pasos, para que los pesos queden congelados antes de mirar la medición:

    python science/validation/he3.py calibrar --assets ../regions_real
    python science/validation/he3.py medir --assets ../regions_real

Las grillas se leen como .npy con `app.storage` (salida del pipeline): no se abre ningún ráster.
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from calibrate import fit_weights, separation_m  # noqa: E402

HERE = Path(__file__).parent
TRECHOS = HERE / "trechos.csv"
SUMMARY = HERE / "he3_resumen.json"
RESULTS = HERE / "he3_resultados.csv"
GRID = np.concatenate([[0.0], np.geomspace(0.1, 10, 7)])
ALPHA = 0.025
R_MIN = 0.3


def layers(g, max_slope_deg, w_slope):
    """Partes fijas del costo (misma fórmula que engine/cost.py; Segura no lleva ciencia)."""
    from app.engine.cost import MIN_CELL_COST
    from app.engine.o2_model import slope_penalty

    base = 1.0 + w_slope * slope_penalty(g.slope, max_slope_deg)
    blocked = g.slope > max_slope_deg

    def cost(w_hazard, w_instability):
        c = base + w_hazard * g.hazard + w_instability * (1.0 - g.thermal_inertia)
        c = np.maximum(c, MIN_CELL_COST).astype(np.float64)
        c[blocked] = np.inf
        return c

    return cost


def calibrate(cost, segments, cell_m):
    """(w_riesgo, w_inestabilidad) de A, w_inestabilidad de B y la superficie de pérdida."""
    (w_h, w_i), loss = fit_weights(cost, segments, cell_m, GRID)
    w_i_b = float(GRID[int(loss[0].argmin())])  # fila w_riesgo = 0
    return w_h, w_i, w_i_b, loss


def one_sided(d):
    """Wilcoxon pareada unilateral (d < 0), aproximada: p, z, r y n sin empates."""
    d = np.asarray(d, dtype=float)
    n = int(np.count_nonzero(d))
    if n == 0:
        return 1.0, 0.0, 0.0, 0
    res = wilcoxon(d, alternative="less", method="approx")
    z = float(res.zstatistic)
    return float(res.pvalue), z, abs(z) / np.sqrt(n), n


def load_trechos(m):
    """Trechos de trechos.csv como celdas de la grilla; fuera los que salen de la región."""
    from app.engine.pathfind import NoPathError
    from app.engine.validation import traverse_to_cells

    pts = {}
    with open(TRECHOS, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (int(r["trecho_id"]), r["conjunto"])
            pts.setdefault(key, []).append((float(r["lon"]), float(r["lat"])))
    kept, dropped = {}, []
    for (tid, conjunto), lonlat in sorted(pts.items()):
        try:
            cells, outside = traverse_to_cells(m, np.array(lonlat))
        except NoPathError:  # el trecho entero cae fuera
            cells, outside = None, len(lonlat)
        if outside:
            dropped.append(tid)
        else:
            kept[tid] = (conjunto, cells)
    return kept, dropped


def _region(assets):
    os.environ["ASSETS_DIR"] = str(Path(assets).resolve())
    from app.geo import cell_size_m
    from app.schemas.route import SuitLimits
    from app.storage import load_region

    g = load_region("jezero")
    if g.manifest.synthetic:
        sys.exit("HE3 solo se mide sobre Jezero real: --assets apunta a la región sintética")
    return g, cell_size_m(g.manifest), SuitLimits().max_slope_deg


def cmd_calibrar(assets):
    from app.engine.cost import MODE_WEIGHTS
    from app.schemas.route import WalkMode

    g, cell_m, max_slope = _region(assets)
    w_slope = MODE_WEIGHTS[WalkMode.safe]["slope"]
    trechos, dropped = load_trechos(g.manifest)
    cal = {t: c for t, (k, c) in trechos.items() if k == "calibracion"}
    w_h, w_i, w_i_b, loss = calibrate(layers(g, max_slope, w_slope), list(cal.values()), cell_m)
    summary = {
        "region": g.manifest.id,
        "dataset_version": g.manifest.dataset_version,
        "max_slope_deg": max_slope,
        "w_pendiente": w_slope,
        "rejilla": GRID.tolist(),
        "trechos_fuera_de_la_region": dropped,
        "calibracion": {
            "trechos": sorted(cal),
            "A": {"w_riesgo": w_h, "w_inestabilidad": w_i},
            "B": {"w_riesgo": 0.0, "w_inestabilidad": w_i_b},
            "perdida_m": np.round(loss, 2).tolist(),  # filas w_riesgo, columnas w_inestabilidad
        },
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"A: w_riesgo {w_h:g}, w_inestabilidad {w_i:g} · B: w_inestabilidad {w_i_b:g}")
    print(f"pérdida mínima {loss.min():.1f} m; con w_riesgo = 0, {loss[0].min():.1f} m")
    print(f"fuera de la región: {dropped}. Pesos congelados en {SUMMARY.name}")


def cmd_medir(assets):
    from app.engine.consumables import ascent_m, segment_profile
    from app.engine.cost import build_cost
    from app.engine.pathfind import find_path
    from app.schemas.route import WalkMode

    g, cell_m, max_slope = _region(assets)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    cal = summary["calibracion"]
    cost = layers(g, max_slope, summary["w_pendiente"])
    arms = {
        "A": cost(cal["A"]["w_riesgo"], cal["A"]["w_inestabilidad"]),
        "B": cost(0.0, cal["B"]["w_inestabilidad"]),
        "C": build_cost(g, WalkMode.baseline, max_slope),
        "segura_app": build_cost(g, WalkMode.safe, max_slope),
    }
    trechos, _ = load_trechos(g.manifest)
    med = {t: c for t, (k, c) in trechos.items() if k == "medicion"}

    def describe(path):
        km = float(segment_profile(path, g.dem, cell_m)[0].sum() / 1000)
        risk = float(g.hazard[path[:, 0], path[:, 1]].mean())
        return km, ascent_m(path, g.dem), risk

    rows, sep = [], {k: [] for k in arms}
    for tid, track in med.items():
        rows.append([tid, "rover", "", *describe(track)])
        for name, c in arms.items():
            path = find_path(c, tuple(map(int, track[0])), tuple(map(int, track[-1])), cell_m)
            s = separation_m(path, track, cell_m)
            sep[name].append(s)
            rows.append([tid, name, s, *describe(path)])

    with open(RESULTS, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["trecho_id", "brazo", "separacion_m", "distancia_km", "desnivel_m", "riesgo"])
        for r in rows:
            w.writerow([r[0], r[1], *(f"{x:.3f}" if x != "" else "" for x in r[2:])])

    a, b, c = (np.array(sep[k]) for k in "ABC")
    tests = {}
    for name, d in (("A<B", a - b), ("B<C", b - c)):
        p, z, r, n = one_sided(d)
        tests[name] = {
            "p": p, "z": z, "r": r, "n_sin_empate": n, "empates": len(d) - n,
            "gana": int(np.sum(d < 0)), "pierde": int(np.sum(d > 0)),
            "soporta": bool(p < ALPHA and r >= R_MIN),
        }  # fmt: skip
    rover_risk = float(np.mean([g.hazard[t[:, 0], t[:, 1]].mean() for t in med.values()]))
    summary["medicion"] = {
        "trechos": sorted(med),
        "separacion_mediana_m": {k: float(np.median(v)) for k, v in sep.items()},
        "pruebas": tests,
        "riesgo_medio_rover": rover_risk,
        "riesgo_medio_region": float(np.nanmean(g.hazard)),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    for k, v in summary["medicion"]["separacion_mediana_m"].items():
        print(f"{k:11s} separación mediana {v:6.1f} m")
    for name, t in tests.items():
        verdict = "soporta" if t["soporta"] else "no soporta"
        print(
            f"{name}: gana {t['gana']}, pierde {t['pierde']}, empates {t['empates']}; "
            f"p = {t['p']:.4f}, r = {t['r']:.2f} -> {verdict}"
        )
    print(f"{RESULTS.name} y {SUMMARY.name} escritos")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paso", choices=["calibrar", "medir"])
    ap.add_argument("--assets", required=True, help="carpeta con index.json y jezero/ (real)")
    args = ap.parse_args()
    (cmd_calibrar if args.paso == "calibrar" else cmd_medir)(args.assets)


if __name__ == "__main__":
    main()
