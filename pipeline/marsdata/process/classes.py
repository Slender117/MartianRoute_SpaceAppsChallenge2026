"""Capas categóricas (NOAH-H) llevadas a una grilla: píxeles de cada clase que caen en cada celda.

Un mosaico de 25 cm tiene miles de píxeles por celda de la región, y promediar códigos de clase no
tiene sentido: se cuentan. De los conteos salen el riesgo medio, la fracción de una clase y la clase
dominante. El mosaico se lee por franjas y submuestreado, sin cargarlo entero en memoria.
"""

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from marsdata.process.reproject import geographic_crs

Bounds = tuple[float, float, float, float]  # izquierda, abajo, derecha, arriba, en grados

# Muestras por lado de la celda más fina que se piden al leer (el resto de píxeles se salta).
SAMPLES_PER_CELL_SIDE = 8


@dataclass
class ClassCounts:
    codes: tuple[int, ...]  # valor de píxel de cada clase
    counts: np.ndarray  # (K, H, W) píxeles muestreados de cada clase
    total: np.ndarray  # (H, W) píxeles muestreados, con clase o sin ella

    @property
    def classified(self) -> np.ndarray:
        return self.counts.sum(axis=0)

    @property
    def valid(self) -> np.ndarray:
        """Fracción de los píxeles de cada celda con alguna de las clases (0 si no hay muestras)."""
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(self.total > 0, self.classified / self.total, 0.0)

    def mean(self, values: dict[int, float]) -> np.ndarray:
        """Promedio de `values` (por código) sobre los píxeles con clase; NaN donde no hay."""
        w = np.array([values[c] for c in self.codes], dtype=np.float64)[:, None, None]
        n = self.classified
        with np.errstate(invalid="ignore", divide="ignore"):
            out = (self.counts * w).sum(axis=0) / n
        return np.where(n > 0, out, np.nan).astype(np.float32)

    def fraction(self, codes: list[int]) -> np.ndarray:
        """Fracción de los píxeles con clase que son de `codes`; NaN donde no hay."""
        idx = [self.codes.index(c) for c in codes]
        n = self.classified
        with np.errstate(invalid="ignore", divide="ignore"):
            out = self.counts[idx].sum(axis=0) / n
        return np.where(n > 0, out, np.nan).astype(np.float32)

    def dominant(self) -> np.ndarray:
        """Código de la clase más frecuente en cada celda; 0 donde no hay ninguna."""
        codes = np.array(self.codes, dtype=np.uint8)
        return np.where(self.classified > 0, codes[self.counts.argmax(axis=0)], 0).astype(np.uint8)


@dataclass(frozen=True)
class ClassInfo:
    code: int
    name: str
    risk: float


def load_risk_table(path: Path) -> list[ClassInfo]:
    """Tabla clase a riesgo de Edgar (science/validation/noahh_ig_risk.csv).

    Las filas sin riesgo (sin dato y nodata) no son clases: no entran al costo.
    """
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [
        ClassInfo(int(r["ig_value"]), r["grupo"], float(r["riesgo"]))
        for r in rows
        if r["riesgo"].strip()
    ]


def count_classes(
    path: Path, targets: dict[str, tuple[tuple[int, int], Bounds]], codes: tuple[int, ...]
) -> dict[str, ClassCounts]:
    """Cuenta los píxeles de cada clase de `codes` en cada celda de cada grilla de `targets`.

    `targets` mapea un nombre a ((alto, ancho), bordes en grados). El archivo debe ser uint8 en
    una proyección cilíndrica (equirectangular o geográfica): así la longitud depende solo de la
    columna y la latitud solo de la fila.
    """
    import rasterio
    from affine import Affine
    from rasterio.enums import Resampling
    from rasterio.warp import transform, transform_bounds
    from rasterio.windows import Window, from_bounds

    slot = np.zeros(256, dtype=np.int64)  # valor de píxel -> 1..K; 0 = sin clase
    for i, code in enumerate(codes, start=1):
        slot[code] = i
    k1 = len(codes) + 1
    acc = {name: np.zeros(h * w * k1, dtype=np.int64) for name, ((h, w), _) in targets.items()}

    union = (
        min(b[0] for _, b in targets.values()),
        min(b[1] for _, b in targets.values()),
        max(b[2] for _, b in targets.values()),
        max(b[3] for _, b in targets.values()),
    )
    finest_deg = min(min((b[2] - b[0]) / w, (b[3] - b[1]) / h) for (h, w), b in targets.values())

    with rasterio.Env(GDAL_CACHEMAX=128), rasterio.open(path) as src:
        if np.dtype(src.dtypes[0]) != np.uint8:
            raise ValueError(f"{path.name} debe ser uint8 (códigos de clase), no {src.dtypes[0]}")
        if not (src.crs.is_geographic or src.crs.to_dict().get("proj") == "eqc"):
            raise ValueError(f"{path.name}: se espera una proyección equirectangular o geográfica")
        geo = geographic_crs(src.crs)
        if src.crs.is_geographic:
            px_deg = abs(src.res[0])
        else:
            params = src.crs.to_dict()
            px_deg = math.degrees(abs(src.res[0]) / (params.get("R") or params["a"]))
        step = max(1, int(finest_deg / px_deg / SAMPLES_PER_CELL_SIDE))

        win = from_bounds(*transform_bounds(geo, src.crs, *union), src.transform)
        win = win.round_offsets().round_lengths().intersection(Window(0, 0, src.width, src.height))
        col0, row0 = int(win.col_off), int(win.row_off)
        width, height = int(win.width), int(win.height)
        out_w = max(1, width // step)
        chunk = 128 * max(1, step)  # filas de origen por franja: múltiplo del bloque de 128

        for r in range(row0, row0 + height, chunk):
            h = min(chunk, row0 + height - r)
            out_h = max(1, h // step)
            sub = Window(col0, r, width, h)
            data = src.read(1, window=sub, out_shape=(out_h, out_w), resampling=Resampling.nearest)
            t = src.window_transform(sub) @ Affine.scale(width / out_w, h / out_h)
            xs = t.c + t.a * (np.arange(out_w) + 0.5)
            ys = t.f + t.e * (np.arange(out_h) + 0.5)
            lons = np.asarray(transform(src.crs, geo, xs, np.full(out_w, ys[0]))[0])
            lats = np.asarray(transform(src.crs, geo, np.full(out_h, xs[0]), ys)[1])
            cls = slot[data]
            for name, ((th, tw), (left, bottom, right, top)) in targets.items():
                cols = np.floor((lons - left) / (right - left) * tw).astype(np.int64)
                rows = np.floor((top - lats) / (top - bottom) * th).astype(np.int64)
                in_c = (cols >= 0) & (cols < tw)
                in_r = (rows >= 0) & (rows < th)
                if not in_c.any() or not in_r.any():
                    continue
                idx = (
                    (rows[in_r][:, None] * tw + cols[in_c][None, :]) * k1 + cls[np.ix_(in_r, in_c)]
                ).ravel()
                lo = int(idx.min())
                part = np.bincount(idx - lo)
                acc[name][lo : lo + part.size] += part

    result = {}
    for name, ((th, tw), _) in targets.items():
        c = acc[name].reshape(th, tw, k1)
        result[name] = ClassCounts(
            codes=tuple(codes),
            counts=np.moveaxis(c[..., 1:], -1, 0).astype(np.float32),
            total=c.sum(axis=-1).astype(np.float32),
        )
    return result
