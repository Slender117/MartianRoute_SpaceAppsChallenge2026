"""Procesa los GeoTIFF crudos de una región y produce las grillas para la API."""

import numpy as np
from rasterio.warp import Resampling

from marsdata.fetch.sources import raw_path
from marsdata.process.reproject import fill_nodata, warp_to_region
from marsdata.process.terrain import normalize, slope_degrees
from marsdata.region import Region

# Capas opcionales; cada una se normaliza a 0–1 (alto = más riesgo / más firme / más valor).
LAYER_KEYS = ("hazard", "thermal_inertia", "ice", "minerals")


def build_region(region: Region) -> dict[str, np.ndarray]:
    dem = fill_nodata(warp_to_region(raw_path(region, "dem"), region))
    grids = {"dem": dem, "slope": slope_degrees(dem, region.resolution_m)}

    for key in LAYER_KEYS:
        if key not in region.sources:
            continue
        raw = warp_to_region(raw_path(region, key), region, Resampling.average)
        grids[key] = normalize(fill_nodata(raw))

    return grids
