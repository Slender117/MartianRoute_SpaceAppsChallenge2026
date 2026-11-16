"""Compares the proposed routes with a rover's real traverse.

Rover and routes are measured the same way: as cell-to-cell paths on the same grid and DEM.
That way the distance ratio does not depend on how many vertices the traverse GeoJSON has.
"""

import numpy as np
from scipy.spatial import cKDTree

from app.engine.consumables import ascent_m, segment_profile
from app.engine.cost import build_cost
from app.engine.pathfind import NoPathError, find_path
from app.geo import cell_size_m, latlon_to_fractional
from app.schemas.region import RegionManifest
from app.schemas.route import Provenance, SuitLimits, WalkMode
from app.schemas.validation import RouteValidation, TrackMetrics, ValidationResponse
from app.storage import RegionDataError, RegionGrids


def _traverse_coords(geojson: dict) -> np.ndarray:
    """GeoJSON coordinates as an (N, 2) array of (lon, lat)."""
    try:
        return np.array([point[:2] for point in geojson["geometry"]["coordinates"]], dtype=float)
    except (KeyError, TypeError, ValueError) as e:
        raise RegionDataError("The traverse is not a valid GeoJSON LineString") from e


def traverse_to_cells(m: RegionManifest, coords: np.ndarray) -> tuple[np.ndarray, int]:
    """Traverse as a continuous path of cells, and how many of its points fall outside."""
    rows, cols = latlon_to_fractional(m, coords[:, 1], coords[:, 0])
    h, w = m.shape
    inside = (
        (np.round(rows) >= 0) & (np.round(rows) < h) & (np.round(cols) >= 0) & (np.round(cols) < w)
    )
    outside = int((~inside).sum())
    rows, cols = rows[inside], cols[inside]
    if rows.size < 2:
        raise NoPathError(f"The traverse has no segment inside region {m.id}")

    # One point per crossed cell, to sample the DEM the same way as the routes.
    steps = np.ceil(np.maximum(np.abs(np.diff(rows)), np.abs(np.diff(cols)))).astype(int)
    pieces = [
        np.linspace([r0, c0], [r1, c1], max(n, 1), endpoint=False)
        for r0, c0, r1, c1, n in zip(rows[:-1], cols[:-1], rows[1:], cols[1:], steps, strict=True)
    ]
    dense = np.vstack([*pieces, [[rows[-1], cols[-1]]]])
    cells = np.round(dense).astype(np.int64)
    repeated = np.all(np.diff(cells, axis=0) == 0, axis=1)
    return cells[np.concatenate([[True], ~repeated])], outside


def validate_traverse(
    grids: RegionGrids, rover: str, geojson: dict, suit: SuitLimits
) -> ValidationResponse:
    m = grids.manifest
    cell_m = cell_size_m(m)
    track, outside = traverse_to_cells(m, _traverse_coords(geojson))
    if len(track) < 2:
        raise NoPathError(f"The traverse has no segment inside region {m.id}")

    track_km = float(segment_profile(track, grids.dem, cell_m)[0].sum() / 1000)
    tree = cKDTree(track * np.array(cell_m))

    routes: dict[WalkMode, RouteValidation] = {}
    for mode in WalkMode:
        cost = build_cost(grids, mode, suit.max_slope_deg)
        path = find_path(cost, tuple(map(int, track[0])), tuple(map(int, track[-1])), cell_m)
        separation, _ = tree.query(path * np.array(cell_m))
        distance_km = float(segment_profile(path, grids.dem, cell_m)[0].sum() / 1000)
        routes[mode] = RouteValidation(
            distance_km=distance_km,
            ascent_m=ascent_m(path, grids.dem),
            distance_ratio=distance_km / track_km,
            mean_separation_m=float(separation.mean()),
            max_separation_m=float(separation.max()),
        )

    return ValidationResponse(
        region=m.id,
        rover=rover,
        synthetic_data=m.synthetic,
        points_outside=outside,
        traverse=TrackMetrics(distance_km=track_km, ascent_m=ascent_m(track, grids.dem)),
        routes=routes,
        provenance={
            "traverse": Provenance.modeled if m.synthetic else Provenance.observed,
            "routes": Provenance.derived,
        },
    )
