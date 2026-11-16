"""Source download and cropping, without network: the crop runs on a local GeoTIFF."""

import math

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from marsdata.fetch import sources
from marsdata.fetch.mmgis import traverse_with_sols, write_feature_collection
from marsdata.fetch.sources import FetchStatus, Product, crop_window, fetch_region
from marsdata.process.traverse import load_points
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
    """100 m mosaic covering 77 to 78 E and 18 to 19 N; each pixel holds its row number."""
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
        # The crop covers the bbox plus the margin, rounded to 100 m pixels.
        assert left <= _m(77.25) + 100 and right >= _m(77.65) - 100
        assert bottom <= _m(18.25) + 100 and top >= _m(18.65) - 100
        assert right - left < _m(0.42) and top - bottom < _m(0.42)
        # The values are the mosaic's: the first row of the crop is the northern edge row.
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


def test_crop_window_decimates_by_averaging_blocks(region, mosaic, tmp_path):
    full = crop_window(str(mosaic), region, tmp_path / "full.tif", margin_deg=0.05)
    small = crop_window(str(mosaic), region, tmp_path / "small.tif", margin_deg=0.05, decimate=4)
    with rasterio.open(full) as a, rasterio.open(small) as b:
        assert b.width == math.ceil(a.width / 4) and b.height == math.ceil(a.height / 4)
        # It covers the same as the full crop: if the width is not a multiple of 4, the
        # reduced pixel ends up a bit smaller than 4 original pixels.
        assert tuple(b.bounds) == pytest.approx(tuple(a.bounds))
        assert 3.9 < b.res[0] / a.res[0] <= 4
        # Each pixel averages a ~4 × 4 block: the first reduced row is the mean of 4 rows.
        assert b.read(1)[0, 0] == pytest.approx(a.read(1)[:4, 0].mean(), abs=0.1)


def test_fetch_region_skips_existing_and_reports_manual(region, tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "RAW_DIR", tmp_path)
    calls = []
    monkeypatch.setattr(sources, "download", lambda url, dest: calls.append(("download", url)))
    monkeypatch.setattr(
        sources,
        "crop_window",
        lambda src, reg, dest, margin, decimate: calls.append(("crop", src)),
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


def _wp(lon: float, lat: float, sol: int) -> dict:
    return {"properties": {"lon": lon, "lat": lat, "sol": sol}}


def _line(*points) -> dict:
    return {"type": "LineString", "coordinates": [[lon, lat, -4000.0] for lon, lat in points]}


# Points 0.001° (~59 m) apart on the same latitude.
A, B, C, D, E, G = ((137.400 + 0.001 * i, -4.80) for i in range(6))


@pytest.fixture
def legs() -> tuple[dict, dict]:
    """Curiosity-style MMGIS traverse (no sol) and its waypoints."""
    multi = {
        "type": "MultiLineString",
        "coordinates": [_line(A, B)["coordinates"], _line(B, C)["coordinates"]],
    }
    traverse = {
        "features": [
            {"properties": {"Length": 118.0}, "geometry": multi},
            {"properties": {"Length": 59.0}, "geometry": _line(C, D)},
            {"properties": {"Length": 59.0}, "geometry": _line(D, E)},  # waypoint with a lower sol
            {"properties": {"Length": 59.0}, "geometry": _line(E, G)},  # no waypoint
        ]
    }
    return traverse, {"features": [_wp(*C, 10), _wp(*D, 12), _wp(*E, 11)]}


def test_traverse_with_sols_takes_the_sol_of_the_waypoint_where_each_leg_ends(legs):
    fc = traverse_with_sols(*legs)

    # The sol never decreases, and a segment with no waypoint inherits the previous one.
    assert [f["properties"]["sol"] for f in fc["features"]] == [10, 12, 12, 12]
    assert {f["geometry"]["type"] for f in fc["features"]} == {"LineString"}
    first = fc["features"][0]
    assert [c[:2] for c in first["geometry"]["coordinates"]] == [list(A), list(B), list(C)]
    assert first["properties"]["length_m"] == 118.0


def test_traverse_with_sols_is_read_by_the_build(legs, tmp_path):
    path = tmp_path / "MSL_traverse.json"
    write_feature_collection({**traverse_with_sols(*legs), "name": "prueba"}, path)

    points = load_points(path)

    assert points[0] == (*A, 10)
    assert [p[:2] for p in points] == [A, B, C, D, E, G]
    assert points[-1][2] == 12
