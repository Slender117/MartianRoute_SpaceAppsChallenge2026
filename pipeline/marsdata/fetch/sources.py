"""Downloads NASA and USGS products into data/raw/<region>/.

data/raw/ is versioned with each region's files: this is only needed to regenerate them or to
add a region, and it does not repeat what is already on disk.

Each `sources` key in config/regions.yaml (dem, ortho, thermal_inertia...) is resolved with
this file's PRODUCTS catalog. A product is downloaded whole or, if it is a large mosaic, only
the region's window is read from the remote file (GDAL only requests the blocks it needs).
Keys with no product in the catalog are placed by hand in data/raw/<region>/.

The citations of each product are in docs/creditos.md.
"""

import math
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import httpx

from marsdata.region import Region

RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"

USGS_TRN = "https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX"
USGS_TRN_HIRISE = "https://planetarymaps.usgs.gov/mosaic/mars2020_trn/HiRISE"
USGS_MSL = "https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/Mars/MSL"
THEMIS_TI = (
    "https://asc-astropedia.s3.us-west-2.amazonaws.com/Mars/Odyssey/"
    "THEMIS-Global-Thermal-Inertia-Mosaic/Quantitative-32-Bit"
)


@dataclass(frozen=True)
class Product:
    url: str
    # True: read only the bbox window (plus `margin_deg` per side) instead of downloading the file.
    window: bool = False
    # Margin so the step to the grid has neighbors at the region edge.
    margin_deg: float = 0.05
    # With window: average blocks of decimate × decimate pixels. For HiRISE mosaics of a whole
    # region, which would weigh gigabytes at full resolution.
    decimate: int = 1


PRODUCTS: dict[str, dict[str, Product]] = {
    "jezero": {
        # USGS (2020), doi:10.5066/P906QQT8. Float32, 20 m. Same set as the orthophoto.
        "dem": Product(
            f"{USGS_TRN}/JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif"
        ),
        # USGS (2020), doi:10.5066/P9GV1ND3. 8-bit, 6 m.
        "ortho": Product(f"{USGS_TRN}/JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0.tif"),
        # USGS, ASU and NASA (2014). Float32, 100 m. Tile 00N060E weighs 2.5 GB: window only.
        "thermal_inertia": Product(
            f"{THEMIS_TI}/THEMIS_TI_Mosaic_Quant_00N060E_100mpp.cub", window=True
        ),
        # hazard: NOAH-H mosaic (Wright et al., 2022), 7.4 GB; copied by hand.
    },
    "jezero_walk": {
        # USGS (2020), doi:10.5066/P9REJ9JN. Float32, 1 m; the full file weighs 1.8 GB.
        "dem": Product(
            f"{USGS_TRN_HIRISE}/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif",
            window=True,
            margin_deg=0.003,
        ),
        # USGS (2020), doi:10.5066/P9QJDP48. 8-bit, 25 cm; the full file weighs 6.9 GB.
        "ortho": Product(
            f"{USGS_TRN_HIRISE}/JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first.tif",
            window=True,
            margin_deg=0.003,
        ),
        "thermal_inertia": Product(
            f"{THEMIS_TI}/THEMIS_TI_Mosaic_Quant_00N060E_100mpp.cub", window=True, margin_deg=0.01
        ),
    },
    "gale": {
        # Calef and Parker (2016), USGS. HiRISE DEM, Float32, 1 m; 3.9 GB in full. Taken at 5 m.
        "dem": Product(
            f"{USGS_MSL}/MSL_Gale_DEM_Mosaic_1m_v3.tif", window=True, margin_deg=0.02, decimate=5
        ),
        # Calef and Parker (2016), USGS. HiRISE orthomosaic, 8-bit, 25 cm; 24 GB in full. At 5 m.
        "ortho": Product(
            f"{USGS_MSL}/MSL_Gale_Orthophoto_Mosaic_25cm_v3.tif",
            window=True,
            margin_deg=0.02,
            decimate=20,
        ),
        # USGS, ASU and NASA (2014). The tile that covers Gale (30° S to 0°, 120° E to 180° E).
        "thermal_inertia": Product(
            f"{THEMIS_TI}/THEMIS_TI_Mosaic_Quant_30S120E_100mpp.cub", window=True
        ),
        # hazard: there is no NOAH-H for Gale.
    },
}


class FetchStatus(StrEnum):
    downloaded = "descargado"
    cropped = "recortado"
    present = "ya existe"
    manual = "no product: place it by hand"


def raw_path(region: Region, key: str) -> Path:
    return RAW_DIR / region.id / region.sources[key]


def download(url: str, dest: Path) -> Path:
    """Streams the download to a temporary file and renames it when finished."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    with httpx.stream("GET", url, follow_redirects=True, timeout=None) as r:
        r.raise_for_status()
        with part.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    part.replace(dest)
    return dest


def crop_window(
    src_path: str, region: Region, dest: Path, margin_deg: float = 0.05, decimate: int = 1
) -> Path:
    """Saves as GeoTIFF the window of the region bbox (plus the margin) from `src_path`.

    `src_path` can be local or remote (`/vsicurl/https://...`). It keeps CRS, dtype and nodata. With
    `decimate` > 1 averages blocks of decimate × decimate pixels; if the mosaic has overviews
    (.ovr), GDAL reads from them and does not download the full resolution.
    """
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import Affine
    from rasterio.warp import transform_bounds
    from rasterio.windows import Window, from_bounds

    from marsdata.process.reproject import geographic_crs

    lon_min, lat_min, lon_max, lat_max = region.bbox
    # EMPTY_DIR avoids listing the remote folder; YES lets GDAL find the mosaic's .ovr.
    readdir = "EMPTY_DIR" if decimate == 1 else "YES"
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN=readdir), rasterio.open(src_path) as src:
        bounds = transform_bounds(
            geographic_crs(src.crs),
            src.crs,
            lon_min - margin_deg,
            lat_min - margin_deg,
            lon_max + margin_deg,
            lat_max + margin_deg,
        )
        win = from_bounds(*bounds, src.transform).round_offsets().round_lengths()
        win = win.intersection(Window(0, 0, src.width, src.height))
        transform = src.window_transform(win)
        if decimate == 1:
            data = src.read(1, window=win)
        else:
            shape = (math.ceil(win.height / decimate), math.ceil(win.width / decimate))
            data = src.read(1, window=win, out_shape=shape, resampling=Resampling.average)
            transform = transform @ Affine.scale(win.width / shape[1], win.height / shape[0])
        profile = {
            "driver": "GTiff",
            "width": data.shape[1],
            "height": data.shape[0],
            "count": 1,
            "dtype": data.dtype,
            "crs": src.crs,
            "transform": transform,
            "nodata": src.nodata,
            "compress": "deflate",
        }

    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    with rasterio.open(part, "w", **profile) as dst:
        dst.write(data, 1)
    part.replace(dest)
    return dest


def fetch_region(region: Region) -> dict[str, FetchStatus]:
    """Downloads or crops each source of the region; skips the ones already on disk."""
    catalog = PRODUCTS.get(region.id, {})
    status = {}
    for key in region.sources:
        dest = raw_path(region, key)
        product = catalog.get(key)
        if dest.exists():
            status[key] = FetchStatus.present
        elif product is None:
            status[key] = FetchStatus.manual
        elif product.window:
            crop_window(
                f"/vsicurl/{product.url}", region, dest, product.margin_deg, product.decimate
            )
            status[key] = FetchStatus.cropped
        else:
            download(product.url, dest)
            status[key] = FetchStatus.downloaded
    return status
