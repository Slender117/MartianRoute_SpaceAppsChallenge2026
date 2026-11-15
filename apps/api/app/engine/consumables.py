"""Tiempo de caminata, consumo y dosis estimados a lo largo de la ruta.

Las fuentes de cada constante están en docs/supuestos.md y en GET /assumptions.
"""

import numpy as np

SOL_HOURS = 24.6598
# Velocidad base de un astronauta con traje sobre terreno plano (km/h): ritmo lunar sobre regolito
# casi plano de Coan (2020), aplicado a Marte.
BASE_SPEED_KMH = 2.0
# Consumo metabólico de O₂ durante una EVA activa (kg/h por persona): la media de las EVA lunares
# de Apollo (234 kcal/h, Waligora y Horrigan, 1975) da 0.066 a 0.071 kg/h con Weir (1949).
O2_KG_PER_HOUR = 0.07
# La EVA se hace en pareja.
CREW_SIZE = 2
# Fracción de la autonomía del traje que no se planea gastar.
AUTONOMY_RESERVE = 0.20
# Reserva mínima al volver a la base (30 min, decisión del plan del equipo). Se aplica la más
# estricta entre esta y AUTONOMY_RESERVE: ver usable_autonomy_h.
WALKBACK_RESERVE_H = 0.5
# Dosis equivalente en la superficie medida por Curiosity RAD, en mSv por día terrestre.
RAD_MSV_PER_DAY = 0.64
RAD_MSV_PER_DAY_ERROR = 0.12
# Dosis absorbida del mayor evento solar medido por RAD hasta 2024 (mGy). No se suma a la dosis
# equivalente de fondo: convertirla a mSv requiere el factor de calidad de ese evento.
SOLAR_EVENT_MGY = 8.1
# Límite de dosis efectiva de carrera de NASA-STD-3001 Vol. 1 Rev. C [V1 4030] (mSv). No hay límite
# por EVA: este valor solo se informa, no dispara alertas.
CAREER_DOSE_LIMIT_MSV = 600.0


def walking_speed_kmh(grade: np.ndarray) -> np.ndarray:
    """Función de Tobler escalada para que el terreno plano dé la velocidad base."""
    return BASE_SPEED_KMH * np.exp(-3.5 * (np.abs(grade + 0.05) - 0.05))


def segment_profile(
    path: np.ndarray, dem: np.ndarray, cell_m: tuple[float, float]
) -> tuple[np.ndarray, np.ndarray]:
    """Distancia (m) y tiempo (h) de cada segmento de la ruta, en el sentido en que se recorre."""
    steps = np.diff(path, axis=0)
    horizontal = np.hypot(steps[:, 0] * cell_m[0], steps[:, 1] * cell_m[1])
    elev = dem[path[:, 0], path[:, 1]].astype(float)
    dz = np.diff(elev)
    grade = np.divide(dz, horizontal, out=np.zeros_like(dz), where=horizontal > 0)
    dist = np.hypot(horizontal, dz)
    hours = (dist / 1000.0) / walking_speed_kmh(grade)
    return dist, hours


def ascent_m(path: np.ndarray, dem: np.ndarray) -> float:
    """Desnivel positivo acumulado a lo largo de la ruta."""
    dz = np.diff(dem[path[:, 0], path[:, 1]].astype(float))
    return float(dz[dz > 0].sum())


def usable_autonomy_h(autonomy_h: float) -> float:
    """Autonomía planeable: la autonomía menos la reserva más estricta (20 % o 30 min).

    Con 8 h manda el 20 % (1.6 h); con menos de 2.5 h de traje manda la reserva de 30 min. Una sola
    regla alimenta la factibilidad, el punto de no retorno y el mapa de regreso seguro.
    """
    return autonomy_h - max(AUTONOMY_RESERVE * autonomy_h, WALKBACK_RESERVE_H)


def point_of_no_return(elapsed_h: np.ndarray, back_h: np.ndarray, budget_h: float) -> int | None:
    """Primer índice donde lo gastado más el regreso a pie ya no cabe en el presupuesto.

    `budget_h` es la autonomía planeable menos el trabajo fijo. En terreno plano cae a la mitad
    del presupuesto; en pendiente se usa el tiempo real de regreso, porque
    subir de vuelta lo que se bajó de ida tarda más.
    """
    idx = np.nonzero(elapsed_h + back_h >= budget_h)[0]
    return int(idx[0]) if idx.size else None


def radiation_dose_msv(duration_h: float) -> float:
    return duration_h / 24.0 * RAD_MSV_PER_DAY
