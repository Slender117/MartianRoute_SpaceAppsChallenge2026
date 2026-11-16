"""Processes a region's raw GeoTIFFs and produces the grids for the API and the 3D view.

- DEM: averaged to the grid, validated (float and within the Mars range); gaps are filled with
  the nearest cell with data.
- Slope: with the real cell size in each direction (the east-west side is shorter).
- Categorical risk (NOAH-H): classes are counted per cell; from that come the mean risk with
  Edgar's table, the impassable fraction (classes with risk 1) and the dominant class.
- Risk without classification (`hazard_proxy: roughness`, Gale): roughness of the unreduced DEM,
  normalized to 0–1 within the region.
- Capas continuas (THEMIS...): bilineal y normalizadas a 0–1.

Each layer's coverage (fraction with data, HE1) is measured before filling and goes to the manifest.
"""

from dataclasses import dataclass, field

import numpy as np
from rasterio.warp import Resampling

from marsdata.fetch.sources import raw_path
from marsdata.process.classes import ClassCounts, ClassInfo, count_classes, load_risk_table
from marsdata.process.reproject import coverage, fill_nearest, warp_to_region
from marsdata.process.terrain import (
    ROUGHNESS_SIGMA_M,
    normalize,
    roughness_to_region,
    slope_degrees,
    validate_elevation,
)
from marsdata.process.visual import class_colors, class_texture, legend, ortho_texture
from marsdata.region import REPO_DIR, Region

# Optional continuous layers; each one is normalized to 0–1 (high = firmer / more value).
CONTINUOUS_KEYS = ("thermal_inertia", "ice", "minerals")
# Texels per grid cell in the class textures: the edge of each class looks finer.
CLASS_TEXTURE_SCALE = 2


@dataclass
class BuildResult:
    grids: dict[str, np.ndarray]
    layer_meta: dict[str, dict] = field(default_factory=dict)
    # Classes of the categorical layer at the texture resolution, for the 3D view.
    classes: ClassCounts | None = None
    class_info: list[ClassInfo] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)  # sources with no file in data/raw
    # Visual only: RGBA layers already colored, their legend and the orthophoto (uint8, grayscale).
    textures: dict[str, np.ndarray] = field(default_factory=dict)
    legends: dict[str, list[dict]] = field(default_factory=dict)
    ortho: np.ndarray | None = None


def _stats(raw: np.ndarray) -> dict[str, float]:
    v = raw[np.isfinite(raw)]
    if v.size == 0:
        return {}
    p5, p50, p95 = np.percentile(v, [5, 50, 95])
    return {"raw_p5": float(p5), "raw_median": float(p50), "raw_p95": float(p95)}


def build_region(region: Region) -> BuildResult:
    dem_path = raw_path(region, "dem")
    dem_raw = warp_to_region(dem_path, region, Resampling.average)
    validate_elevation(dem_path, dem_raw)
    dem_coverage = coverage(dem_raw)
    dem = fill_nearest(dem_raw)
    dy, dx = region.cell_size_m
    result = BuildResult(grids={"dem": dem, "slope": slope_degrees(dem, dy, dx)})
    result.layer_meta["dem"] = {"coverage": dem_coverage, "fill": "nearest"}
    result.layer_meta["slope"] = {"coverage": dem_coverage, "cell_size_m": [dy, dx]}

    if "hazard" in region.sources:
        path = raw_path(region, "hazard")
        if not path.exists():
            result.missing.append("hazard")
        elif region.hazard_table:
            _categorical_hazard(region, path, result)
        else:
            raw = warp_to_region(path, region, Resampling.average)
            result.layer_meta["hazard"] = {"coverage": coverage(raw), "fill": "nearest"}
            result.grids["hazard"] = normalize(fill_nearest(raw))
    elif region.hazard_proxy == "roughness":
        _roughness_hazard(region, dem_path, result)

    for key in CONTINUOUS_KEYS:
        if key not in region.sources:
            continue
        path = raw_path(region, key)
        if not path.exists():
            result.missing.append(key)
            continue
        raw = warp_to_region(path, region, Resampling.bilinear)
        result.layer_meta[key] = {
            "coverage": coverage(raw),
            "fill": "nearest",
            "normalization": "percentiles 2 to 98 of the region",
            **_stats(raw),
        }
        result.grids[key] = normalize(fill_nearest(raw))

    if "ortho" in region.sources:
        path = raw_path(region, "ortho")
        if path.exists():
            result.ortho = ortho_texture(path, region)
        else:
            result.missing.append("ortho")

    return result


def _roughness_hazard(region: Region, dem_path, result: BuildResult) -> None:
    """Risk where there is no terrain classification: DEM roughness, relative to the region."""
    rms = roughness_to_region(dem_path, region)
    result.layer_meta["hazard"] = {
        "provenance": "derived",
        "source": region.sources["dem"],
        "coverage": coverage(rms),
        "fill": "nearest",
        "method": (
            "roughness: per-cell RMS of the DEM minus its smoothed version "
            f"(gaussiana de {ROUGHNESS_SIGMA_M:g} m)"
        ),
        "units": "m",
        "normalization": "percentiles 2 to 98 of the region",
        **_stats(rms),
    }
    result.grids["hazard"] = normalize(fill_nearest(rms))


def _categorical_hazard(region: Region, path, result: BuildResult) -> None:
    info = load_risk_table(REPO_DIR / region.hazard_table)
    codes = tuple(c.code for c in info)
    n, s = region.size, CLASS_TEXTURE_SCALE
    counts = count_classes(
        path,
        {"grid": ((n, n), region.grid_bounds), "texture": ((n * s, n * s), region.bbox)},
        codes,
    )
    grid = counts["grid"]
    hazard = grid.mean({c.code: c.risk for c in info})
    impassable = grid.fraction([c.code for c in info if c.risk >= 1.0])
    cov = float(grid.valid.mean())
    table = region.hazard_table
    result.grids["hazard"] = fill_nearest(hazard)
    result.grids["impassable_fraction"] = fill_nearest(impassable)
    result.layer_meta["hazard"] = {
        "provenance": "modeled",
        "coverage": cov,
        "fill": "nearest",
        "risk_table": table,
    }
    result.layer_meta["impassable_fraction"] = {
        "coverage": cov,
        "fill": "nearest",
        "classes": [c.name for c in info if c.risk >= 1.0],
        "risk_table": table,
    }
    result.classes = counts["texture"]
    result.class_info = info
    colors = class_colors(info)
    result.textures["terrain_class"] = class_texture(counts["texture"], colors)
    result.legends["terrain_class"] = legend(info, colors, counts["texture"])
    result.layer_meta["terrain_class"] = {
        "coverage": cov,
        "kind": "categorical",
        "classes": [c.name for c in info],
    }
