import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.engine.assumptions import PENDING_SOURCE
from app.main import create_app
from app.storage import load_manifest

BODY = {
    "region": "test",
    "start": {"lat": 0.9, "lon": 0.1},
    "end": {"lat": 0.9, "lon": 0.9},
}
SUPUESTOS = Path(__file__).resolve().parents[3] / "docs" / "supuestos.md"


@pytest.fixture
def client(assets_dir) -> TestClient:
    return TestClient(create_app())


def test_regions_and_route(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert [r["id"] for r in client.get("/regions").json()] == ["test"]

    r = client.post("/routes", json=BODY)
    assert r.status_code == 200
    assert r.json()["mode"] == "safe"

    r = client.post("/routes/compare", json=BODY)
    assert set(r.json()) == {"safe", "fast", "science"}


def test_start_is_optional(client):
    r = client.post("/routes", json={"region": "test", "end": BODY["end"]})
    assert r.status_code == 200
    assert r.json()["path"][0]["lon"] == pytest.approx(0.0, abs=0.01)


def test_solar_event_reaches_the_response(client):
    r = client.post("/routes", json={**BODY, "solar_event": True})
    assert r.json()["solar_event_mgy"] > 0


def test_unknown_region_is_404(client):
    r = client.post(
        "/routes",
        json={"region": "nope", "start": {"lat": 0, "lon": 0}, "end": {"lat": 1, "lon": 1}},
    )
    assert r.status_code == 404
    assert client.get("/regions/nope").status_code == 404


def test_region_id_cannot_leave_the_assets_folder(client, assets_dir):
    (assets_dir.parent / "manifest.json").write_text("{}", encoding="utf-8")
    r = client.post("/routes", json={**BODY, "region": ".."})
    assert r.status_code == 404


def test_unknown_rover_is_404(client):
    assert client.get("/regions/test/traverse/curiosity").status_code == 404
    r = client.post("/routes/validate", json={"region": "test", "rover": "curiosity"})
    assert r.status_code == 404


@pytest.mark.parametrize(
    "change, detail",
    [
        ({"end": {"lat": 5.0, "lon": 0.9}}, "fuera de la región"),
        ({"end": {"lat": 0.5, "lon": 0.51}}, "no es caminable"),
        ({"end": BODY["start"]}, "misma celda"),
    ],
)
def test_impossible_route_is_422_with_a_reason(client, change, detail):
    r = client.post("/routes", json={**BODY, **change})
    assert r.status_code == 422
    assert detail in r.json()["detail"]


def test_no_route_is_422(assets_dir, flat_grids):
    flat_grids.slope[:, 30] = 45.0
    np.save(assets_dir / "test" / "slope.npy", flat_grids.slope)
    r = TestClient(create_app()).post("/routes", json=BODY)
    assert r.status_code == 422
    assert "No existe una ruta" in r.json()["detail"]


@pytest.mark.parametrize("lon", [181.0, 257.45, -181.0])
def test_longitude_outside_convention_is_rejected(client, lon):
    r = client.post("/routes", json={**BODY, "end": {"lat": 0.9, "lon": lon}})
    assert r.status_code == 422


def _rewrite_manifest(assets_dir: Path, **changes) -> None:
    path = assets_dir / "test" / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps({**manifest, **changes}), encoding="utf-8")
    load_manifest.cache_clear()


def test_manifest_with_longitudes_from_0_to_360_is_503(client, assets_dir):
    _rewrite_manifest(assets_dir, bbox=[0.0, 0.0, 361.0, 1.0])
    assert client.get("/regions/test").status_code == 503


def test_file_with_wrong_checksum_is_503(client, assets_dir):
    _rewrite_manifest(assets_dir, checksums={"dem.npy": "0" * 64})
    r = client.post("/routes", json=BODY)
    assert r.status_code == 503
    assert "checksum" in r.json()["detail"]


def test_file_with_correct_checksum_loads(client, assets_dir):
    digest = hashlib.sha256((assets_dir / "test" / "dem.npy").read_bytes()).hexdigest()
    _rewrite_manifest(assets_dir, checksums={"dem.npy": digest})
    assert client.post("/routes", json=BODY).status_code == 200


def test_grid_with_wrong_shape_is_503(client, assets_dir):
    _rewrite_manifest(assets_dir, shape=[10, 10])
    r = client.post("/routes", json=BODY)
    assert r.status_code == 503
    assert "mide" in r.json()["detail"]


def test_missing_index_is_503(client, assets_dir):
    (assets_dir / "index.json").unlink()
    r = client.get("/regions")
    assert r.status_code == 503
    assert "index.json" in r.json()["detail"]


def test_validate_endpoint_reports_three_modes(client):
    r = client.post("/routes/validate", json={"region": "test", "rover": "rover"})
    assert r.status_code == 200
    body = r.json()
    assert set(body["routes"]) == {"safe", "fast", "science"}
    assert body["traverse"]["distance_km"] > 0
    assert body["routes"]["safe"]["mean_separation_m"] >= 0


def test_assumptions_have_a_source_or_the_pending_marker(client):
    body = client.get("/assumptions").json()

    assert body["limits"]
    by_id = {p["id"]: p for p in body["parameters"]}
    assert all(p["source"] for p in body["parameters"])
    assert by_id["radiation_rate"]["source"] == "Hassler et al. (2014)"
    assert by_id["o2_rate"]["source"] == PENDING_SOURCE
    assert by_id["max_dose"]["value"] is None


def test_every_assumption_is_documented(client):
    documented = SUPUESTOS.read_text(encoding="utf-8")
    ids = [p["id"] for p in client.get("/assumptions").json()["parameters"]]
    assert [pid for pid in ids if f"`{pid}`" not in documented] == []
