"""Lectura de regiones precalculadas (manifest + grillas .npy) desde disco o R2."""

import hashlib
import io
import json
import re
from collections import OrderedDict
from collections.abc import Callable, Hashable
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import TypeVar

import httpx
import numpy as np
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.region import RegionManifest

# Capas opcionales: si una región no la tiene, se usa una grilla de ceros.
OPTIONAL_LAYERS = ("hazard", "thermal_inertia", "ice", "minerals")

# Los IDs terminan en rutas de archivo: no pueden traer separadores ni "..".
_SAFE_ID = re.compile(r"[A-Za-z0-9_-]+")

# Cuántos resultados intermedios guarda cada región (ver GridMemo).
MEMO_SIZE = 8

T = TypeVar("T")


class NotFoundError(Exception):
    """La región o el recorrido pedidos no existen."""


class RegionDataError(Exception):
    """Los datos no se pudieron leer o no son consistentes con el manifest."""


class GridMemo:
    """Caché pequeña (la menos usada sale primero) de resultados que se repiten entre peticiones.

    Por ejemplo, la penalización por pendiente es la misma para las cuatro rutas de una comparación,
    y el mapa de regreso seguro no cambia si solo se mueve la autonomía del traje. Se usa desde
    varios hilos (FastAPI corre las rutas síncronas en un grupo de hilos): el candado protege el
    diccionario; el cálculo va fuera, y si dos hilos calculan lo mismo a la vez, gana cualquiera.
    """

    def __init__(self, size: int = MEMO_SIZE) -> None:
        self._items: OrderedDict[Hashable, object] = OrderedDict()
        self._size = size
        self._lock = Lock()

    def get(self, key: Hashable, compute: Callable[[], T]) -> T:
        with self._lock:
            if key in self._items:
                self._items.move_to_end(key)
                return self._items[key]  # type: ignore[return-value]
        value = compute()
        with self._lock:
            self._items[key] = value
            self._items.move_to_end(key)
            while len(self._items) > self._size:
                self._items.popitem(last=False)
        return value


@dataclass
class RegionGrids:
    manifest: RegionManifest
    dem: np.ndarray  # metros
    slope: np.ndarray  # grados
    hazard: np.ndarray  # 0–1, obstáculos (HiRISE/CTX)
    thermal_inertia: np.ndarray  # 0–1, alto = roca firme (THEMIS)
    ice: np.ndarray  # 0–1, probabilidad de hielo (SWIM)
    minerals: np.ndarray  # 0–1, valor científico (CRISM)
    # Solo las grillas de load_region (que no cambian) guardan resultados; las que se arman a mano,
    # como en las pruebas, pueden modificarse y por eso no usan caché.
    memo: GridMemo | None = field(default=None, repr=False, compare=False)


def memoized(grids: RegionGrids, key: Hashable, compute: Callable[[], T]) -> T:
    """Resultado guardado de `compute` para esta región, o calculado al momento si no hay caché."""
    return compute() if grids.memo is None else grids.memo.get(key, compute)


def _read_bytes(rel_path: str) -> bytes:
    s = get_settings()
    if s.assets_dir:
        return (Path(s.assets_dir) / rel_path).read_bytes()
    if s.assets_url:
        try:
            r = httpx.get(f"{s.assets_url.rstrip('/')}/{rel_path}", timeout=30)
        except httpx.HTTPError as e:
            raise RegionDataError(f"No se pudo leer {rel_path}: {e}") from e
        if r.status_code == 404:
            raise FileNotFoundError(rel_path)
        if r.is_error:
            raise RegionDataError(f"No se pudo leer {rel_path}: HTTP {r.status_code}")
        return r.content
    raise RegionDataError("Configura ASSETS_DIR o ASSETS_URL")


def _read_verified(m: RegionManifest, rel_path: str) -> bytes:
    """Lee un archivo de la región y lo compara con el checksum del manifest."""
    try:
        data = _read_bytes(f"{m.id}/{rel_path}")
    except FileNotFoundError as e:
        raise RegionDataError(f"Falta {rel_path} en la región {m.id}") from e
    expected = m.checksums.get(rel_path)
    if expected and hashlib.sha256(data).hexdigest() != expected:
        raise RegionDataError(f"{rel_path} no coincide con el checksum del manifest de {m.id}")
    return data


def _read_grid(m: RegionManifest, rel_path: str) -> np.ndarray:
    grid = np.load(io.BytesIO(_read_verified(m, rel_path))).astype(np.float32)
    if grid.shape != m.shape:
        raise RegionDataError(f"{rel_path} mide {grid.shape}; el manifest de {m.id} dice {m.shape}")
    if not np.isfinite(grid).all():
        raise RegionDataError(f"{rel_path} tiene celdas sin dato en la región {m.id}")
    return grid


def list_regions() -> list[RegionManifest]:
    try:
        index = json.loads(_read_bytes("index.json"))
    except FileNotFoundError as e:
        raise RegionDataError("No hay regiones publicadas: falta index.json") from e
    return [load_manifest(rid) for rid in index["regions"]]


@lru_cache(maxsize=16)
def load_manifest(region_id: str) -> RegionManifest:
    if not _SAFE_ID.fullmatch(region_id):
        raise NotFoundError(f"Región '{region_id}' no encontrada")
    try:
        return RegionManifest.model_validate_json(_read_bytes(f"{region_id}/manifest.json"))
    except FileNotFoundError as e:
        raise NotFoundError(f"Región '{region_id}' no encontrada") from e
    except ValidationError as e:
        raise RegionDataError(f"Manifest inválido en la región {region_id}: {e}") from e


@lru_cache(maxsize=4)
def load_region(region_id: str) -> RegionGrids:
    m = load_manifest(region_id)
    dem = _read_grid(m, "dem.npy")
    layers = {
        name: _read_grid(m, f"layers/{name}.npy") if name in m.layers else np.zeros_like(dem)
        for name in OPTIONAL_LAYERS
    }
    slope = _read_grid(m, "slope.npy")
    return RegionGrids(manifest=m, dem=dem, slope=slope, **layers, memo=GridMemo())


def load_traverse(region_id: str, rover: str) -> dict:
    m = load_manifest(region_id)
    if rover not in m.traverses:
        raise NotFoundError(f"No hay recorrido de '{rover}' en '{region_id}'")
    return json.loads(_read_verified(m, f"traverses/{rover}.geojson"))
