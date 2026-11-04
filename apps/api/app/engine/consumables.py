"""Tiempo de caminata, consumo y dosis estimados a lo largo de la ruta.

Las fuentes de cada constante están en docs/supuestos.md y en GET /assumptions.
"""

import numpy as np

SOL_HOURS = 24.6598
# Velocidad base de un astronauta con traje sobre terreno plano (km/h).
BASE_SPEED_KMH = 2.5
# Consumo metabólico de O₂ durante una EVA activa (kg/h por persona), valor de referencia.
O2_KG_PER_HOUR = 0.07
# La EVA se hace en pareja.
CREW_SIZE = 2
# Fracción de la autonomía del traje que no se planea gastar.
AUTONOMY_RESERVE = 0.20
# Dosis equivalente en la superficie medida por Curiosity RAD, en mSv por día terrestre.
RAD_MSV_PER_DAY = 0.64
RAD_MSV_PER_DAY_ERROR = 0.12
# Dosis absorbida del mayor evento solar medido por RAD hasta 2024 (mGy). No se suma a la dosis
# equivalente de fondo: convertirla a mSv requiere el factor de calidad de ese evento.
SOLAR_EVENT_MGY = 8.1


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
    return autonomy_h * (1 - AUTONOMY_RESERVE)


def point_of_no_return(elapsed_h: np.ndarray, back_h: np.ndarray, usable_h: float) -> int | None:
    """Primer índice desde donde el regreso ya no alcanza con la autonomía utilizable.

    En terreno plano es la mitad de esa autonomía. En pendiente se usa el tiempo real de regreso,
    porque subir de vuelta lo que se bajó de ida tarda más.
    """
    idx = np.nonzero(elapsed_h + back_h >= usable_h)[0]
    return int(idx[0]) if idx.size else None


def radiation_dose_msv(duration_h: float) -> float:
    return duration_h / 24.0 * RAD_MSV_PER_DAY
