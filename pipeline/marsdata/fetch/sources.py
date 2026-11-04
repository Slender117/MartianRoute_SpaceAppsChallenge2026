"""Descarga de productos de NASA a data/raw/<region>/.

Pendiente de implementar por el rol de datos geoespaciales. Cada función debe dejar
un GeoTIFF en la ruta que indica `sources` en config/regions.yaml.

Fuentes (verificar URLs y productos exactos antes de usarlos):
- MOLA MEGDR (elevación global):     PDS Geosciences Node
- CTX / HiRISE DTM (elevación local): PDS Imaging Node, HiRISE PDS (uahirise.org/dtm)
- THEMIS inercia térmica:            PDS Geosciences / ASU THEMIS
- CRISM parámetros de resumen:       PDS Geosciences Node
- SWIM (hielo subsuperficial):       swim.psi.edu
- Mosaicos y capas listas:           NASA Mars Trek (servicios WMTS)
"""

from pathlib import Path

import httpx

from marsdata.region import Region

RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


def raw_path(region: Region, key: str) -> Path:
    return RAW_DIR / region.id / region.sources[key]


def download(url: str, dest: Path) -> Path:
    """Descarga en streaming; no vuelve a bajar si el archivo ya existe."""
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", url, follow_redirects=True, timeout=None) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    return dest


def fetch_region(region: Region) -> None:
    # TODO(datos): mapear cada clave de `region.sources` a su producto en PDS/Trek/SWIM
    # y llamar a `download(url, raw_path(region, key))`.
    raise NotImplementedError(
        "Descarga real pendiente. Usa `marsdata synthetic` para trabajar con datos de prueba."
    )
