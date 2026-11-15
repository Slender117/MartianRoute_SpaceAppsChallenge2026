"""Descarga de productos de NASA y USGS a data/raw/<region>/.

data/raw/ se versiona con los archivos de cada región: esto solo hace falta para regenerarlos o para
agregar una región, y no repite lo que ya está en disco.

Cada clave de `sources` en config/regions.yaml (dem, ortho, thermal_inertia...) se resuelve con
el catálogo PRODUCTS de este archivo. Un producto se baja completo o, si es un mosaico grande, se
lee solo la ventana de la región desde el archivo remoto (GDAL pide únicamente los bloques
necesarios). Las claves sin producto en el catálogo se colocan a mano en data/raw/<region>/.

Las citas de cada producto están en docs/creditos.md.
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
    # True: leer solo la ventana del bbox (más `margin_deg` por lado) en vez de bajar el archivo.
    window: bool = False
    # Margen para que el paso a la grilla tenga vecinos en el borde de la región.
    margin_deg: float = 0.05
    # Con window: promediar bloques de decimate × decimate píxeles. Para mosaicos de HiRISE de una
    # región entera, que a resolución completa pesarían gigabytes.
    decimate: int = 1


PRODUCTS: dict[str, dict[str, Product]] = {
    "jezero": {
        # USGS (2020), doi:10.5066/P906QQT8. Float32, 20 m. Mismo conjunto que la ortofoto.
        "dem": Product(
            f"{USGS_TRN}/JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif"
        ),
        # USGS (2020), doi:10.5066/P9GV1ND3. 8 bits, 6 m.
        "ortho": Product(f"{USGS_TRN}/JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0.tif"),
        # USGS, ASU y NASA (2014). Float32, 100 m. El tile 00N060E pesa 2.5 GB: solo la ventana.
        "thermal_inertia": Product(
            f"{THEMIS_TI}/THEMIS_TI_Mosaic_Quant_00N060E_100mpp.cub", window=True
        ),
        # hazard: mosaico NOAH-H (Wright et al., 2022), 7.4 GB; se copia a mano.
    },
    "jezero_walk": {
        # USGS (2020), doi:10.5066/P9REJ9JN. Float32, 1 m; el archivo completo pesa 1.8 GB.
        "dem": Product(
            f"{USGS_TRN_HIRISE}/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif",
            window=True,
            margin_deg=0.003,
        ),
        # USGS (2020), doi:10.5066/P9QJDP48. 8 bits, 25 cm; el archivo completo pesa 6.9 GB.
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
        # Calef y Parker (2016), USGS. DEM de HiRISE, Float32, 1 m; 3.9 GB completo. Se baja a 5 m.
        "dem": Product(
            f"{USGS_MSL}/MSL_Gale_DEM_Mosaic_1m_v3.tif", window=True, margin_deg=0.02, decimate=5
        ),
        # Calef y Parker (2016), USGS. Ortomosaico de HiRISE, 8 bits, 25 cm; 24 GB completo. A 5 m.
        "ortho": Product(
            f"{USGS_MSL}/MSL_Gale_Orthophoto_Mosaic_25cm_v3.tif",
            window=True,
            margin_deg=0.02,
            decimate=20,
        ),
        # USGS, ASU y NASA (2014). El tile que cubre Gale (30° S a 0°, 120° E a 180° E).
        "thermal_inertia": Product(
            f"{THEMIS_TI}/THEMIS_TI_Mosaic_Quant_30S120E_100mpp.cub", window=True
        ),
        # hazard: no hay NOAH-H de Gale.
    },
}


class FetchStatus(StrEnum):
    downloaded = "descargado"
    cropped = "recortado"
    present = "ya existe"
    manual = "sin producto: colocarlo a mano"


def raw_path(region: Region, key: str) -> Path:
    return RAW_DIR / region.id / region.sources[key]


def download(url: str, dest: Path) -> Path:
    """Descarga en streaming a un archivo temporal y lo renombra al terminar."""
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
    """Guarda como GeoTIFF la ventana del bbox de la región (más el margen) de `src_path`.

    `src_path` puede ser local o remoto (`/vsicurl/https://...`). Conserva CRS, tipo y nodata. Con
    `decimate` > 1 promedia bloques de decimate × decimate píxeles; si el mosaico tiene vistas
    reducidas (.ovr), GDAL lee de ellas y no baja la resolución completa.
    """
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import Affine
    from rasterio.warp import transform_bounds
    from rasterio.windows import Window, from_bounds

    from marsdata.process.reproject import geographic_crs

    lon_min, lat_min, lon_max, lat_max = region.bbox
    # EMPTY_DIR evita listar la carpeta remota; YES deja que GDAL encuentre el .ovr del mosaico.
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
    """Baja o recorta cada fuente de la región; no repite las que ya están en disco."""
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
