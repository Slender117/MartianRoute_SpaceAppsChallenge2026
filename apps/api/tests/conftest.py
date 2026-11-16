import json

import numpy as np
import pytest

from app.config import get_settings
from app.schemas.region import RegionManifest
from app.schemas.route import LatLon
from app.storage import RegionGrids, load_manifest, load_region

SIZE = 60
ROVER_TRACK = [[0.1, 0.9], [0.5, 0.9], [0.9, 0.9]]  # (lon, lat)


def _manifest() -> RegionManifest:
    return RegionManifest(
        id="test",
        name="Región de prueba",
        bbox=(0.0, 0.0, 1.0, 1.0),
        shape=(SIZE, SIZE),
        resolution_m=50.0,
        elevation_range=(0.0, 0.0),
        base=LatLon(lat=0.5, lon=0.0),
        layers=["hazard", "thermal_inertia", "ice", "minerals"],
        traverses=["rover"],
    )


@pytest.fixture
def flat_grids() -> RegionGrids:
    """Flat terrain with a steep wall in the central column and a gap at the bottom."""
    zeros = np.zeros((SIZE, SIZE), dtype=np.float32)
    slope = zeros.copy()
    slope[: SIZE - 8, SIZE // 2] = 45.0
    return RegionGrids(
        manifest=_manifest(),
        dem=zeros.copy(),
        slope=slope,
        hazard=zeros.copy(),
        thermal_inertia=np.ones_like(zeros),
        ice=zeros.copy(),
        minerals=zeros.copy(),
    )


@pytest.fixture
def assets_dir(tmp_path, monkeypatch, flat_grids):
    """Writes the test region to disk and points the API at it."""
    region = tmp_path / "test"
    (region / "layers").mkdir(parents=True)
    (region / "traverses").mkdir()
    (tmp_path / "index.json").write_text(json.dumps({"regions": ["test"]}), encoding="utf-8")
    (region / "manifest.json").write_text(flat_grids.manifest.model_dump_json(), encoding="utf-8")
    np.save(region / "dem.npy", flat_grids.dem)
    np.save(region / "slope.npy", flat_grids.slope)
    for name in ("hazard", "thermal_inertia", "ice", "minerals"):
        np.save(region / "layers" / f"{name}.npy", getattr(flat_grids, name))
    track = {
        "type": "Feature",
        "properties": {"rover": "rover"},
        "geometry": {"type": "LineString", "coordinates": ROVER_TRACK},
    }
    (region / "traverses" / "rover.geojson").write_text(json.dumps(track), encoding="utf-8")

    monkeypatch.setenv("ASSETS_DIR", str(tmp_path))
    for cached in (get_settings, load_manifest, load_region):
        cached.cache_clear()
    yield tmp_path
    for cached in (get_settings, load_manifest, load_region):
        cached.cache_clear()
