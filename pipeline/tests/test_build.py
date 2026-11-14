"""Build de una región real con rásteres pequeños escritos en la prueba (sin descargas)."""

import json
import math

import numpy as np
import pytest
import rasterio
from PIL import Image
from rasterio.transform import from_origin

from marsdata.export import write_region
from marsdata.fetch import sources
from marsdata.process.build import build_region
from marsdata.process.classes import ClassCounts, ClassInfo, count_classes, load_risk_table
from marsdata.process.reproject import fill_nearest, warp_to_region
from marsdata.process.terrain import (
    ElevationError,
    local_relief,
    slope_degrees,
    validate_elevation,
)
from marsdata.process.traverse import build_traverse, continuous_runs, load_points
from marsdata.process.visual import (
    CLASS_ALPHA,
    ORTHO_PX_PER_CELL,
    class_texture,
    legend,
    ortho_texture,
)
from marsdata.region import MARS_RADIUS_M, Region

R = 3_396_190.0  # esfera de los mosaicos de USGS y NOAH-H
EQC = f"+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +R={R} +units=m +no_defs"
BBOX = (77.30, 18.30, 77.40, 18.40)
WEST, NORTH = 77.28, 18.42  # los rásteres de prueba cubren el bbox con margen
SIZE = 21  # celdas por lado: medio paso de 0.0025°


def _m(deg: float) -> float:
    return math.radians(deg) * R


def _write(path, data, res, nodata=None):
    with rasterio.open(
        path, "w", driver="GTiff", width=data.shape[1], height=data.shape[0], count=1,
        dtype=data.dtype, crs=EQC, transform=from_origin(_m(WEST), _m(NORTH), res, res),
        nodata=nodata,
    ) as dst:  # fmt: skip
        dst.write(data, 1)
    return path


def _lon_lat(shape, res):
    rows, cols = np.mgrid[0 : shape[0], 0 : shape[1]]
    lon = np.degrees((_m(WEST) + (cols + 0.5) * res) / R)
    lat = np.degrees((_m(NORTH) - (rows + 0.5) * res) / R)
    return lon, lat


def _noahh(path):
    """Mitad oeste roca madre (2, riesgo 0), mitad este ondulaciones grandes (5, riesgo 1) y una
    franja norte sin clase (127, nodata)."""
    shape = (900, 900)
    lon, lat = _lon_lat(shape, 10.0)
    data = np.where(lon < 77.35, 2, 5).astype(np.uint8)
    data[lat > 18.38] = 127
    return _write(path, data, 10.0, nodata=127)


@pytest.fixture
def risk_table(tmp_path):
    path = tmp_path / "riesgo.csv"
    path.write_text(
        "ig_value,grupo,riesgo\n0,Sin dato,\n1,No roca madre,0.25\n2,Roca madre,0.00\n"
        "3,Campos de rocas,0.50\n4,Ondulaciones pequeñas,0.75\n5,Ondulaciones grandes,1.00\n"
        "127,Nodata,\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def region(tmp_path, monkeypatch, risk_table):
    monkeypatch.setattr(sources, "RAW_DIR", tmp_path)
    (tmp_path / "t").mkdir()
    return Region(
        id="t",
        name="Prueba",
        bbox=BBOX,
        size=SIZE,
        base={"lat": 18.35, "lon": 77.35},
        sources={
            "dem": "dem.tif",
            "hazard": "noahh.tif",
            "thermal_inertia": "ti.tif",
            "minerals": "no_existe.tif",
        },
        hazard_table=str(risk_table),
    )


def test_warp_puts_row_0_and_col_0_on_the_bbox_like_the_api(region, tmp_path):
    shape, res = (90, 90), 100.0
    lon, lat = _lon_lat(shape, res)
    lon_grid = warp_to_region(_write(tmp_path / "lon.tif", lon.astype(np.float32), res), region)
    lat_grid = warp_to_region(_write(tmp_path / "lat.tif", lat.astype(np.float32), res), region)
    assert lon_grid[:, 0] == pytest.approx(77.30, abs=2e-4)
    assert lon_grid[:, -1] == pytest.approx(77.40, abs=2e-4)
    assert lat_grid[0, :] == pytest.approx(18.40, abs=2e-4)
    assert lat_grid[-1, :] == pytest.approx(18.30, abs=2e-4)


def test_validate_elevation_rejects_images_and_impossible_heights(tmp_path):
    flat = np.full((4, 4), -2500, dtype=np.float32)
    validate_elevation(_write(tmp_path / "ok.tif", flat, 20.0), flat)
    image = np.full((4, 4), 200, dtype=np.uint8)
    with pytest.raises(ElevationError, match="uint8"):
        validate_elevation(_write(tmp_path / "img.tif", image, 20.0), image.astype(np.float32))
    tall = np.full((4, 4), 30_000, dtype=np.float32)
    with pytest.raises(ElevationError, match="fuera del rango"):
        validate_elevation(_write(tmp_path / "alto.tif", tall, 20.0), tall)


def test_slope_uses_the_real_side_of_the_cell_in_each_direction():
    dem = np.tile(np.arange(10, dtype=np.float64), (10, 1))  # sube 1 m por columna
    assert slope_degrees(dem, dy_m=20.0, dx_m=10.0)[5, 5] == pytest.approx(
        math.degrees(math.atan(0.1))
    )
    assert slope_degrees(dem, dy_m=20.0)[5, 5] == pytest.approx(math.degrees(math.atan(0.05)))


def test_fill_nearest_copies_the_closest_cell_with_data():
    grid = np.array([[1.0, 2.0, np.nan], [4.0, np.nan, np.nan]])
    assert fill_nearest(grid).tolist() == [[1.0, 2.0, 2.0], [4.0, 4.0, 2.0]]
    with pytest.raises(ValueError):
        fill_nearest(np.full((2, 2), np.nan))


def test_count_classes_gives_risk_fraction_and_dominant_class(region, risk_table, tmp_path):
    info = load_risk_table(risk_table)
    assert [c.code for c in info] == [1, 2, 3, 4, 5]
    path = _noahh(tmp_path / "noahh.tif")
    grid = count_classes(path, {"grid": ((SIZE, SIZE), region.grid_bounds)}, (1, 2, 3, 4, 5))[
        "grid"
    ]

    hazard = grid.mean({c.code: c.risk for c in info})
    impassable = grid.fraction([5])
    south = SIZE - 2
    assert hazard[south, 2] == pytest.approx(0.0)  # oeste: roca madre
    assert hazard[south, SIZE - 3] == pytest.approx(1.0)  # este: ondulaciones grandes
    assert 0.3 < hazard[south, SIZE // 2] < 0.7  # la celda central cae sobre el límite
    assert impassable[south, SIZE - 3] == pytest.approx(1.0)
    assert np.isnan(hazard[0, 5])  # franja norte sin clase
    assert grid.dominant()[south, 2] == 2 and grid.dominant()[south, SIZE - 3] == 5
    assert grid.dominant()[0, 5] == 0
    # La franja sin clase va de 18.38 al borde norte de la grilla (18.4025).
    lon0, lat0, lon1, lat1 = region.grid_bounds
    assert grid.valid.mean() == pytest.approx((18.38 - lat0) / (lat1 - lat0), abs=0.03)


def test_build_region_measures_coverage_before_filling(region, tmp_path):
    shape, res = (90, 90), 100.0
    lon, _ = _lon_lat(shape, res)
    dem = (-2500 + (lon - WEST) * 1000).astype(np.float32)
    dem[40:44, 40:44] = -3.4e38  # hueco dentro de la región
    _write(tmp_path / "t" / "dem.tif", dem, res, nodata=-3.4e38)
    _noahh(tmp_path / "t" / "noahh.tif")
    ti = np.linspace(150, 450, 30 * 30, dtype=np.float32).reshape(30, 30)
    _write(tmp_path / "t" / "ti.tif", ti, 300.0)

    result = build_region(region)

    assert set(result.grids) == {"dem", "slope", "hazard", "impassable_fraction", "thermal_inertia"}
    for name, grid in result.grids.items():
        assert grid.shape == (SIZE, SIZE), name
        assert np.isfinite(grid).all(), name
    assert 0.9 < result.layer_meta["dem"]["coverage"] < 1.0
    assert result.layer_meta["hazard"]["coverage"] == pytest.approx(0.79, abs=0.03)
    assert result.layer_meta["hazard"]["provenance"] == "modeled"
    assert result.layer_meta["thermal_inertia"]["coverage"] == pytest.approx(1.0)
    assert 150 <= result.layer_meta["thermal_inertia"]["raw_median"] <= 450
    assert result.grids["thermal_inertia"].min() >= 0 and result.grids["thermal_inertia"].max() <= 1
    assert result.missing == ["minerals"]
    assert result.classes.counts.shape == (5, 2 * SIZE, 2 * SIZE)


def _mmgis(path, sols):
    features = [
        {
            "type": "Feature",
            "properties": {"sol": sol},
            "geometry": {"type": "LineString", "coordinates": pts},
        }
        for sol, pts in sols
    ]
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8"
    )
    return path


def test_traverse_keeps_the_longest_continuous_run_with_dem_elevation(region, tmp_path):
    step = math.degrees(10.0 / (MARS_RADIUS_M * math.cos(math.radians(18.35))))  # 10 m al este
    long_run = [[77.32 + i * step, 18.35, -1.0] for i in range(60)]
    outside = [[77.45, 18.35, -1.0]]
    short_run = [[77.38 + i * step, 18.32, -1.0] for i in range(5)]
    path = _mmgis(tmp_path / "m20.json", [(2, outside + short_run), (1, long_run)])

    points = load_points(path)
    assert [p[2] for p in points[:2]] == [1, 1]  # ordenado por sol
    assert len(continuous_runs(points, BBOX)) == 2

    region.traverse_files = {"perseverance": str(path)}
    dem = np.tile(-2500 + np.arange(SIZE, dtype=np.float32), (SIZE, 1))  # +1 m por columna
    coords, props = build_traverse(region, dem, "perseverance")
    assert len(coords) == 60
    assert props["sol_min"] == props["sol_max"] == 1
    assert props["length_m"] == pytest.approx(590, rel=0.01)
    lat, lon, elev = coords[0]
    assert elev == pytest.approx(-2500 + (77.32 - 77.30) / 0.1 * (SIZE - 1), abs=0.01)


def test_traverse_gap_can_be_set_per_region(region, tmp_path):
    step = math.degrees(10.0 / (MARS_RADIUS_M * math.cos(math.radians(18.35))))  # 10 m al este
    first = [[77.32 + i * step, 18.35, -1.0] for i in range(20)]
    # 50 m después del último punto: un vértice ralo, como los del archivo de Curiosity.
    second = [[77.32 + (24 + i) * step, 18.35, -1.0] for i in range(20)]
    region.traverse_files = {"curiosity": str(_mmgis(tmp_path / "msl.json", [(1, first + second)]))}
    dem = np.full((SIZE, SIZE), -4000.0, np.float32)

    _, default = build_traverse(region, dem, "curiosity")
    region.traverse_max_gap_m = 60.0
    _, wider = build_traverse(region, dem, "curiosity")

    assert default["max_gap_m"] == 30.0 and default["length_m"] == pytest.approx(190, rel=0.02)
    assert wider["max_gap_m"] == 60.0 and wider["length_m"] == pytest.approx(430, rel=0.02)


def test_export_writes_elevation_and_coverage(region, tmp_path):
    grids = {
        "dem": np.full((SIZE, SIZE), -2500.0, np.float32),
        "slope": np.zeros((SIZE, SIZE), np.float32),
    }
    out = write_region(
        region,
        grids,
        {"perseverance": [(18.35, 77.32, -2498.0), (18.35, 77.33, -2497.5)]},
        out_dir=tmp_path / "out",
        layer_meta={"dem": {"coverage": 0.99}},
        traverse_properties={"perseverance": {"sol_min": 1}},
    )
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["layer_meta"]["dem"] == {
        "provenance": "derived",
        "source": "dem.tif",
        "coverage": 0.99,
    }
    geojson = json.loads((out / "traverses" / "perseverance.geojson").read_text(encoding="utf-8"))
    assert geojson["geometry"]["coordinates"][0] == [77.32, 18.35, -2498.0]
    assert geojson["properties"] == {"rover": "perseverance", "sol_min": 1}


# --- Archivos para la vista 3D ---


def test_heightmap_bin_is_float32_little_endian_with_row_0_north(region, tmp_path):
    dem = (-2600 + np.arange(SIZE, dtype=np.float32)[:, None] * np.ones(SIZE)).astype(np.float32)
    grids = {"dem": dem, "slope": np.zeros_like(dem)}
    out = write_region(region, grids, out_dir=tmp_path / "out")

    raw = np.fromfile(out / "heightmap.bin", dtype="<f4")
    assert raw.size == SIZE * SIZE
    assert np.array_equal(raw.reshape(SIZE, SIZE), dem)  # la primera fila es la del norte
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["assets"]["heightmap"] == {
        "path": "heightmap.bin",
        "dtype": "float32",
        "byte_order": "little",
        "shape": [SIZE, SIZE],
        "row0": "north",
    }
    assert "heightmap.bin" in manifest["checksums"]
    assert manifest["cell_size_m"][0] > manifest["cell_size_m"][1]  # el lado este-oeste es menor


def test_class_texture_blends_colors_and_hides_cells_without_class():
    counts = ClassCounts(
        codes=(1, 2),
        counts=np.array([[[0, 2, 0]], [[4, 2, 0]]], dtype=np.float32),  # (K=2, H=1, W=3)
        total=np.array([[4, 4, 4]], dtype=np.float32),
    )
    colors = {1: "#FF0000", 2: "#0000FF"}
    rgba = class_texture(counts, colors)
    assert rgba.shape == (1, 3, 4)
    assert rgba[0, 0].tolist() == [0, 0, 255, round(CLASS_ALPHA * 255)]  # todo clase 2
    assert rgba[0, 1].tolist() == [128, 0, 128, round(CLASS_ALPHA * 255)]  # mitad y mitad
    assert rgba[0, 2, 3] == 0  # sin clase: transparente
    info = [ClassInfo(1, "Uno", 0.0), ClassInfo(2, "Dos", 1.0)]
    shares = {item["code"]: item["share"] for item in legend(info, colors, counts)}
    assert shares == {1: pytest.approx(0.25), 2: pytest.approx(0.75)}


def test_ortho_texture_covers_the_bbox_north_up_with_stretched_contrast(region, tmp_path):
    shape, res = (300, 300), 30.0
    _, lat = _lon_lat(shape, res)
    gray = np.clip((lat - 18.28) / 0.14 * 200 + 20, 0, 255).astype(np.uint8)  # más claro al norte
    gray[140:160, 140:160] = 0  # hueco del mosaico en el centro
    region.sources["ortho"] = "ortho.tif"
    tex = ortho_texture(_write(tmp_path / "t" / "ortho.tif", gray, res, nodata=0), region)
    n = SIZE * ORTHO_PX_PER_CELL
    assert tex.shape == (n, n)
    assert tex[0].mean() > tex[-1].mean()  # norte arriba
    assert tex.min() <= 5 and tex.max() >= 250  # contraste estirado
    assert tex[n // 2, n // 2] > 60  # el hueco toma el gris vecino, no negro


def test_build_and_export_write_the_3d_files(region, tmp_path):
    shape, res = (90, 90), 100.0
    lon, lat = _lon_lat(shape, res)
    _write(tmp_path / "t" / "dem.tif", (-2500 + (lon - WEST) * 1000).astype(np.float32), res)
    _noahh(tmp_path / "t" / "noahh.tif")
    _write(tmp_path / "t" / "ti.tif", np.full((30, 30), 300, np.float32), 300.0)
    gray = np.clip((lat - 18.28) / 0.14 * 255, 0, 255).astype(np.uint8)
    _write(tmp_path / "t" / "ortho.tif", gray, res)
    region.sources["ortho"] = "ortho.tif"
    region.labels = [
        {"name": "Base", "lat": 18.35, "lon": 77.35, "source": "base"},
        {"name": "Solo sintética", "lat": 18.36, "lon": 77.36, "only": "synthetic"},
        {"name": "Solo real", "lat": 18.37, "lon": 77.37, "only": "real"},
    ]
    region.demo = {"start": {"lat": 18.35, "lon": 77.35}, "end": {"lat": 18.36, "lon": 77.36}}
    region.demo_real = {"start": {"lat": 18.35, "lon": 77.35}, "end": {"lat": 18.37, "lon": 77.37}}

    result = build_region(region)
    out = write_region(
        region,
        result.grids,
        {"perseverance": [(18.35, 77.32, -2480.0), (18.36, 77.33, -2470.0)]},
        out_dir=tmp_path / "out",
        layer_meta=result.layer_meta,
        traverse_properties={"perseverance": {"sol_min": 3, "sol_max": 9, "source": "m20.json"}},
        textures=result.textures,
        legends=result.legends,
        ortho=result.ortho,
    )

    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert "terrain_class" in manifest["layers"]
    assert not (out / "layers" / "terrain_class.npy").exists()  # solo visual
    with Image.open(out / "textures" / "terrain_class.png") as img:
        assert img.mode == "RGBA" and img.size == (2 * SIZE, 2 * SIZE)
    with Image.open(out / "textures" / "ortho.jpg") as img:
        assert img.mode == "L" and img.size == (4 * SIZE, 4 * SIZE)
    assert manifest["assets"]["ortho"]["path"] == "textures/ortho.jpg"
    names = [item["name"] for item in manifest["legends"]["terrain_class"]]
    assert names == ["No roca madre", "Roca madre", "Campos de rocas", "Ondulaciones pequeñas",
                     "Ondulaciones grandes"]  # fmt: skip
    labels = {item["name"]: item for item in manifest["labels"]}
    # La región real lleva sus etiquetas y su escenario de demo, no los de la sintética.
    assert set(labels) == {"Base", "Solo real", "Perseverance · sol 3", "Perseverance · sol 9"}
    assert "only" not in labels["Solo real"]
    assert manifest["demo"]["end"] == {"lat": 18.37, "lon": 77.37}
    assert labels["Perseverance · sol 9"]["kind"] == "traverse"
    assert "kind" not in labels["Base"]
    # La elevación de cada nombre sale del DEM: +10 m por cada 0.01° hacia el este.
    assert labels["Base"]["elev"] == pytest.approx(-2500 + (77.35 - WEST) * 1000, abs=1.5)
    assert manifest["layer_meta"]["terrain_class"]["kind"] == "categorical"


def test_synthetic_region_keeps_its_own_demo_and_labels(tmp_path):
    from marsdata.region import load_regions
    from marsdata.synthetic import make_grids

    jezero = load_regions()["jezero"]
    out = write_region(jezero, make_grids(jezero), out_dir=tmp_path, synthetic=True)
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["demo"] == jezero.demo
    names = {item["name"] for item in manifest["labels"]}
    assert "Destino de la demo" in names
    assert "Ahorro de O₂ por pendiente" not in names


def test_local_relief_ignores_even_slopes_and_measures_bumps():
    rows, cols = np.mgrid[0:80, 0:80]
    plane = (0.3 * cols + 0.1 * rows).astype(np.float32)  # pendiente pareja: sin relieve local
    assert np.abs(local_relief(plane, pixel_m=5.0)[10:-10, 10:-10]).max() < 1e-3

    bumps = plane.copy()
    checker = np.where((rows + cols) % 2 == 0, 1.0, -1.0)  # ±1 m cada 5 m
    bumps[40:60, 40:60] += checker[40:60, 40:60]
    relief = local_relief(bumps, pixel_m=5.0)
    assert np.sqrt(np.mean(relief[45:55, 45:55] ** 2)) > 0.5
    # Lejos de los bordes y de los bultos (la gaussiana llega a 4 σ = 8 píxeles), sigue en cero.
    assert np.abs(relief[10:30, 10:30]).max() < 1e-3


def test_build_region_derives_hazard_from_roughness_without_terrain_classes(region, tmp_path):
    region.sources = {"dem": "dem.tif"}
    region.hazard_table = None
    region.hazard_proxy = "roughness"
    shape, res = (900, 900), 10.0
    lon, _ = _lon_lat(shape, res)
    rows, cols = np.mgrid[0 : shape[0], 0 : shape[1]]
    dem = (-2500 + (lon - WEST) * 1000).astype(np.float32)
    rough = lon > 77.35  # mitad este con relieve de ±2 m entre píxeles vecinos
    dem[rough] += np.where((rows + cols) % 2 == 0, 2.0, -2.0)[rough]
    _write(tmp_path / "t" / "dem.tif", dem, res)

    result = build_region(region)

    meta = result.layer_meta["hazard"]
    assert meta["provenance"] == "derived" and meta["coverage"] == 1.0
    assert meta["source"] == "dem.tif"
    lon_grid = np.linspace(BBOX[0], BBOX[2], SIZE)
    hazard = result.grids["hazard"]
    assert hazard[:, lon_grid > 77.36].mean() > 0.9
    assert hazard[:, lon_grid < 77.34].mean() < 0.1


def test_every_region_has_its_base_inside_and_its_traverse_files():
    from marsdata.region import REPO_DIR, load_regions

    for region in load_regions().values():
        lon_min, lat_min, lon_max, lat_max = region.bbox
        assert lon_min <= region.base["lon"] <= lon_max, region.id
        assert lat_min <= region.base["lat"] <= lat_max, region.id
        for name in region.traverse_files.values():
            assert (REPO_DIR / name).exists(), f"{region.id}: falta {name}"
