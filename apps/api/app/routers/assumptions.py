from typing import Literal

from fastapi import APIRouter

from app.engine.assumptions import build_assumptions
from app.engine.assumptions_en import to_english
from app.schemas.assumptions import AssumptionsResponse

router = APIRouter(tags=["assumptions"])


@router.get("/assumptions", response_model=AssumptionsResponse)
def get_assumptions(lang: Literal["es", "en"] = "es") -> AssumptionsResponse:
    """Parámetros del modelo con su fuente y límites conocidos, en español o en inglés."""
    res = build_assumptions()
    return to_english(res) if lang == "en" else res
