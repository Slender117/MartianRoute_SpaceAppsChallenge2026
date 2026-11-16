"""H2: Perseverance traverse (JPL M20_Traverse_Path layer, one segment per sol) to GeoJSON.

The API expects a Feature with one LineString in (lon, lat) and `properties.rover`. This script:
  - joins the segments in sol order and removes the points repeated at the joins;
  - splits the traverse where it leaves the region bbox or where a segment is missing (a jump larger
    than --max-gap-m, 30 m by default: the normal spacing reaches 12 m), because the API joins the
    remaining points with a straight line and that would invent a path;
  - keeps the longest continuous stretch in the requested sol range.

    python convert_traverse.py M20_traverse_2026-11-12.json --out perseverance.geojson
    python convert_traverse.py M20_traverse_2026-11-12.json --sols 389 413 --out tramo.geojson
    python convert_traverse.py M20_traverse_2026-11-12.json --candidates

Standard library only. The elevation (the file's third coordinate) is not copied: the API
takes it from the DEM.
"""

import argparse
import json
import math
from itertools import pairwise

R_MARS = 3389.5e3  # m, mean radius (project convention, docs/supuestos.md)
# lon_min, lat_min, lon_max, lat_max of `jezero` in pipeline/config/regions.yaml
BBOX = (77.25, 18.30, 77.60, 18.65)
SOURCE = "M20_Traverse_Path layer (JPL), file M20_traverse_2026-11-12.json in this repository"


def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    dla, dlo = math.sin((la2 - la1) / 2), math.sin((lo2 - lo1) / 2)
    h = dla**2 + math.cos(la1) * math.cos(la2) * dlo**2
    return 2 * R_MARS * math.asin(math.sqrt(h))


def points(features, sols):
    """(lon, lat, sol) in order, without the points repeated at segment joins."""
    out = []
    for f in features:
        sol = f["properties"]["sol"]
        if not sols[0] <= sol <= sols[1]:
            continue
        for lon, lat, *_ in f["geometry"]["coordinates"]:
            if not out or (lon, lat) != out[-1][:2]:
                out.append((lon, lat, sol))
    return out


def runs(pts, bbox, max_gap_m):
    """Continuous stretches: inside the bbox and with no jumps larger than max_gap_m."""

    def inside(p):
        return bbox[0] <= p[0] <= bbox[2] and bbox[1] <= p[1] <= bbox[3]

    out, cur = [], []
    for p in pts:
        if not inside(p) or (cur and hav(cur[-1], p) > max_gap_m):
            if cur:
                out.append(cur)
            cur = []
        if inside(p):
            cur.append(p)
    return out + [cur] if cur else out


def length_m(run):
    return sum(hav(a, b) for a, b in pairwise(run))


def candidates(run_list, lo=3000.0, hi=6000.0, top=6):
    """Stretches of lo to hi meters, as straight as possible (chord / length).

    They validate point-to-point routes: the full traverse loops around and does not compare with a
    sola ruta de A a B.
    """
    found = []
    for run in run_list:
        cum = [0.0]
        for a, b in pairwise(run):
            cum.append(cum[-1] + hav(a, b))
        j = 0
        for i in range(len(run)):
            while j < len(run) - 1 and cum[j] - cum[i] < lo:
                j += 1
            if cum[j] - cum[i] < lo:
                break
            k = j
            while k < len(run) - 1 and cum[k + 1] - cum[i] <= hi:
                k += 1
            for e in (j, k):
                dist = cum[e] - cum[i]
                found.append((hav(run[i], run[e]) / dist, run[i], run[e], dist))
    found.sort(key=lambda c: -c[0])
    chosen = []
    for c in found:
        s0, s1 = c[1][2], c[2][2]
        if all(s1 < d[1][2] or s0 > d[2][2] for d in chosen):
            chosen.append(c)
        if len(chosen) == top:
            break
    return chosen


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("traverse", help="M20_traverse_*.json (one LineString per sol)")
    ap.add_argument("--out", help="GeoJSON de salida")
    ap.add_argument("--sols", nargs=2, type=int, default=(0, 10**6), metavar=("DESDE", "HASTA"))
    ap.add_argument("--bbox", nargs=4, type=float, default=BBOX, metavar="GRADOS")
    ap.add_argument("--max-gap-m", type=float, default=30.0)
    ap.add_argument("--candidates", action="store_true", help="the straightest 3 to 6 km stretches")
    args = ap.parse_args()

    with open(args.traverse, encoding="utf-8") as f:
        features = json.load(f)["features"]
    pts = points(features, args.sols)
    rs = runs(pts, args.bbox, args.max_gap_m)
    kept = sum(len(r) for r in rs)
    print(
        f"{len(pts)} puntos, {len(rs)} trechos continuos dentro del bbox; {kept} dentro, "
        f"{len(pts) - kept} fuera"
    )

    if args.candidates:
        print("recta   sols        longitud   inicio (lon, lat)       fin (lon, lat)")
        for ratio, a, b, dist in candidates(rs):
            print(
                f"{ratio:5.2f}   {a[2]:>4}-{b[2]:<5}  {dist / 1000:6.2f} km  "
                f"({a[0]:.4f}, {a[1]:.4f})  ({b[0]:.4f}, {b[1]:.4f})"
            )

    if args.out:
        best = max(rs, key=length_m)
        geojson = {
            "type": "Feature",
            "properties": {
                "rover": "perseverance",
                "source": SOURCE,
                "sol_min": best[0][2],
                "sol_max": best[-1][2],
                "length_m": round(length_m(best), 1),
                "max_gap_m": args.max_gap_m,
            },
            "geometry": {"type": "LineString", "coordinates": [[lon, lat] for lon, lat, _ in best]},
        }
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(geojson, f)
        print(
            f"{args.out}: {len(best)} puntos, sols {best[0][2]} a {best[-1][2]}, "
            f"{length_m(best) / 1000:.2f} km"
        )


if __name__ == "__main__":
    main()
