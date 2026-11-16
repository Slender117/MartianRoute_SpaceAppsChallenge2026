from fastapi import APIRouter

from app.engine.planner import compare_routes, plan_route
from app.engine.safe_return import build_safe_return
from app.engine.validation import validate_traverse
from app.schemas.route import CompareRequest, RouteRequest, RouteResponse, WalkMode
from app.schemas.safe_return import SafeReturnRequest, SafeReturnResponse
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
    """Metrics of the three routes against a rover's real traverse."""
    grids = load_region(req.region)
    return validate_traverse(grids, req.rover, load_traverse(req.region, req.rover), req.suit)


@router.post("/safe-return", response_model=SafeReturnResponse)
def safe_return(req: SafeReturnRequest) -> SafeReturnResponse:
    """Safe-return map: minutes to walk back to base from each cell."""
    return build_safe_return(load_region(req.region), req.base, req.suit)
