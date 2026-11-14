"""Consulta las fuentes de NASA, guarda cada respuesta en memoria y cae a la copia guardada.

- Cada fuente se consulta como mucho una vez por `CACHE_TTL` mientras corre la API.
- Si NASA no responde (sin internet, límite de la llave, cambio de formato), se usa la última
  respuesta buena de esta ejecución; si no hay, la copia de `snapshot.json`. La respuesta dice
  cuál se usó (`status`) y de cuándo es (`fetched_at`), para que la interfaz no la presente como
  dato del momento.
- `python -m app.live` vuelve a escribir `snapshot.json` con lo que dé NASA en ese momento.
"""

import asyncio
import json
import math
import ssl
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.config import get_settings
from app.geo import MARS_RADIUS_M
from app.schemas.live import (
    CmeArrival,
    LiveResponse,
    RoverImages,
    RoverPosition,
    SourceInfo,
    SpaceWeather,
)
from app.schemas.region import RegionManifest
from app.schemas.route import Provenance

from . import sources as s

SNAPSHOT_PATH = Path(__file__).with_name("snapshot.json")
CACHE_TTL = timedelta(minutes=30)
TIMEOUT_S = 10.0

SOURCES: dict[str, dict[str, Any]] = {
    "space_weather": {
        "name": "NASA CCMC DONKI · WSA-ENLIL",
        "page": s.DONKI_PAGE,
        "provenance": Provenance.modeled,
    },
    "rover": {
        "name": "NASA/JPL MMGIS · Perseverance waypoints",
        "page": s.WAYPOINTS_PAGE,
        "provenance": Provenance.observed,
    },
    "images": {
        "name": "NASA/JPL-Caltech · Perseverance raw images",
        "page": s.RAW_IMAGES_PAGE,
        "provenance": Provenance.observed,
    },
}

# Última respuesta buena de cada fuente en esta ejecución: (cuándo, datos ya leídos).
_cache: dict[str, tuple[datetime, Any]] = {}


def clear_cache() -> None:
    _cache.clear()


def _source(key: str, status: str, fetched_at: datetime, error: str | None = None) -> SourceInfo:
    meta = SOURCES[key]
    return SourceInfo(
        name=meta["name"],
        url=meta["page"],
        status=status,
        fetched_at=fetched_at,
        provenance=meta["provenance"],
        error=error,
    )


async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, str]) -> Any:
    res = await client.get(url, params=params)
    res.raise_for_status()
    return res.json()


async def _fetch_space_weather(client: httpx.AsyncClient, now: datetime) -> list[dict]:
    params = {
        "startDate": (now - timedelta(days=s.DONKI_DAYS)).date().isoformat(),
        "endDate": now.date().isoformat(),
        "api_key": get_settings().nasa_api_key,
    }
    arrivals = s.parse_enlil(await _get_json(client, s.DONKI_ENLIL_URL, params))
    return [a.model_dump(mode="json") for a in arrivals]


async def _fetch_rover(client: httpx.AsyncClient, now: datetime) -> dict:
    return s.parse_waypoints(await _get_json(client, s.WAYPOINTS_URL, {}))


async def _fetch_images(client: httpx.AsyncClient, now: datetime) -> dict:
    latest_sol, images = s.parse_raw_images(
        await _get_json(client, s.RAW_IMAGES_URL, s.RAW_IMAGES_PARAMS)
    )
    return {"latest_sol": latest_sol, "images": [i.model_dump(mode="json") for i in images]}


FETCHERS: dict[str, Callable] = {
    "space_weather": _fetch_space_weather,
    "rover": _fetch_rover,
    "images": _fetch_images,
}


def _client(transport: httpx.AsyncBaseTransport | None) -> httpx.AsyncClient:
    # Certificados del sistema operativo (en Windows, su almacén) en vez del paquete certifi de
    # httpx: así funciona en equipos con antivirus o proxy que inspeccionan HTTPS. Respeta
    # SSL_CERT_FILE si está definido.
    return httpx.AsyncClient(
        timeout=TIMEOUT_S,
        transport=transport,
        follow_redirects=True,
        verify=ssl.create_default_context(),
    )


def read_snapshot(path: Path = SNAPSHOT_PATH) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _error_text(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return f"NASA respondió {exc.response.status_code}"
    if isinstance(exc, httpx.TimeoutException):
        return "NASA no respondió a tiempo"
    if isinstance(exc, httpx.TransportError):
        return "sin conexión con NASA"
    return f"respuesta inesperada de NASA ({type(exc).__name__})"


async def _one(
    key: str, client: httpx.AsyncClient | None, now: datetime, snapshot: dict
) -> tuple[SourceInfo, Any]:
    cached = _cache.get(key)
    if cached and now - cached[0] < CACHE_TTL:
        return _source(key, "live", cached[0]), cached[1]
    error = "consulta en vivo apagada (LIVE_DATA=false)"
    if client is not None:
        try:
            data = await FETCHERS[key](client, now)
            _cache[key] = (now, data)
            return _source(key, "live", now), data
        except Exception as exc:  # cualquier falla de NASA cae al respaldo
            error = _error_text(exc)
    if cached:
        return _source(key, "live", cached[0], error), cached[1]
    saved = snapshot.get(key) or {}
    fetched_at = s.parse_time(saved.get("fetched_at")) or datetime(1970, 1, 1, tzinfo=UTC)
    return _source(key, "snapshot", fetched_at, error), saved.get("data")


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * MARS_RADIUS_M * math.asin(math.sqrt(h)) / 1000


async def get_live(
    region: RegionManifest | None = None,
    now: datetime | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> LiveResponse:
    now = now or datetime.now(UTC)
    snapshot = read_snapshot()
    if get_settings().live_data:
        async with _client(transport) as client:
            results = await asyncio.gather(*(_one(k, client, now, snapshot) for k in FETCHERS))
    else:
        results = [await _one(k, None, now, snapshot) for k in FETCHERS]
    (sw_src, sw), (rv_src, rv), (im_src, im) = results

    arrivals = [CmeArrival.model_validate(a) for a in sw or []]
    space_weather = SpaceWeather(
        source=sw_src,
        arrivals=arrivals,
        alert=s.solar_alert(arrivals, now),
        alert_before_h=s.SOLAR_ALERT_BEFORE_H,
        alert_after_h=s.SOLAR_ALERT_AFTER_H,
    )

    rover = None
    if rv:
        rover = RoverPosition(source=rv_src, **rv)
        if region is not None:
            lon_min, lat_min, lon_max, lat_max = region.bbox
            rover.in_region = lon_min <= rover.lon <= lon_max and lat_min <= rover.lat <= lat_max
            rover.distance_to_base_km = round(
                distance_km(rover.lat, rover.lon, region.base.lat, region.base.lon), 2
            )

    im = im or {}
    images = RoverImages(
        source=im_src, latest_sol=im.get("latest_sol"), images=im.get("images", [])
    )
    return LiveResponse(generated_at=now, space_weather=space_weather, rover=rover, images=images)


async def build_snapshot(
    previous: dict[str, Any], transport: httpx.AsyncBaseTransport | None = None
) -> tuple[dict[str, Any], dict[str, str]]:
    """Consulta cada fuente en vivo. La que falle conserva su parte de la copia anterior.

    Devuelve la copia nueva y, por fuente, el motivo de lo que no se pudo actualizar.
    """
    now = datetime.now(UTC)
    out: dict[str, Any] = {}
    errors: dict[str, str] = {}
    async with _client(transport) as client:
        for key, fetch in FETCHERS.items():
            try:
                out[key] = {"fetched_at": now.isoformat(), "data": await fetch(client, now)}
            except Exception as exc:  # la parte vieja sigue valiendo como respaldo
                errors[key] = _error_text(exc)
                if key in previous:
                    out[key] = previous[key]
    return out, errors
