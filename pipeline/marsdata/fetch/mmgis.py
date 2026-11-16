"""Rover traverses from MMGIS (JPL), with the sol of each segment.

Perseverance's traverse in MMGIS already has the sol of each segment. Curiosity's does not: each
segment ends at a waypoint, and the sol is taken from the waypoint where it ends. From pipeline/:

    python -m marsdata.fetch.mmgis MSL ../MSL_traverse_<date>.json

downloads the traverse and the waypoints and writes the traverse with sols, in the format read by
process/traverse.py (one LineString per segment with `sol` in its properties).
"""

import json
import math
import sys
from pathlib import Path

import httpx
import numpy as np

from marsdata.region import METERS_PER_DEGREE

MMGIS_URL = "https://mars.nasa.gov/mmgis-maps/{mission}/Layers/json/{mission}_{layer}.json"
# Maximum distance between the end of a segment and its waypoint. In the Curiosity traverse of
# 14 Nov 2026, 1316 of 1317 segments end less than 1 m from one.
MAX_MATCH_M = 2.0
CRS84 = {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}


def _flatten(geometry: dict) -> list[list[float]]:
    """Coordinates of a LineString or MultiLineString, without repeating the join points."""
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
    """One LineString per segment, in file order, with the sol of the waypoint where it ends.

    A segment that does not end at a waypoint inherits the previous sol. The sol never decreases
    from one segment to the next, so sorting by sol does not change the traverse order.
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
    """One segment per line, like the MMGIS files, so changes read well in a diff."""
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
