from fastapi import APIRouter

from app.schemas.region import RegionManifest, RegionSummary
from app.storage import list_regions, load_manifest, load_traverse

router = APIRouter(prefix="/regions", tags=["regions"])


@router.get("", response_model=list[RegionSummary])
def get_regions() -> list[RegionManifest]:
    return list_regions()


@router.get("/{region_id}", response_model=RegionManifest)
def get_region(region_id: str) -> RegionManifest:
    return load_manifest(region_id)


@router.get("/{region_id}/traverse/{rover}")
def get_traverse(region_id: str, rover: str) -> dict:
    """The rover's real traverse as GeoJSON, to compare with the proposed route."""
    return load_traverse(region_id, rover)
