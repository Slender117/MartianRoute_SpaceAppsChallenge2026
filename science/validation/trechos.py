"""Trechos rectos de 0.5 a 1 km del recorrido con ambos extremos dentro del mosaico NOAH-H, a CSV.

Una fila por vértice. Calibración: trechos que terminan en sol <= SOL_CUT; medición: el resto.
Las longitudes siguen la convención del proyecto (R_MARS de convert_traverse). x_m, y_m están en el
CRS del mosaico (Equirectangular, esfera de 3,396,190 m), común a los mosaicos DC e IG; fila y
columna se sacan con `src.index(x, y)` de cada mosaico, porque sus geotransformaciones difieren en
fracciones de píxel.

    python science/validation/trechos.py M20_traverse_2026-11-12.json

Solo biblioteca estándar.
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import convert_traverse as ct  # noqa: E402

R_MOSAIC = 3_396_190.0  # m, esfera Mars_2000 del CRS de NOAH-H
# left, bottom, right, top de Jezero_NOAHH_mosaic_DC.tif (rasterio .bounds)
MOSAIC_BOUNDS = (4581995.356228024, 1085019.6179371926, 4598872.606228024, 1102248.8679371926)
SOL_CUT = 606  # propuesta por confirmar: deja 18 de calibración y 20 de medición


def to_mosaic(lon, lat):
    return R_MOSAIC * math.radians(lon), R_MOSAIC * math.radians(lat)


def inside(p):
    x, y = to_mosaic(p[0], p[1])
    b = MOSAIC_BOUNDS
    return b[0] <= x <= b[2] and b[1] <= y <= b[3]


def trechos(features, lo=500, hi=1000):
    """(id, conjunto, vértices, longitud_m, rectitud) en orden de sol."""
    rs = ct.runs(ct.points(features, (0, 10**6)), ct.BBOX, 30.0)
    found = [c for c in ct.candidates(rs, lo, hi, top=None) if inside(c[1]) and inside(c[2])]
    found.sort(key=lambda c: c[1][2])
    out = []
    for n, (ratio, a, b, dist) in enumerate(found, 1):
        # candidates() devuelve los mismos objetos del trecho continuo: se ubican por identidad.
        run = next(r for r in rs if any(p is a for p in r))
        i = next(k for k, p in enumerate(run) if p is a)
        e = next(k for k, p in enumerate(run) if p is b)
        conjunto = "calibracion" if b[2] <= SOL_CUT else "medicion"
        out.append((n, conjunto, run[i : e + 1], dist, ratio))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("traverse", help="M20_traverse_*.json (una LineString por sol)")
    ap.add_argument("--out", default=str(Path(__file__).with_name("trechos.csv")))
    args = ap.parse_args()

    with open(args.traverse, encoding="utf-8") as f:
        tr = trechos(json.load(f)["features"])

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["trecho_id", "conjunto", "sol", "lon", "lat", "x_m", "y_m"])
        for n, conjunto, verts, *_ in tr:
            for lon, lat, sol in verts:
                x, y = to_mosaic(lon, lat)
                w.writerow([n, conjunto, sol, lon, lat, f"{x:.2f}", f"{y:.2f}"])

    print("id  conjunto     sols        longitud  recta  vértices  todos dentro")
    for n, conjunto, verts, dist, ratio in tr:
        print(
            f"{n:>2}  {conjunto:<11}  {verts[0][2]:>4}-{verts[-1][2]:<5}  {dist:7.1f} m  "
            f"{ratio:5.2f}  {len(verts):>8}  {all(map(inside, verts))}"
        )
    cal = sum(c == "calibracion" for _, c, *_ in tr)
    print(f"{args.out}: {len(tr)} trechos, {cal} calibración, {len(tr) - cal} medición")


if __name__ == "__main__":
    main()
