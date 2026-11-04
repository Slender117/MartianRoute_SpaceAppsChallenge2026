from fastapi import APIRouter

from app.engine.assumptions import build_assumptions
from app.schemas.assumptions import AssumptionsResponse

router = APIRouter(tags=["assumptions"])


@router.get("/assumptions", response_model=AssumptionsResponse)
def get_assumptions() -> AssumptionsResponse:
    """Parámetros del modelo con su fuente y límites conocidos."""
    return build_assumptions()
