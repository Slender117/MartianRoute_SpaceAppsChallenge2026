"""Terrain risk (0-1) per NOAH-H interpretive group, in the order of Barrett et al., 2022.

The risk comes from what Barrett states about each group, scaled by rank (IG_RISK): the extremes
have a direct quote and the three in the middle are an assumed linear interpolation (modeled).

Backup (it does not enter the cost): the risk given by Barrett's 14 labels (Table 2), in an order
of its own (Alta 1 < Aceptable con peligros locales 2 < Peligros locales 3 < Incierta 4 <
Possibly low 5 < Low 6 < Very low 7; risk = (level - 1) / 6), with each group's mean
weighted by the area of each DC class, over the whole mosaic and over the windows (bounding box)
of the calibration stretches in trechos.csv; the measurement ones are not read. Both weightings
put bedrock above non-bedrock, the reverse of Barrett: along Perseverance's path
rough bedrock dominates, labeled "Very low" for the ExoMars rover at Oxia
Planum. The per-class labels do not carry over to Jezero; the 14 classes remain future
work. Each window or strip is weighted by cos(lat), because the Plate Carrée pixel shrinks to the
north; the raster is never read whole.

    python science/validation/noahh_risk.py RUTA/Jezero_NOAHH_mosaic_DC.tif

Fuentes:
- Barrett, A. M., Balme, M. R., Woods, M., Karachalios, S., Petrocelli, D., Joudrier, L., &
  Sefton-Nash, E. (2022). NOAH-H, a deep-learning, terrain classification system for Mars: Results
  for the ExoMars Rover candidate landing sites. Icarus, 371, 114701.
  https://doi.org/10.1016/j.icarus.2021.114701
- Wright, J., Barrett, A. M., Fawdon, P., et al. (2022). Jezero crater, Mars: application of the
  deep learning NOAH-H terrain classification system. Journal of Maps, 18(2), 484-496.
  https://doi.org/10.1080/17445647.2022.2095935
- Wright, J., Barrett, A. M., Fawdon, P., et al. (2022). NOAH-H_terrain_classifications_of_Jezero_
  Crater_Mars.zip (v2) [Data set]. The Open University. https://doi.org/10.21954/ou.rd.17121482.v2
"""

import argparse
import csv
import math
from pathlib import Path

import numpy as np

LABELS = [
    "Alta",
    "Aceptable con peligros locales",
    "Peligros locales",
    "Incierta",
    "Posiblemente baja",
    "Baja",
    "Muy baja",
]
# DC pixel value (Wright et al., 2022, Table 1) -> (Barrett class, label, IG); labels go to the CSV.
DC = {
    1: (1, "Incierta", 1),
    2: (5, "Aceptable con peligros locales", 2),
    3: (12, "Peligros locales", 4),
    4: (4, "Alta", 2),
    5: (13, "Baja", 4),
    6: (11, "Baja", 4),
    7: (3, "Incierta", 1),
    8: (2, "Baja", 1),
    9: (9, "Posiblemente baja", 5),
    10: (6, "Muy baja", 2),
    11: (14, "Peligros locales", 3),
    12: (8, "Baja", 5),
    13: (7, "Peligros locales", 2),
    14: (10, "Muy baja", 5),
}
IG = {
    1: "No roca madre",
    2: "Roca madre",
    3: "Campos de rocas",
    4: "Ondulaciones pequeñas",
    5: "Ondulaciones grandes",
}
BARRETT = "Barrett et al. (2022), doi:10.1016/j.icarus.2021.114701,"
DATASET = "Wright et al. (2022b), doi:10.21954/ou.rd.17121482.v2"
# IG -> (risk, basis, statement by Barrett et al., 2022), in Spanish: they go to noahh_ig_risk.csv.
IG_RISK = {
    2: (0.0, "cita directa", "§2.3: la roca madre da agarre sea rugosa o lisa"),
    1: (0.25, "interpolación supuesta", "§2.3 y §6.3: peligro bastante incierto, puede ser arena"),
    3: (0.5, "interpolación supuesta", "§7.2: peligro de navegación sea cual sea el sustrato"),
    4: (0.75, "interpolación supuesta", "§6.3: las ondulaciones chicas a veces son transitables"),
    5: (1.0, "cita directa", "§6.3: las ondulaciones grandes nunca son transitables"),
}
R_MOSAIC = 3_396_190.0  # m, sphere of the mosaic CRS


def class_risk(label):
    return LABELS.index(label) / (len(LABELS) - 1)


def trecho_windows(src, trechos_csv, conjunto="calibracion"):
    """One window per stretch of the set: the pixel rectangle that encloses its vertices."""
    from rasterio.windows import Window

    xy = {}
    with open(trechos_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["conjunto"] == conjunto:
                xy.setdefault(row["trecho_id"], []).append((float(row["x_m"]), float(row["y_m"])))
    wins = []
    for pts in xy.values():
        xs, ys = zip(*pts, strict=True)
        r0, c0 = src.index(min(xs), max(ys))
        r1, c1 = src.index(max(xs), min(ys))
        wins.append(Window.from_slices((r0, r1 + 1), (c0, c1 + 1)))
    return wins


def dc_areas_km2(path, trechos_csv=None, rows=128):
    """Area (km²) per pixel value, in the calibration windows or, without `trechos_csv`, in all the
    mosaic in strips of `rows` rows (one row of tiles).

    GDAL's block cache is limited so it does not hold the decompressed raster either.
    """
    import rasterio
    from rasterio.windows import Window

    area = np.zeros(256)
    with rasterio.Env(GDAL_CACHEMAX=64), rasterio.open(path) as src:
        if trechos_csv:
            wins = trecho_windows(src, trechos_csv)
        else:
            wins = [
                Window(0, r, src.width, min(rows, src.height - r))
                for r in range(0, src.height, rows)
            ]
        px_m = src.res[0]
        for win in wins:
            y = src.xy(win.row_off + win.height / 2, win.col_off)[1]
            cos_lat = math.cos(y / R_MOSAIC)
            counts = np.bincount(src.read(1, window=win).ravel(), minlength=256)
            area += counts * px_m * px_m * cos_lat / 1e6
    return area


def group_risk(area):
    """IG -> (area-weighted risk, min risk, max risk, area km²); nan if there is no area."""
    out = {}
    for g in IG:
        vals = [v for v, (_, _, ig) in DC.items() if ig == g]
        risks = np.array([class_risk(DC[v][1]) for v in vals])
        w = np.array([area[v] for v in vals])
        risk = float(risks @ w / w.sum()) if w.sum() else math.nan
        out[g] = (risk, risks.min(), risks.max(), float(w.sum()))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("dc_tif", help="Jezero_NOAHH_mosaic_DC.tif")
    ap.add_argument("--trechos", default=str(Path(__file__).with_name("trechos.csv")))
    ap.add_argument("--out-dir", default=str(Path(__file__).parent))
    args = ap.parse_args()

    cal = dc_areas_km2(args.dc_tif, args.trechos)
    mosaic = dc_areas_km2(args.dc_tif)
    for name, area in (("calibración", cal), ("mosaico", mosaic)):
        other = {v: round(a, 4) for v, a in enumerate(area) if a and v not in DC}
        print(f"{name}: area outside the 14 classes (km²): {other}")

    out = Path(args.out_dir)
    with open(out / "noahh_dc_risk.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            ["dc_value", "clase_barrett", "etiqueta", "nivel", "riesgo", "ig_value",
             "area_calibracion_km2", "area_mosaico_km2"]
        )  # fmt: skip
        for v, (cls, label, g) in DC.items():
            w.writerow(
                [v, cls, label, LABELS.index(label) + 1, f"{class_risk(label):.4f}", g,
                 f"{cal[v]:.4f}", f"{mosaic[v]:.4f}"]
            )  # fmt: skip

    groups, groups_mosaic = group_risk(cal), group_risk(mosaic)
    with open(out / "noahh_ig_risk.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            ["ig_value", "grupo", "clases_barrett", "riesgo", "base", "cita", "dataset",
             "procedencia", "area_calibracion_km2", "respaldo_riesgo_clases_calibracion",
             "respaldo_riesgo_clases_mosaico"]
        )  # fmt: skip
        no_cost = "sin información: no entra al costo"
        w.writerow([0, "Sin dato", "", "", no_cost, "", DATASET, "", "", "", ""])
        for g in sorted(IG_RISK):
            risk, base, cita = IG_RISK[g]
            cls = " ".join(str(c) for c, _, ig in sorted(DC.values()) if ig == g)
            w.writerow(
                [g, IG[g], cls, f"{risk:.2f}", base, f"{BARRETT} {cita}", DATASET, "modeled",
                 f"{groups[g][3]:.4f}", f"{groups[g][0]:.4f}", f"{groups_mosaic[g][0]:.4f}"]
            )  # fmt: skip
        w.writerow([127, "Nodata", "", "", no_cost, "", DATASET, "", f"{cal[127]:.4f}", "", ""])

    print("IG  grupo                   riesgo  base                    respaldo cal.  mosaico")
    for g, (risk, base, _) in IG_RISK.items():
        print(
            f"{g:>2}  {IG[g]:<22}  {risk:6.2f}  {base:<22}  {groups[g][0]:13.3f}  "
            f"{groups_mosaic[g][0]:7.3f}"
        )
    print(f"nodata in the calibration windows: {cal[127]:.4f} km²")


if __name__ == "__main__":
    main()
