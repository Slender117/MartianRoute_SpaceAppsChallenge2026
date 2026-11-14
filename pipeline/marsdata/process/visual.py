"""Productos solo visuales para la vista 3D: ortofoto como textura y capa de clases coloreada.

Nada de esto entra al ruteo: la API usa las grillas .npy. Las texturas se estiran de borde a borde
de la malla, así que cubren el bbox (no la grilla de la API, que sobresale media celda).
"""

from pathlib import Path

import numpy as np
from rasterio.warp import Resampling

from marsdata.process.classes import ClassCounts, ClassInfo
from marsdata.process.reproject import warp_to_region
from marsdata.region import Region

# Píxeles de la ortofoto por celda de la grilla (600 celdas -> 2400 px).
ORTHO_PX_PER_CELL = 4
# Opacidad de la capa de clases: deja ver el relieve y la ortofoto debajo.
CLASS_ALPHA = 0.6
# Paleta de Okabe e Ito (distinguible con daltonismo), por código de grupo de NOAH-H.
NOAHH_COLORS = {
    1: "#F0E442",  # no roca madre: amarillo
    2: "#009E73",  # roca madre: verde azulado
    3: "#E69F00",  # campos de rocas: naranja
    4: "#56B4E9",  # ondulaciones pequeñas: azul cielo
    5: "#CC79A7",  # ondulaciones grandes: púrpura rojizo
}
FALLBACK_COLORS = ["#0072B2", "#D55E00", "#999999", "#F5C710", "#61D04F"]


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def ortho_texture(path: Path, region: Region) -> np.ndarray:
    """Ortofoto en escala de grises (uint8) sobre el bbox, con contraste estirado al 1-99 %."""
    n = region.size * ORTHO_PX_PER_CELL
    img = warp_to_region(path, region, Resampling.average, shape=(n, n), bounds=region.bbox)
    valid = np.isfinite(img)
    if not valid.any():
        raise ValueError(f"{path.name} no cubre la región")
    lo, hi = np.percentile(img[valid], [1, 99])
    out = np.clip((img - lo) / max(hi - lo, 1e-6) * 255, 0, 255)
    return np.where(valid, out, 0).astype(np.uint8)


def class_colors(info: list[ClassInfo]) -> dict[int, str]:
    return {
        c.code: NOAHH_COLORS.get(c.code, FALLBACK_COLORS[i % len(FALLBACK_COLORS)])
        for i, c in enumerate(info)
    }


def class_texture(counts: ClassCounts, colors: dict[int, str]) -> np.ndarray:
    """RGBA: cada texel mezcla los colores según la fracción de cada clase; transparente sin dato.

    La mezcla suaviza los bordes entre clases, y la opacidad baja donde parte del texel no tiene
    clase (borde del mosaico).
    """
    n = counts.classified
    frac = np.where(n > 0, counts.counts / np.maximum(n, 1), 0.0)  # (K, H, W)
    palette = np.array([_rgb(colors[c]) for c in counts.codes], dtype=np.float64)  # (K, 3)
    rgb = np.einsum("khw,kc->hwc", frac, palette)
    alpha = counts.valid * CLASS_ALPHA * 255
    return np.dstack([rgb, alpha]).round().clip(0, 255).astype(np.uint8)


def legend(info: list[ClassInfo], colors: dict[int, str], counts: ClassCounts) -> list[dict]:
    """Leyenda de la capa de clases, con la fracción del área con dato que ocupa cada una."""
    total = counts.classified.sum()
    shares = counts.counts.sum(axis=(1, 2)) / total if total else np.zeros(len(info))
    by_code = dict(zip(counts.codes, shares, strict=True))
    return [
        {
            "code": c.code,
            "name": c.name,
            "color": colors[c.code],
            "risk": c.risk,
            "share": round(float(by_code.get(c.code, 0.0)), 4),
        }
        for c in info
    ]
