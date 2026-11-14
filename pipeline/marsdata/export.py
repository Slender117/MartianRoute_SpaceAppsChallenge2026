"""Escribe una región procesada en el formato que leen la API y la web.

data/regions/
├── index.json
└── <region>/
    ├── manifest.json
    ├── dem.npy, slope.npy
    ├── layers/<capa>.npy
    ├── heightmap.png          (16 bits, para el terreno 3D)
    ├── textures/<capa>.png    (RGBA, para los overlays)
    └── traverses/<rover>.geojson
"""

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from marsdata.region import Region

OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "regions"

# CRS de todas las grillas y recorridos (el mismo de process/reproject.py).
CRS = "+proj=longlat +R=3389500 +no_defs"

# Color de cada capa en su textura; la opacidad sale del valor normalizado.
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
    """Commit del pipeline, o None si la carpeta no está en un repositorio de git."""
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
    """Procedencia de cada capa. Los productos reales pasan por estéreo o por un modelo: derived.

    `extra` (del build) agrega la cobertura de cada capa y puede corregir la procedencia.
    """
    if synthetic:
        return {name: {"provenance": "modeled", "source": "marsdata.synthetic"} for name in names}
    sources = {
        **region.sources,
        "slope": region.sources.get("dem", ""),
        "impassable_fraction": region.sources.get("hazard", ""),
    }
    extra = extra or {}
    return {
        name: {"provenance": "derived", "source": sources.get(name, ""), **extra.get(name, {})}
        for name in names
    }


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
) -> Path:
    """Escribe la región. Cada punto de un recorrido es (lat, lon) o (lat, lon, elevación)."""
    rdir = out_dir / region.id
    (rdir / "layers").mkdir(parents=True, exist_ok=True)
    (rdir / "textures").mkdir(exist_ok=True)

    dem, slope = grids["dem"], grids["slope"]
    np.save(rdir / "dem.npy", dem.astype(np.float32))
    np.save(rdir / "slope.npy", slope.astype(np.float32))

    layers = [k for k in grids if k not in ("dem", "slope")]
    for name in layers:
        np.save(rdir / "layers" / f"{name}.npy", grids[name].astype(np.float32))
        _texture(grids[name], LAYER_COLORS[name]).save(rdir / "textures" / f"{name}.png")
    _texture(np.clip(slope / 35, 0, 1), LAYER_COLORS["slope"]).save(rdir / "textures" / "slope.png")

    zmin, zmax = float(dem.min()), float(dem.max())
    height16 = ((dem - zmin) / max(zmax - zmin, 1e-6) * 65535).astype(np.uint16)
    Image.fromarray(height16).save(rdir / "heightmap.png")

    traverses = traverses or {}
    if traverses:
        (rdir / "traverses").mkdir(exist_ok=True)
    for rover, coords in traverses.items():
        geojson = {
            "type": "Feature",
            "properties": {"rover": rover, **(traverse_properties or {}).get(rover, {})},
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
        "elevation_range": [zmin, zmax],
        "base": region.base,
        "layers": layers,
        "traverses": list(traverses),
        "dataset_version": region.dataset_version,
        "pipeline_commit": _pipeline_commit(),
        "crs": CRS,
        "synthetic": synthetic,
        "layer_meta": _layer_meta(region, ["dem", "slope", *layers], synthetic, layer_meta),
        "checksums": _checksums(rdir),
        "demo": region.demo,
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
