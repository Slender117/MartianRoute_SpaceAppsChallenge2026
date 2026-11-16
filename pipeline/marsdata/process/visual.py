"""Visual-only products for the 3D view: orthophoto as a texture and a colored class layer.

None of this enters routing: the API uses the .npy grids. Textures stretch from edge to edge
of the mesh, so they cover the bbox (not the API grid, which sticks out half a cell).
"""

from pathlib import Path

import numpy as np
from rasterio.warp import Resampling

from marsdata.process.classes import ClassCounts, ClassInfo
from marsdata.process.reproject import fill_nearest, warp_to_region
from marsdata.region import Region

# Orthophoto pixels per grid cell (600 cells -> 2400 px).
ORTHO_PX_PER_CELL = 4
# Opacity of the class layer: it lets the relief and the orthophoto show through.
CLASS_ALPHA = 0.6
# Okabe and Ito palette (distinguishable with color blindness), per NOAH-H group code.
NOAHH_COLORS = {
    1: "#F0E442",  # not bedrock: yellow
    2: "#009E73",  # bedrock: bluish green
    3: "#E69F00",  # boulder fields: orange
    4: "#56B4E9",  # small ripples: sky blue
    5: "#CC79A7",  # large ripples: reddish purple
}
FALLBACK_COLORS = ["#0072B2", "#D55E00", "#999999", "#F5C710", "#61D04F"]


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def ortho_texture(path: Path, region: Region) -> np.ndarray:
    """Grayscale orthophoto (uint8) over the bbox, with contrast stretched to 1-99 %.

    Gaps in the mosaic take the nearest pixel with data: a black strip on the ground would
    read as a shadow or a ravine.
    """
    n = region.size * ORTHO_PX_PER_CELL
    img = warp_to_region(path, region, Resampling.average, shape=(n, n), bounds=region.bbox)
    valid = np.isfinite(img)
    if not valid.any():
        raise ValueError(f"{path.name} does not cover the region")
    lo, hi = np.percentile(img[valid], [1, 99])
    out = np.clip((fill_nearest(img) - lo) / max(hi - lo, 1e-6) * 255, 0, 255)
    return out.astype(np.uint8)


def class_colors(info: list[ClassInfo]) -> dict[int, str]:
    return {
        c.code: NOAHH_COLORS.get(c.code, FALLBACK_COLORS[i % len(FALLBACK_COLORS)])
        for i, c in enumerate(info)
    }


def class_texture(counts: ClassCounts, colors: dict[int, str]) -> np.ndarray:
    """RGBA: each texel mixes the colors by the fraction of each class; transparent with no data.

    The mix smooths the edges between classes, and the opacity drops where part of the texel has
    no class (mosaic edge).
    """
    n = counts.classified
    frac = np.where(n > 0, counts.counts / np.maximum(n, 1), 0.0)  # (K, H, W)
    palette = np.array([_rgb(colors[c]) for c in counts.codes], dtype=np.float64)  # (K, 3)
    rgb = np.einsum("khw,kc->hwc", frac, palette)
    alpha = counts.valid * CLASS_ALPHA * 255
    return np.dstack([rgb, alpha]).round().clip(0, 255).astype(np.uint8)


def legend(info: list[ClassInfo], colors: dict[int, str], counts: ClassCounts) -> list[dict]:
    """Legend of the class layer, with the fraction of the area with data that each one covers."""
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
