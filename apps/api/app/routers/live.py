from fastapi import APIRouter

from app.live.service import get_live
from app.schemas.live import LiveResponse
from app.storage import load_manifest

router = APIRouter(tags=["live"])


@router.get("/live", response_model=LiveResponse)
async def live(region: str | None = None) -> LiveResponse:
    """Marte hoy: llegadas de eyecciones solares (DONKI), posición de Perseverance y sus últimas
    imágenes. Si NASA no responde, devuelve la copia guardada e indica de cuándo es."""
    return await get_live(load_manifest(region) if region else None)
