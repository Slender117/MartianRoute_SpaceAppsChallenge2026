"""Mapa de regreso seguro: cuánto se tarda en volver caminando a la base desde cada celda.

Un solo Dijkstra desde la base (`MCP_Geometric.find_costs`) da el tiempo de regreso a todas las
celdas a la vez. El costo de cada celda es el tiempo por metro, que hace la grilla simétrica:
se toma la más lenta entre subir y bajar esa pendiente, así el tiempo es una cota pesimista y vale
en los dos sentidos (plan B del equipo para el costo asimétrico).
"""

import base64

import numpy as np
from skimage.graph import MCP_Geometric

from app.engine.consumables import (
    radiation_dose_msv,
    usable_autonomy_h,
    walking_speed_kmh,
)
from app.geo import cell_size_m, latlon_to_cell
from app.schemas.route import LatLon, SuitLimits
from app.schemas.safe_return import SafeReturnResponse
from app.storage import RegionGrids, memoized

# Valor de "sin regreso posible" en la grilla de minutos (máximo de uint16).
NO_RETURN = np.iinfo(np.uint16).max


def time_per_meter_h(slope_deg: np.ndarray, max_slope_deg: float) -> np.ndarray:
    """Horas por metro horizontal en cada celda; infinito donde la pendiente es intransitable."""
    slope_rad = np.radians(slope_deg)
    grade = np.tan(slope_rad)
    slower_kmh = np.minimum(walking_speed_kmh(grade), walking_speed_kmh(-grade))
    # 1/cos: el metro horizontal es más largo sobre la pendiente.
    hours = 1.0 / (slower_kmh * 1000.0 * np.cos(slope_rad))
    return np.where(slope_deg > max_slope_deg, np.inf, hours)


def return_hours(grids: RegionGrids, base: LatLon, max_slope_deg: float) -> np.ndarray:
    """Horas de regreso a la base desde cada celda (infinito si no hay camino).

    Solo depende de la base y la pendiente máxima: se guarda por región (solo lectura), así que
    mover la autonomía del traje no repite el Dijkstra.
    """
    m = grids.manifest
    cell = latlon_to_cell(m, base.lat, base.lon)

    def compute() -> np.ndarray:
        cost = time_per_meter_h(grids.slope, max_slope_deg)
        mcp = MCP_Geometric(cost, fully_connected=True, sampling=cell_size_m(m))
        hours, _ = mcp.find_costs([cell])
        hours.setflags(write=False)
        return hours

    return memoized(grids, ("return_hours", cell, float(max_slope_deg)), compute)


def encode_minutes(hours: np.ndarray) -> str:
    """Minutos como uint16 little-endian en base64; NO_RETURN marca las celdas sin regreso."""
    minutes = np.where(np.isfinite(hours), np.round(hours * 60), NO_RETURN)
    minutes = np.clip(minutes, 0, NO_RETURN).astype("<u2")
    return base64.b64encode(minutes.tobytes()).decode("ascii")


def build_safe_return(
    grids: RegionGrids, base: LatLon | None, suit: SuitLimits
) -> SafeReturnResponse:
    m = grids.manifest
    node = base or m.base
    hours = return_hours(grids, node, suit.max_slope_deg)

    # Una celda es visitable si caben la ida, el trabajo fijo y el regreso. La ida tarda, como
    # mucho, lo mismo que el regreso (la grilla es simétrica y pesimista).
    planned_h = max(usable_autonomy_h(suit.autonomy_h) - suit.task_h, 0.0) / 2
    total_h = max(suit.autonomy_h - suit.task_h, 0.0) / 2
    reachable = np.isfinite(hours)
    return SafeReturnResponse(
        region=m.id,
        base=node,
        shape=m.shape,
        bbox=m.bbox,
        return_minutes=encode_minutes(hours),
        no_return_value=int(NO_RETURN),
        planned_limit_min=planned_h * 60,
        total_limit_min=total_h * 60,
        planned_area_fraction=float((hours <= planned_h).sum() / hours.size),
        total_area_fraction=float((hours <= total_h).sum() / hours.size),
        unreachable_fraction=float((~reachable).sum() / hours.size),
        max_eva_dose_msv=radiation_dose_msv(2 * planned_h + suit.task_h),
        synthetic_data=m.synthetic,
    )
