"""Recorridos de rovers desde MMGIS (JPL), con el sol de cada tramo.

El recorrido de Perseverance en MMGIS ya trae el sol de cada tramo. El de Curiosity no: cada tramo
termina en un waypoint, y el sol se toma del waypoint donde termina. Desde pipeline/:

    python -m marsdata.fetch.mmgis MSL ../MSL_traverse_<fecha>.json

baja el recorrido y los waypoints y escribe el recorrido con soles, en el formato que lee
process/traverse.py (una LineString por tramo con `sol` en sus propiedades).
"""

import json
import math
import sys
from pathlib import Path

import httpx
import numpy as np

from marsdata.region import METERS_PER_DEGREE

MMGIS_URL = "https://mars.nasa.gov/mmgis-maps/{mission}/Layers/json/{mission}_{layer}.json"
# Distancia máxima entre el final de un tramo y su waypoint. En el recorrido de Curiosity del
# 14 nov 2026, 1316 de 1317 tramos terminan a menos de 1 m de uno.
MAX_MATCH_M = 2.0
CRS84 = {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}


def _flatten(geometry: dict) -> list[list[float]]:
    """Coordenadas de una LineString o MultiLineString, sin repetir los puntos de unión."""
    parts = geometry["coordinates"]
    if geometry["type"] == "LineString":
        parts = [parts]
    coords: list[list[float]] = []
    for part in parts:
        for c in part:
            if not coords or c[:2] != coords[-1][:2]:
                coords.append(c)
    return coords


def traverse_with_sols(traverse: dict, waypoints: dict, max_match_m: float = MAX_MATCH_M) -> dict:
    """Una LineString por tramo, en el orden del archivo, con el sol del waypoint donde termina.

    Un tramo que no termina en un waypoint hereda el sol del anterior. El sol nunca baja de un
    tramo al siguiente, para que ordenar por sol no cambie el orden del recorrido.
    """
    props = [w["properties"] for w in waypoints["features"]]
    lon = np.array([p["lon"] for p in props])
    lat = np.array([p["lat"] for p in props])
    sols = np.array([int(p["sol"]) for p in props])

    features, prev = [], None
    for f in traverse["features"]:
        coords = _flatten(f["geometry"])
        end_lon, end_lat = coords[-1][:2]
        dx = (lon - end_lon) * METERS_PER_DEGREE * math.cos(math.radians(end_lat))
        dy = (lat - end_lat) * METERS_PER_DEGREE
        dist = np.hypot(dx, dy)
        i = int(dist.argmin())
        sol = int(sols[i])
        if prev is not None and (dist[i] > max_match_m or sol < prev):
            sol = prev
        prev = sol
        features.append(
            {
                "type": "Feature",
                "properties": {"sol": sol, "length_m": f["properties"].get("Length")},
                "geometry": {"type": "LineString", "coordinates": coords},
            }
        )
    return {"type": "FeatureCollection", "crs": CRS84, "features": features}


def _get(mission: str, layer: str) -> dict:
    r = httpx.get(MMGIS_URL.format(mission=mission, layer=layer), timeout=120)
    r.raise_for_status()
    return r.json()


def write_feature_collection(fc: dict, path: Path) -> None:
    """Un tramo por línea, como los archivos de MMGIS, para que los cambios se lean en un diff."""
    head = {k: v for k, v in fc.items() if k != "features"}
    body = ",\n".join(json.dumps(f, ensure_ascii=False) for f in fc["features"])
    text = json.dumps(head, ensure_ascii=False)[:-1] + ', "features": [\n' + body + "\n]}\n"
    path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    mission, out = argv or sys.argv[1:]
    fc = traverse_with_sols(_get(mission, "traverse"), _get(mission, "waypoints"))
    fc["name"] = f"{mission}_traverse_with_sols"
    write_feature_collection(fc, Path(out))
    first, last = fc["features"][0]["properties"]["sol"], fc["features"][-1]["properties"]["sol"]
    print(f"{len(fc['features'])} tramos, soles {first} a {last}: {out}")


if __name__ == "__main__":
    main()
