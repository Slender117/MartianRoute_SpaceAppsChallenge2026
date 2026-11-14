from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.engine.pathfind import NoPathError
from app.geo import OutOfRegionError
from app.routers import assumptions, health, live, regions, routes
from app.storage import NotFoundError, RegionDataError

# Código HTTP de cada error del dominio. El mensaje llega a la UI en `detail`.
ERROR_STATUS: dict[type[Exception], int] = {
    NotFoundError: 404,
    NoPathError: 422,
    OutOfRegionError: 422,
    RegionDataError: 503,
}


def _domain_error(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=ERROR_STATUS[type(exc)], content={"detail": str(exc)})


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Martian Route API", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # El mapa de regreso seguro y la comparación de rutas pesan cientos de KB: comprimirlos.
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    for error in ERROR_STATUS:
        app.add_exception_handler(error, _domain_error)

    app.include_router(health.router)
    app.include_router(regions.router)
    app.include_router(routes.router)
    app.include_router(assumptions.router)
    app.include_router(live.router)

    # En desarrollo servimos los assets locales para no depender de R2.
    if settings.assets_dir and Path(settings.assets_dir).is_dir():
        app.mount("/assets", StaticFiles(directory=settings.assets_dir), name="assets")

    return app


app = create_app()
