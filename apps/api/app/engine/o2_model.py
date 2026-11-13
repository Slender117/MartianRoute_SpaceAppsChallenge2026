"""Costo de O₂ de caminar según la pendiente, a partir de la curva de Minetti et al. (2002).

Es la parte física del modelo de Edgar (`science/model/eva_cost.py`), copiada al motor porque la
imagen de la API solo lleva `apps/api/`. La calibración de pesos (`science/model/calibrate.py`) no
viene aquí: es un script offline.

Dos usos en el motor:

1. `slope_penalty`: la forma de la penalización por pendiente en `engine/cost.py` (0 en plano,
   1 en la pendiente máxima). Decide la ruta.
2. `o2_interval_kg`: el O₂ de la EVA completa como intervalo (cota baja y alta). Solo se reporta,
   no cambia la ruta.

Por qué un intervalo: no hay fuente para cómo cambia el costo en plano con 0.38 g. En vez de
inventar un factor, la penalización por pendiente se escala entre dos casos extremos
(`gradient_scale_bounds`).
"""

import numpy as np

from app.engine.consumables import BASE_SPEED_KMH, O2_KG_PER_HOUR
from app.geo import MARS_RADIUS_M

G_EARTH_MS2 = 9.80665
# GM de Marte (m³/s²) del campo de gravedad JGMRO_120f: Konopliv et al. (2020),
# https://doi.org/10.1029/2020GL090568
GM_MARS_M3_S2 = 42_828.3748574e9
# Gravedad en la superficie (m/s²) = GM / R², con el radio medio del proyecto: unos 3.73, 0.38 g.
# No descuenta la rotación de Marte, que la baja menos de 0.5 %.
G_MARS_MS2 = GM_MARS_M3_S2 / MARS_RADIUS_M**2

# O₂ por metro en plano, por astronauta: tasa por hora ÷ velocidad en plano. Hereda el `[__]` de
# esas dos cifras (docs/supuestos.md) y absorbe el efecto del traje.
O2_FLAT_KG_PER_M = O2_KG_PER_HOUR / (BASE_SPEED_KMH * 1000)

# Costo de caminar (J/kg/m) según la pendiente (subida ÷ avance), de Minetti et al. (2002):
# 3.46 a -45 %, 0.81 a -10 %, 1.64 en plano y 17.33 a +45 %. Entre nudos se interpola en línea
# recta y fuera de ±45 % se satura. Con el polinomio del artículo completo, sustituir estos nudos.
_GRADE_KNOTS = np.array([-0.45, -0.10, 0.0, 0.45])
_COST_KNOTS = np.array([3.46, 0.81, 1.64, 17.33])
_FLAT_COST = _COST_KNOTS[2]


def gradient_scale_bounds(g_ms2: float = G_MARS_MS2) -> tuple[float, float]:
    """Cotas de la escala `s` de la penalización por pendiente a una gravedad dada.

    Subir una masa cuesta en proporción a la gravedad; el costo en plano, no se sabe. Si no cambia
    con la gravedad, `s` = g/g_Tierra (cota baja); si cambia en proporción, `s` = 1 (cota alta).
    """
    return g_ms2 / G_EARTH_MS2, 1.0


def o2_multiplier(grade: np.ndarray, s: float = 1.0) -> np.ndarray:
    """O₂ por metro respecto al plano, para una pendiente con signo (positiva = subida)."""
    return 1.0 + s * (np.interp(grade, _GRADE_KNOTS, _COST_KNOTS) - _FLAT_COST) / _FLAT_COST


def round_trip_multiplier(grade: np.ndarray, s: float = 1.0) -> np.ndarray:
    """Promedio de ida y vuelta por el mismo camino: lo que se sube de ida se baja de vuelta."""
    g = np.abs(grade)
    return 0.5 * (o2_multiplier(g, s) + o2_multiplier(-g, s))


def slope_penalty(slope_deg: np.ndarray, max_slope_deg: float) -> np.ndarray:
    """Penalización por pendiente normalizada: 0 en plano y 1 en la pendiente máxima del traje.

    Sustituye a (pendiente/máx)². Es el O₂ extra de ida y vuelta respecto al plano, dividido entre
    el de la pendiente máxima. La escala `s` multiplica numerador y denominador y se cancela, así
    que la gravedad no cambia la ruta: solo el O₂ que se reporta.
    """

    def extra(deg: np.ndarray | float) -> np.ndarray:
        return round_trip_multiplier(np.tan(np.radians(deg))) - 1.0

    return np.clip(extra(slope_deg) / extra(max_slope_deg), 0.0, 1.0)


def route_o2_kg(
    path: np.ndarray,
    dem: np.ndarray,
    cell_m: tuple[float, float],
    s: float = 1.0,
    o2_flat_kg_per_m: float = O2_FLAT_KG_PER_M,
) -> float:
    """O₂ de ida y vuelta por el mismo camino, por astronauta, con la pendiente de cada segmento."""
    steps = np.diff(path, axis=0)
    horizontal = np.hypot(steps[:, 0] * cell_m[0], steps[:, 1] * cell_m[1])
    dz = np.diff(dem[path[:, 0], path[:, 1]].astype(float))
    grade = dz / horizontal  # una ruta nunca repite celda seguida: horizontal > 0
    dist = np.hypot(horizontal, dz)
    # Ida con `grade` y vuelta con `-grade`, sobre la misma distancia.
    per_m = o2_multiplier(grade, s) + o2_multiplier(-grade, s)
    return float(o2_flat_kg_per_m * np.sum(dist * per_m))


def o2_interval_kg(
    path: np.ndarray,
    dem: np.ndarray,
    cell_m: tuple[float, float],
    g_ms2: float = G_MARS_MS2,
) -> tuple[float, float]:
    """O₂ de la EVA completa por astronauta, entre las dos cotas de gravedad (baja, alta)."""
    lo, hi = gradient_scale_bounds(g_ms2)
    return route_o2_kg(path, dem, cell_m, lo), route_o2_kg(path, dem, cell_m, hi)
