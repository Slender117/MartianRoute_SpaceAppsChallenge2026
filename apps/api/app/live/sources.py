"""Real-time NASA sources and how their responses are read.

Each `parse_*` function takes the JSON exactly as NASA returns it and keeps only what the app
uses. They make no requests, so the tests exercise them with saved responses.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from app.schemas.live import CmeArrival, RoverImage

# DONKI (Space Weather Database Of Notifications, Knowledge, Information) from NASA's CCMC. The
# WSA-ENLIL simulations forecast which planets and spacecraft each coronal mass ejection reaches.
DONKI_ENLIL_URL = "https://api.nasa.gov/DONKI/WSAEnlilSimulations"
DONKI_PAGE = "https://kauai.ccmc.gsfc.nasa.gov/DONKI/"
DONKI_DAYS = 30

# Perseverance position: waypoint layer of JPL's MMGIS (one point per location).
WAYPOINTS_URL = "https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_waypoints.json"
WAYPOINTS_PAGE = "https://mars.nasa.gov/mars2020/mission/where-is-the-rover/"

# Perseverance raw images, the same as in the public gallery.
RAW_IMAGES_URL = "https://mars.nasa.gov/rss/api/"
RAW_IMAGES_PARAMS = {
    "feed": "raw_images",
    "category": "mars2020",
    "feedtype": "json",
    "num": "25",
    "page": "0",
    "order": "sol desc",
}
RAW_IMAGES_PAGE = "https://mars.nasa.gov/mars2020/multimedia/raw-images/"
MAX_IMAGES = 6

# Alert window around the forecast arrival of an ejection at Mars (project
# decision): from 72 h before to 48 h after.
SOLAR_ALERT_BEFORE_H = 72.0
SOLAR_ALERT_AFTER_H = 48.0


def parse_time(value: str | None) -> datetime | None:
    """NASA dates: "2026-11-13T12:00Z", "2026-11-06T12:16:25.848" or "2026-11-06T15:59:53Z"."""
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        t = datetime.fromisoformat(text)
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=UTC)


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_enlil(simulations: list[dict]) -> list[CmeArrival]:
    """Arrivals at Mars. If an ejection was simulated several times, the newest run is kept."""
    by_cme: dict[str, CmeArrival] = {}
    for sim in simulations or []:
        completion = parse_time(sim.get("modelCompletionTime"))
        inputs = (sim.get("cmeInputs") or [{}])[0] or {}
        cme_id = inputs.get("CMEID") or inputs.get("cmeid") or inputs.get("associatedCMEID")
        for impact in sim.get("impactList") or []:
            arrival = parse_time(impact.get("arrivalTime"))
            if impact.get("location") != "Mars" or arrival is None or completion is None:
                continue
            item = CmeArrival(
                simulation_id=sim.get("simulationID", ""),
                cme_id=cme_id,
                cme_start=parse_time(inputs.get("cmeStartTime")),
                speed_km_s=_float(inputs.get("speed")),
                arrival_time=arrival,
                glancing_blow=bool(impact.get("isGlancingBlow")),
                minor_impact=bool(impact.get("isMinorImpact")),
                model_completion=completion,
                link=sim.get("link") or DONKI_PAGE,
            )
            key = cme_id or arrival.isoformat()
            if key not in by_cme or item.model_completion > by_cme[key].model_completion:
                by_cme[key] = item
    return sorted(by_cme.values(), key=lambda a: a.arrival_time, reverse=True)


def solar_alert(arrivals: list[CmeArrival], now: datetime) -> CmeArrival | None:
    """The arrival closest to `now` inside the window; if several, the one still to come."""
    inside = [
        a
        for a in arrivals
        if a.arrival_time - timedelta(hours=SOLAR_ALERT_BEFORE_H)
        <= now
        <= a.arrival_time + timedelta(hours=SOLAR_ALERT_AFTER_H)
    ]
    if not inside:
        return None
    upcoming = [a for a in inside if a.arrival_time >= now]
    pool = upcoming or inside
    return min(pool, key=lambda a: abs((a.arrival_time - now).total_seconds()))


def parse_waypoints(collection: dict) -> dict:
    """Last rover point: the one with the highest sol, site and drive."""
    points = [f for f in collection.get("features") or [] if f.get("properties")]
    if not points:
        raise ValueError("the waypoint layer has no points")

    def order(f: dict) -> tuple[int, int, int]:
        p = f["properties"]
        return (int(p.get("sol") or 0), int(p.get("site") or 0), int(p.get("drive") or 0))

    last = max(points, key=order)
    p = last["properties"]
    coords = (last.get("geometry") or {}).get("coordinates") or []
    lon = _float(p.get("lon")) if p.get("lon") is not None else _float(coords[0])
    lat = _float(p.get("lat")) if p.get("lat") is not None else _float(coords[1])
    if lat is None or lon is None:
        raise ValueError("the last waypoint has no coordinates")
    total_m = _float(p.get("dist_total_m"))
    return {
        "rover": "Perseverance",
        "sol": int(p.get("sol") or 0),
        "site": int(p.get("site") or 0),
        "drive": int(p.get("drive") or 0),
        "lat": lat,
        "lon": lon,
        "elevation_m": _float(p.get("elev_geoid")),
        "odometry_km": None if total_m is None else round(total_m / 1000, 2),
    }


def parse_raw_images(payload: dict) -> tuple[int | None, list[RoverImage]]:
    """Most recent images, one per camera, without the engineering thumbnails."""
    images: list[RoverImage] = []
    cameras: set[str] = set()
    for item in payload.get("images") or []:
        if str(item.get("sample_type", "")).lower() == "thumbnail":
            continue
        files = item.get("image_files") or {}
        thumb = files.get("small") or files.get("medium")
        taken = parse_time(item.get("date_taken_utc"))
        camera = (item.get("camera") or {}).get("instrument") or "?"
        if not thumb or taken is None or camera in cameras:
            continue
        cameras.add(camera)
        images.append(
            RoverImage(
                image_id=item.get("imageid", ""),
                sol=int(item.get("sol") or 0),
                taken_utc=taken,
                camera=camera,
                thumbnail_url=thumb,
                full_url=files.get("full_res") or files.get("large"),
                page_url=item.get("link"),
            )
        )
        if len(images) == MAX_IMAGES:
            break
    sols = [int(i.get("sol") or 0) for i in payload.get("images") or []]
    return (max(sols) if sols else None), images
