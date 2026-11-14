"""Descarga y recorte de fuentes, sin red: el recorte corre sobre un GeoTIFF local."""

import math

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from marsdata.fetch import sources
from marsdata.fetch.sources import FetchStatus, Product, crop_window, fetch_region
from marsdata.region import Region

R = 3_396_190.0
EQC = f"+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +R={R} +units=m +no_defs"


def _m(deg: float) -> float:
    return math.radians(deg) * R


@pytest.fixture
def region() -> Region:
    return Region(
        id="test",
        name="Prueba",
        bbox=(77.30, 18.30, 77.60, 18.60),
        size=64,
        base={"lat": 18.45, "lon": 77.45},
        sources={"dem": "dem.tif", "ortho": "ortho.tif", "hazard": "hazard.tif"},
    )


@pytest.fixture
def mosaic(tmp_path):
    """Mosaico de 100 m que cubre de 77 a 78 E y de 18 a 19 N; cada píxel vale su número de fila."""
    res = 100.0
    width, height = int((_m(78) - _m(77)) / res), int((_m(19) - _m(18)) / res)
    path = tmp_path / "mosaic.tif"
    data = np.repeat(np.arange(height, dtype=np.float32)[:, None], width, axis=1)
    with rasterio.open(
        path, "w", driver="GTiff", width=width, height=height, count=1, dtype="float32",
        crs=EQC, transform=from_origin(_m(77), _m(19), res, res), nodata=-1.0,
    ) as dst:  # fmt: skip
        dst.write(data, 1)
    return path


def test_crop_window_covers_bbox_with_margin(region, mosaic, tmp_path):
    out = crop_window(str(mosaic), region, tmp_path / "crop.tif", margin_deg=0.05)
    with rasterio.open(out) as crop:
        left, bottom, right, top = crop.bounds
        assert crop.crs.to_dict()["R"] == R
        assert crop.nodata == -1.0
        # El recorte cubre el bbox más el margen, redondeado a píxeles de 100 m.
        assert left <= _m(77.25) + 100 and right >= _m(77.65) - 100
        assert bottom <= _m(18.25) + 100 and top >= _m(18.65) - 100
        assert right - left < _m(0.42) and top - bottom < _m(0.42)
        # Los valores son los del mosaico: la primera fila del recorte es la fila del borde norte.
        first_row = crop.read(1)[0, 0]
        assert first_row == pytest.approx(round((_m(19) - top) / 100), abs=1)


def test_crop_window_clips_to_the_mosaic(region, mosaic, tmp_path):
    far = Region(
        id="borde", name="Borde", bbox=(77.90, 18.90, 77.99, 18.99), size=32,
        base={"lat": 18.95, "lon": 77.95},
    )  # fmt: skip
    out = crop_window(str(mosaic), far, tmp_path / "edge.tif", margin_deg=0.05)
    with rasterio.open(out) as crop:
        assert crop.bounds.right <= _m(78) + 1e-6
        assert crop.bounds.top <= _m(19) + 1e-6


def test_fetch_region_skips_existing_and_reports_manual(region, tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "RAW_DIR", tmp_path)
    calls = []
    monkeypatch.setattr(sources, "download", lambda url, dest: calls.append(("download", url)))
    monkeypatch.setattr(
        sources, "crop_window", lambda src, reg, dest, margin: calls.append(("crop", src))
    )
    monkeypatch.setattr(
        sources,
        "PRODUCTS",
        {"test": {"dem": Product("https://x/dem.tif"), "ortho": Product("https://x/o.cub", True)}},
    )
    (tmp_path / "test").mkdir()
    (tmp_path / "test" / "dem.tif").write_bytes(b"ya estaba")

    status = fetch_region(region)

    assert status == {
        "dem": FetchStatus.present,
        "ortho": FetchStatus.cropped,
        "hazard": FetchStatus.manual,
    }
    assert calls == [("crop", "/vsicurl/https://x/o.cub")]
