"""Costo de O₂ de una EVA a pie según la pendiente y la gravedad.

La forma de la curva sale de Minetti et al. (2002), medida en 1 g y sin traje. Aquí solo se usa
para saber cuánto más (o menos) cuesta cada metro respecto al terreno plano. El nivel absoluto de
O₂ en plano lo pone el proyecto (`o2_flat_kg_per_m`; hoy `[__]` en docs/supuestos.md), así que el
modelo no necesita el factor de conversión energía a O₂ ni la masa del astronauta, y absorbe el
efecto del traje en ese nivel.

Lo que sigue sin fuente es cómo cambia el costo en plano con la gravedad. En vez de inventar un
factor, la penalización por pendiente se acota entre dos casos extremos y la salida es un
intervalo (`o2_interval_kg`).
"""

import numpy as np

G_EARTH = 9.80665  # m/s²

# Costo de caminar (J/kg/m) a distintas pendientes (subida/avance). Valores del resumen de Minetti
# et al. (2002): 1.64 en plano (mínimo, a 1.0 m/s), 0.81 a -10 %, 3.46 a -45 % y 17.33 a +45 %.
# Entre nudos se interpola y fuera de ±0.45 se satura.
# ponytail: cuatro nudos del resumen; con el texto completo, sustituir por su polinomio.
_GRADE = np.array([-0.45, -0.10, 0.0, 0.45])
_COST = np.array([3.46, 0.81, 1.64, 17.33])


def gradient_scale_bounds(g_ms2: float) -> tuple[float, float]:
    """Cotas de la escala `s` de la penalización por pendiente; no hay fuente para el valor central.

    El trabajo de subir una masa es proporcional a la gravedad, pero el costo en plano puede no
    serlo: si no cambia con la gravedad, `s` = g/g_Tierra; si es proporcional, `s` = 1.
    """
    return g_ms2 / G_EARTH, 1.0


def o2_multiplier(grade: np.ndarray, s: float = 1.0) -> np.ndarray:
    """O₂ por metro respecto al terreno plano, para una pendiente con signo (positiva = subida)."""
    flat = _COST[2]
    return 1.0 + s * (np.interp(grade, _GRADE, _COST) - flat) / flat


def round_trip_multiplier(grade: np.ndarray, s: float = 1.0) -> np.ndarray:
    """Promedio por sentido de una EVA que vuelve por el mismo camino.

    Lo que se sube de ida se baja de vuelta.
    """
    g = np.abs(grade)
    return 0.5 * (o2_multiplier(g, s) + o2_multiplier(-g, s))


def slope_penalty(slope_deg: np.ndarray, max_slope_deg: float) -> np.ndarray:
    """Penalización por pendiente normalizada a 0–1 en la pendiente máxima.

    Sustituye a (pendiente/máx)².

    Es el encaje mínimo en `engine/cost.py`: conserva la estructura y los pesos por modo del equipo.
    No depende de la gravedad: `s` multiplica el numerador y el denominador y se cancela, así que
    la gravedad solo cambia el O₂ que se reporta (`o2_interval_kg`) y no la ruta.
    """

    def extra(deg):
        return round_trip_multiplier(np.tan(np.radians(deg))) - 1.0

    return np.clip(extra(slope_deg) / extra(max_slope_deg), 0.0, 1.0)


def cell_cost(
    slope_deg: np.ndarray,
    hazard: np.ndarray,
    thermal_inertia: np.ndarray,
    w_hazard: float,
    w_instability: float,
    s: float = 1.0,
    max_slope_deg: float | None = None,
) -> np.ndarray:
    """Costo por celda en unidades físicas.

    Vale 1 en plano sin riesgo y, en pendiente, el O₂ relativo al plano.

    Ignora los pesos de pendiente por modo, así que los tres modos solo se distinguirían por riesgo.
    """
    cost = (
        round_trip_multiplier(np.tan(np.radians(slope_deg)), s)
        + w_hazard * hazard
        + w_instability * (1.0 - thermal_inertia)
    )
    if max_slope_deg is not None:
        cost = np.where(slope_deg > max_slope_deg, np.inf, cost)
    return cost


def route_o2_kg(
    path: np.ndarray,
    dem: np.ndarray,
    cell_m: tuple[float, float],
    o2_flat_kg_per_m: float,
    s: float = 1.0,
) -> float:
    """O₂ de ida y vuelta por el mismo camino, usando la pendiente real de cada segmento."""
    steps = np.diff(path, axis=0)
    horizontal = np.hypot(steps[:, 0] * cell_m[0], steps[:, 1] * cell_m[1])
    dz = np.diff(dem[path[:, 0], path[:, 1]].astype(float))
    grade = dz / horizontal
    dist = np.hypot(horizontal, dz)
    return float(
        o2_flat_kg_per_m * np.sum(dist * (o2_multiplier(grade, s) + o2_multiplier(-grade, s)))
    )


def o2_interval_kg(
    path: np.ndarray,
    dem: np.ndarray,
    cell_m: tuple[float, float],
    o2_flat_kg_per_m: float,
    g_ms2: float,
) -> tuple[float, float]:
    """Intervalo de O₂ de la EVA completa entre las dos cotas de gravedad.

    El efecto del traje va dentro de `o2_flat_kg_per_m`.
    """
    lo, hi = gradient_scale_bounds(g_ms2)
    return (
        route_o2_kg(path, dem, cell_m, o2_flat_kg_per_m, lo),
        route_o2_kg(path, dem, cell_m, o2_flat_kg_per_m, hi),
    )
