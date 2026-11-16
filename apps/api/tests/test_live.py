"""Live NASA data (/live). No test goes to the internet: NASA is simulated with httpx."""

import asyncio
from datetime import UTC, datetime

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.live import service, sources
from app.main import create_app
from app.storage import load_manifest

NOW = datetime(2026, 11, 14, 19, 30, tzinfo=UTC)

ENLIL = [
    {  # old simulation of the same ejection: the new one must remain
        "simulationID": "WSA-ENLIL/49472/1",
        "modelCompletionTime": "2026-11-09T18:00Z",
        "cmeInputs": [{"CMEID": "2026-11-09T10:00:00-CME-001", "speed": 610.0}],
        "impactList": [
            {"location": "Mars", "arrivalTime": "2026-11-13T10:00Z", "isGlancingBlow": True}
        ],
        "link": "https://kauai.ccmc.gsfc.nasa.gov/DONKI/view/WSA-ENLIL/49472/1",
    },
    {
        "simulationID": "WSA-ENLIL/49473/1",
        "modelCompletionTime": "2026-11-09T19:59Z",
        "cmeInputs": [{"CMEID": "2026-11-09T10:00:00-CME-001", "speed": 640.0}],
        "impactList": [
            {"location": "STEREO A", "arrivalTime": "2026-11-12T01:00Z", "isGlancingBlow": False},
            {"location": "Mars", "arrivalTime": "2026-11-13T12:00Z", "isGlancingBlow": True},
        ],
        "link": "https://kauai.ccmc.gsfc.nasa.gov/DONKI/view/WSA-ENLIL/49473/1",
    },
    {
        "simulationID": "WSA-ENLIL/49326/1",
        "modelCompletionTime": "2026-11-01T08:00Z",
        "cmeInputs": [{"CMEID": "2026-10-31T20:00:00-CME-001"}],
        "impactList": [
            {"location": "Mars", "arrivalTime": "2026-11-04T08:00Z", "isMinorImpact": True}
        ],
    },
    {
        "simulationID": "WSA-ENLIL/1/1",
        "modelCompletionTime": "2026-11-02T00:00Z",
        "impactList": None,
    },
]

WAYPOINTS = {
    "type": "FeatureCollection",
    "features": [
        {
            "geometry": {"type": "Point", "coordinates": [77.2, 18.4, -1930.0]},
            "properties": {"sol": 2020, "site": 92, "drive": 0, "lon": 77.2, "lat": 18.4},
        },
        {
            "geometry": {"type": "Point", "coordinates": [77.23322287, 18.43559434, -1936.37]},
            "properties": {
                "sol": 2022,
                "site": 93,
                "drive": 0,
                "lon": 77.23322287,
                "lat": 18.43559434,
                "elev_geoid": -1936.366943,
                "dist_total_m": 45245.71,
            },
        },
    ],
}


def _image(i: int, camera: str, sample_type: str = "Full") -> dict:
    url = f"https://mars.nasa.gov/img/{i}"
    return {
        "imageid": f"IMG_{i}",
        "sol": 2031,
        "sample_type": sample_type,
        "date_taken_utc": "2026-11-06T12:16:25.848",
        "camera": {"instrument": camera},
        "image_files": {"small": f"{url}_320.jpg", "full_res": f"{url}.png"},
        "link": f"https://mars.nasa.gov/raw/{i}",
    }


RAW_IMAGES = {
    "images": [
        _image(1, "SUPERCAM_RMI"),
        _image(2, "SUPERCAM_RMI"),
        _image(3, "NAVCAM_LEFT", "Thumbnail"),
        _image(4, "NAVCAM_LEFT"),
    ]
}


def nasa(request: httpx.Request) -> httpx.Response:
    if "DONKI" in request.url.path:
        assert request.url.params["api_key"]
        return httpx.Response(200, json=ENLIL)
    if request.url.path.endswith("M20_waypoints.json"):
        return httpx.Response(200, json=WAYPOINTS)
    if request.url.params.get("feed") == "raw_images":
        return httpx.Response(200, json=RAW_IMAGES)
    return httpx.Response(404)


def offline(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("sin red", request=request)


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    """Each test starts with no cache and with live querying on."""
    service.clear_cache()
    monkeypatch.setattr(get_settings(), "live_data", True)
    yield
    service.clear_cache()


def live(transport, region=None, now=NOW):
    return asyncio.run(service.get_live(region, now=now, transport=transport))


def test_enlil_keeps_mars_and_the_newest_run_of_each_cme():
    arrivals = sources.parse_enlil(ENLIL)
    assert [a.simulation_id for a in arrivals] == ["WSA-ENLIL/49473/1", "WSA-ENLIL/49326/1"]
    assert arrivals[0].glancing_blow and arrivals[0].speed_km_s == 640.0
    assert arrivals[1].minor_impact


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (datetime(2026, 11, 10, 13, tzinfo=UTC), "WSA-ENLIL/49473/1"),  # 71 h antes
        (datetime(2026, 11, 15, 11, tzinfo=UTC), "WSA-ENLIL/49473/1"),  # 47 h after
        (datetime(2026, 11, 15, 13, tzinfo=UTC), None),  # 49 h after: no longer
        (datetime(2026, 11, 5, 0, tzinfo=UTC), "WSA-ENLIL/49326/1"),
    ],
)
def test_solar_alert_window(now, expected):
    alert = sources.solar_alert(sources.parse_enlil(ENLIL), now)
    assert (alert.simulation_id if alert else None) == expected


def test_alert_prefers_the_arrival_still_to_come():
    arrivals = sources.parse_enlil(ENLIL)
    # 2026-11-06: the 11-04 one arrived 40 h ago, the 11-13 one comes in 174 h (outside): old stays.
    assert sources.solar_alert(arrivals, datetime(2026, 11, 6, tzinfo=UTC)).minor_impact
    # 2026-11-11: the 11-13 one arrives in 48 h and is the only one inside.
    alert = sources.solar_alert(arrivals, datetime(2026, 11, 11, 12, tzinfo=UTC))
    assert alert.simulation_id == "WSA-ENLIL/49473/1"


def test_waypoints_return_the_last_position():
    rover = sources.parse_waypoints(WAYPOINTS)
    assert (rover["sol"], rover["site"], rover["drive"]) == (2022, 93, 0)
    assert rover["lat"] == pytest.approx(18.43559434) and rover["odometry_km"] == 45.25


def test_raw_images_skip_thumbnails_and_repeat_cameras():
    latest_sol, images = sources.parse_raw_images(RAW_IMAGES)
    assert latest_sol == 2031
    assert [i.camera for i in images] == ["SUPERCAM_RMI", "NAVCAM_LEFT"]
    assert images[0].taken_utc.tzinfo is not None


def test_live_reads_the_three_sources():
    res = live(httpx.MockTransport(nasa))
    assert {res.space_weather.source.status, res.rover.source.status, res.images.source.status} == {
        "live"
    }
    assert res.space_weather.alert.simulation_id == "WSA-ENLIL/49473/1"
    assert res.space_weather.source.provenance == "modeled"
    assert res.rover.source.provenance == "observed" and res.rover.distance_to_base_km is None
    assert len(res.images.images) == 2


def test_rover_distance_to_the_base_of_a_region(assets_dir):
    res = live(httpx.MockTransport(nasa), region=load_manifest("test"))
    # Base of the test region at (0.5, 0.0): the rover is thousands of km away and outside the bbox.
    assert res.rover.in_region is False and res.rover.distance_to_base_km > 1000


def test_cache_avoids_asking_nasa_again():
    calls = []

    def counting(request):
        calls.append(request.url.path)
        return nasa(request)

    live(httpx.MockTransport(counting))
    live(httpx.MockTransport(counting))
    assert len(calls) == 3


def test_without_internet_it_uses_the_snapshot_and_says_so():
    res = live(httpx.MockTransport(offline))
    snap = service.read_snapshot()
    for key, src in [
        ("space_weather", res.space_weather.source),
        ("rover", res.rover.source),
        ("images", res.images.source),
    ]:
        assert src.status == "snapshot" and src.error == "no connection to NASA"
        assert src.fetched_at == sources.parse_time(snap[key]["fetched_at"])
    assert res.rover.sol >= 2022


def test_nasa_error_after_a_good_answer_keeps_the_good_answer():
    live(httpx.MockTransport(nasa))
    later = datetime(2026, 11, 14, 21, tzinfo=UTC)
    res = live(httpx.MockTransport(lambda r: httpx.Response(429)), now=later)
    assert res.space_weather.source.status == "live"
    assert res.space_weather.source.error == "NASA answered 429"
    assert res.space_weather.source.fetched_at == NOW


def test_snapshot_file_has_the_three_sources():
    snap = service.read_snapshot()
    assert set(snap) == {"space_weather", "rover", "images"}
    for part in snap.values():
        assert sources.parse_time(part["fetched_at"]) is not None


def test_live_endpoint_works_offline(assets_dir, monkeypatch):
    monkeypatch.setattr(get_settings(), "live_data", False)
    res = TestClient(create_app()).get("/live", params={"region": "test"})
    assert res.status_code == 200
    body = res.json()
    assert body["rover"]["source"]["status"] == "snapshot"
    assert body["rover"]["in_region"] is False
    assert body["space_weather"]["alert_before_h"] == sources.SOLAR_ALERT_BEFORE_H


def test_live_endpoint_unknown_region_is_404(assets_dir, monkeypatch):
    monkeypatch.setattr(get_settings(), "live_data", False)
    assert TestClient(create_app()).get("/live", params={"region": "nope"}).status_code == 404


def test_snapshot_update_keeps_the_old_part_of_a_failing_source():
    def images_down(request):
        if request.url.params.get("feed") == "raw_images":
            return httpx.Response(503)
        return nasa(request)

    old = {"images": {"fetched_at": "2026-11-01T00:00:00+00:00", "data": {"images": []}}}
    new, errors = asyncio.run(service.build_snapshot(old, httpx.MockTransport(images_down)))
    assert errors == {"images": "NASA answered 503"}
    assert new["images"] == old["images"]
    assert new["rover"]["data"]["sol"] == 2022 and len(new["space_weather"]["data"]) == 2
