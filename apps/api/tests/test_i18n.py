"""Textos en inglés: la API manda lo necesario para que la web cambie de idioma."""

from fastapi.testclient import TestClient

from app.engine.assumptions import LIMITS, build_assumptions
from app.engine.assumptions_en import LIMITS_EN, PARAMETERS_EN
from app.main import create_app


def test_every_parameter_has_an_english_label():
    ids = {p.id for p in build_assumptions().parameters}
    assert ids - PARAMETERS_EN.keys() == set()


def test_every_limit_has_an_english_version():
    assert len(LIMITS_EN) == len(LIMITS)


def test_assumptions_in_english_keep_values_and_sources(assets_dir):
    client = TestClient(create_app())
    es = client.get("/assumptions").json()
    en = client.get("/assumptions", params={"lang": "en"}).json()

    assert [p["id"] for p in en["parameters"]] == [p["id"] for p in es["parameters"]]
    by_id = {p["id"]: p for p in en["parameters"]}
    assert by_id["autonomy"]["label"] == "Suit autonomy"
    assert (
        by_id["autonomy"]["value"]
        == next(p for p in es["parameters"] if p["id"] == "autonomy")["value"]
    )
    assert by_id["weights_safe"]["value"].startswith("slope ")
    assert by_id["crew_size"]["source"] == "Project decision"
    assert by_id["o2_rate"]["source"] == "Waligora and Horrigan (1975), table 2; Weir (1949)"
    assert by_id["o2_rate"]["note"].startswith("Mean of the Apollo")
    assert en["limits"][0].startswith("While a region")


def test_unknown_language_is_rejected(assets_dir):
    r = TestClient(create_app()).get("/assumptions", params={"lang": "fr"})
    assert r.status_code == 422
