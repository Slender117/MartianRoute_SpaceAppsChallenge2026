"""Reads precomputed regions (manifest + .npy grids) from disk or R2."""

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

# Optional layers: if a region does not have one, a grid of zeros is used.
OPTIONAL_LAYERS = ("hazard", "thermal_inertia", "ice", "minerals")

# IDs end up in file paths: they cannot contain separators or "..".
_SAFE_ID = re.compile(r"[A-Za-z0-9_-]+")

# How many intermediate results each region keeps (see GridMemo).
MEMO_SIZE = 8

T = TypeVar("T")


class NotFoundError(Exception):
    """The requested region or traverse does not exist."""


class RegionDataError(Exception):
    """The data could not be read or is not consistent with the manifest."""


class GridMemo:
    """Small cache (least recently used goes first) of results repeated across requests.

    For example, the slope penalty is the same for the four routes of a comparison,
    and the safe-return map does not change if only the suit autonomy moves. It is used from
    several threads (FastAPI runs sync routes in a thread pool): the lock protects the
    dictionary; the computation runs outside it, and if two threads compute the same, either wins.
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
    hazard: np.ndarray  # 0–1, obstacles (HiRISE/CTX)
    thermal_inertia: np.ndarray  # 0–1, high = firm rock (THEMIS)
    ice: np.ndarray  # 0–1, ice probability (SWIM)
    minerals: np.ndarray  # 0–1, science value (CRISM)
    # Only load_region grids (which do not change) cache results; hand-built ones,
    # as in the tests, can be modified, so they do not use the cache.
    memo: GridMemo | None = field(default=None, repr=False, compare=False)


def memoized(grids: RegionGrids, key: Hashable, compute: Callable[[], T]) -> T:
    """Cached result of `compute` for this region, or computed now if there is no cache."""
    return compute() if grids.memo is None else grids.memo.get(key, compute)


def _read_bytes(rel_path: str) -> bytes:
    s = get_settings()
    if s.assets_dir:
        return (Path(s.assets_dir) / rel_path).read_bytes()
    if s.assets_url:
        try:
            r = httpx.get(f"{s.assets_url.rstrip('/')}/{rel_path}", timeout=30)
        except httpx.HTTPError as e:
            raise RegionDataError(f"Could not read {rel_path}: {e}") from e
        if r.status_code == 404:
            raise FileNotFoundError(rel_path)
        if r.is_error:
            raise RegionDataError(f"Could not read {rel_path}: HTTP {r.status_code}")
        return r.content
    raise RegionDataError("Configura ASSETS_DIR o ASSETS_URL")


def _read_verified(m: RegionManifest, rel_path: str) -> bytes:
    """Reads a region file and checks it against the manifest checksum."""
    try:
        data = _read_bytes(f"{m.id}/{rel_path}")
    except FileNotFoundError as e:
        raise RegionDataError(f"{rel_path} is missing in region {m.id}") from e
    expected = m.checksums.get(rel_path)
    if expected and hashlib.sha256(data).hexdigest() != expected:
        raise RegionDataError(f"{rel_path} does not match the manifest checksum of {m.id}")
    return data


def _read_grid(m: RegionManifest, rel_path: str) -> np.ndarray:
    grid = np.load(io.BytesIO(_read_verified(m, rel_path))).astype(np.float32)
    if grid.shape != m.shape:
        raise RegionDataError(f"{rel_path} is {grid.shape}; the manifest of {m.id} says {m.shape}")
    if not np.isfinite(grid).all():
        raise RegionDataError(f"{rel_path} has cells with no data in region {m.id}")
    return grid


def list_regions() -> list[RegionManifest]:
    try:
        index = json.loads(_read_bytes("index.json"))
    except FileNotFoundError as e:
        raise RegionDataError("No regions published: index.json is missing") from e
    return [load_manifest(rid) for rid in index["regions"]]


@lru_cache(maxsize=16)
def load_manifest(region_id: str) -> RegionManifest:
    if not _SAFE_ID.fullmatch(region_id):
        raise NotFoundError(f"Region '{region_id}' not found")
    try:
        return RegionManifest.model_validate_json(_read_bytes(f"{region_id}/manifest.json"))
    except FileNotFoundError as e:
        raise NotFoundError(f"Region '{region_id}' not found") from e
    except ValidationError as e:
        raise RegionDataError(f"Invalid manifest in region {region_id}: {e}") from e


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
        raise NotFoundError(f"No '{rover}' traverse in '{region_id}'")
    return json.loads(_read_verified(m, f"traverses/{rover}.geojson"))
