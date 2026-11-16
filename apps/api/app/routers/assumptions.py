from typing import Literal

from fastapi import APIRouter

from app.engine.assumptions import build_assumptions
from app.engine.assumptions_en import to_english
from app.schemas.assumptions import AssumptionsResponse

router = APIRouter(tags=["assumptions"])


@router.get("/assumptions", response_model=AssumptionsResponse)
def get_assumptions(lang: Literal["es", "en"] = "en") -> AssumptionsResponse:
    """Model parameters with their sources and known limits, in English (default) or Spanish."""
    res = build_assumptions()
    return to_english(res) if lang == "en" else res
