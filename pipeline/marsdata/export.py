"""Writes a processed region in the format the API and the web read.

data/regions/
├── index.json
└── <region>/
    ├── manifest.json
    ├── dem.npy, slope.npy
    ├── layers/<layer>.npy
    ├── heightmap.bin          (Float32 little-endian, row 0 to the north: 3D terrain)
    ├── heightmap.png          (16-bit; the scene used it before the .bin)
    ├── textures/<layer>.png   (RGBA, for the overlays)
    ├── textures/ortho.jpg     (grayscale orthophoto, if the region has one)
    └── traverses/<rover>.geojson

The manifest also carries `assets`, `legends`, `labels` and `cell_size_m` for the 3D view (contract
proposal in docs/arquitectura.md). The API does not declare them yet and drops them when serving the
manifest, so the web reads them from the manifest.json published next to the files.
"""

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from marsdata.process.traverse import sample_grid
from marsdata.region import Region

OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "regions"

# CRS of every grid and traverse (the same as in process/reproject.py).
CRS = "+proj=longlat +R=3389500 +no_defs"

# Color of each layer in its texture; the opacity comes from the normalized value.
LAYER_COLORS = {
    "slope": (255, 80, 40),
    "hazard": (255, 200, 0),
    "thermal_inertia": (90, 160, 255),
    "ice": (180, 240, 255),
    "minerals": (60, 220, 120),
    "impassable_fraction": (200, 60, 255),
}


def _texture(values01: np.ndarray, rgb: tuple[int, int, int]) -> Image.Image:
    h, w = values01.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., :3] = rgb
    rgba[..., 3] = (np.clip(values01, 0, 1) * 220).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def _pipeline_commit() -> str | None:
    """Pipeline commit, or None if the folder is not in a git repository."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip()


def _layer_meta(
    region: Region, names: list[str], synthetic: bool, extra: dict[str, dict] | None = None
) -> dict[str, dict]:
    """Provenance of each layer. Real products go through stereo or a model: derived.

    `extra` (from the build) adds each layer's coverage and can correct the provenance.
    """
    if synthetic:
        return {name: {"provenance": "modeled", "source": "marsdata.synthetic"} for name in names}
    sources = {
        **region.sources,
        "slope": region.sources.get("dem", ""),
        "impassable_fraction": region.sources.get("hazard", ""),
        "terrain_class": region.sources.get("hazard", ""),
    }
    extra = extra or {}
    return {
        name: {"provenance": "derived", "source": sources.get(name, ""), **extra.get(name, {})}
        for name in names
    }


def _labels(
    region: Region, dem: np.ndarray, traverses: dict, traverse_properties: dict, synthetic: bool
) -> list[dict]:
    """Names from regions.yaml plus the start and end of each traverse, with their elevation.

    A label with `only` goes only into the version it names (synthetic or real).
    """
    version = "synthetic" if synthetic else "real"
    labels = [
        {k: v for k, v in label.items() if k != "only"}
        for label in region.labels
        if label.get("only", version) == version
    ]
    for rover, coords in traverses.items():
        props = traverse_properties.get(rover, {})
        for point, sol in ((coords[0], props.get("sol_min")), (coords[-1], props.get("sol_max"))):
            if sol is None:
                continue
            labels.append(
                {
                    "name": f"{rover.capitalize()} · sol {sol}",
                    "lat": point[0],
                    "lon": point[1],
                    "source": props.get("source", rover),
                    "kind": "traverse",
                }
            )
    for label in labels:
        label["elev"] = round(float(sample_grid(dem, region, label["lat"], label["lon"])), 1)
    return labels


def _checksums(rdir: Path) -> dict[str, str]:
    return {
        path.relative_to(rdir).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(rdir.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }


def write_region(
    region: Region,
    grids: dict[str, np.ndarray],
    traverses: dict[str, list[tuple[float, ...]]] | None = None,
    out_dir: Path = OUT_DIR,
    synthetic: bool = False,
    layer_meta: dict[str, dict] | None = None,
    traverse_properties: dict[str, dict] | None = None,
    textures: dict[str, np.ndarray] | None = None,
    legends: dict[str, list[dict]] | None = None,
    ortho: np.ndarray | None = None,
) -> Path:
    """Writes the region. Each traverse point is (lat, lon) or (lat, lon, elevation).

    `textures` are visual-only layers already colored (RGBA), like the NOAH-H classes: they are
    listed in `layers` so the web shows them, but they have no .npy grid.
    """
    rdir = out_dir / region.id
    (rdir / "layers").mkdir(parents=True, exist_ok=True)
    (rdir / "textures").mkdir(exist_ok=True)
    traverses = traverses or {}
    traverse_properties = traverse_properties or {}
    textures = textures or {}

    dem, slope = grids["dem"], grids["slope"]
    np.save(rdir / "dem.npy", dem.astype(np.float32))
    np.save(rdir / "slope.npy", slope.astype(np.float32))

    grid_layers = [k for k in grids if k not in ("dem", "slope")]
    for name in grid_layers:
        np.save(rdir / "layers" / f"{name}.npy", grids[name].astype(np.float32))
        _texture(grids[name], LAYER_COLORS[name]).save(rdir / "textures" / f"{name}.png")
    _texture(np.clip(slope / 35, 0, 1), LAYER_COLORS["slope"]).save(rdir / "textures" / "slope.png")
    for name, rgba in textures.items():
        Image.fromarray(rgba, "RGBA").save(rdir / "textures" / f"{name}.png")
    layers = [*grid_layers, *textures]

    zmin, zmax = float(dem.min()), float(dem.max())
    height16 = ((dem - zmin) / max(zmax - zmin, 1e-6) * 65535).astype(np.uint16)
    Image.fromarray(height16).save(rdir / "heightmap.png")
    dem.astype("<f4").tofile(rdir / "heightmap.bin")
    assets = {
        "heightmap": {
            "path": "heightmap.bin",
            "dtype": "float32",
            "byte_order": "little",
            "shape": list(dem.shape),
            "row0": "north",
        }
    }
    if ortho is not None:
        Image.fromarray(ortho, "L").save(rdir / "textures" / "ortho.jpg", quality=88)
        assets["ortho"] = {
            "path": "textures/ortho.jpg",
            "size": [ortho.shape[1], ortho.shape[0]],
            "provenance": "observed",
            "source": region.sources.get("ortho", ""),
        }

    if traverses:
        (rdir / "traverses").mkdir(exist_ok=True)
    for rover, coords in traverses.items():
        geojson = {
            "type": "Feature",
            "properties": {"rover": rover, **traverse_properties.get(rover, {})},
            "geometry": {
                "type": "LineString",
                "coordinates": [[lon, lat, *rest] for lat, lon, *rest in coords],
            },
        }
        (rdir / "traverses" / f"{rover}.geojson").write_text(json.dumps(geojson), encoding="utf-8")

    manifest = {
        "id": region.id,
        "name": region.name,
        "bbox": list(region.bbox),
        "shape": list(region.shape),
        "resolution_m": region.resolution_m,
        "cell_size_m": [round(v, 2) for v in region.cell_size_m],
        "elevation_range": [zmin, zmax],
        "base": region.base,
        "layers": layers,
        "traverses": list(traverses),
        "dataset_version": region.dataset_version,
        "pipeline_commit": _pipeline_commit(),
        "crs": CRS,
        "synthetic": synthetic,
        "layer_meta": _layer_meta(region, ["dem", "slope", *layers], synthetic, layer_meta),
        "assets": assets,
        "legends": legends or {},
        "labels": _labels(region, dem, traverses, traverse_properties, synthetic),
        "checksums": _checksums(rdir),
        "demo": region.demo if synthetic else (region.demo_real or region.demo),
    }
    (rdir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _update_index(out_dir, region.id)
    return rdir


def _update_index(out_dir: Path, region_id: str) -> None:
    index_path = out_dir / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
    regions = sorted(set(index.get("regions", [])) | {region_id})
    index_path.write_text(json.dumps({"regions": regions}, indent=2), encoding="utf-8")
