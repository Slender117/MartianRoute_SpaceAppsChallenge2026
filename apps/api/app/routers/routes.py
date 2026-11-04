from fastapi import APIRouter

from app.engine.planner import compare_routes, plan_route
from app.engine.validation import validate_traverse
from app.schemas.route import CompareRequest, RouteRequest, RouteResponse, WalkMode
from app.schemas.validation import ValidationRequest, ValidationResponse
from app.storage import load_region, load_traverse

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("", response_model=RouteResponse)
def create_route(req: RouteRequest) -> RouteResponse:
    grids = load_region(req.region)
    return plan_route(grids, req.start, req.end, req.mode, req.suit, req.solar_event)


@router.post("/compare", response_model=dict[WalkMode, RouteResponse])
def compare(req: CompareRequest) -> dict[WalkMode, RouteResponse]:
    grids = load_region(req.region)
    return compare_routes(grids, req.start, req.end, req.suit, req.solar_event)


@router.post("/validate", response_model=ValidationResponse)
def validate(req: ValidationRequest) -> ValidationResponse:
    """Métricas de las tres rutas contra el recorrido real de un rover."""
    grids = load_region(req.region)
    return validate_traverse(grids, req.rover, load_traverse(req.region, req.rover), req.suit)
