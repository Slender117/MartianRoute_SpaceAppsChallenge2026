from fastapi import APIRouter

from app.live.service import get_live
from app.schemas.live import LiveResponse
from app.storage import load_manifest

router = APIRouter(tags=["live"])


@router.get("/live", response_model=LiveResponse)
async def live(region: str | None = None) -> LiveResponse:
    """Mars today: solar ejection arrivals (DONKI), Perseverance's position and its latest
    images. If NASA does not answer, it returns the saved copy and says when it is from."""
    return await get_live(load_manifest(region) if region else None)
