"use client";

import { useEffect, useMemo } from "react";
import {
  DataTexture,
  LinearFilter,
  NearestFilter,
  RGBAFormat,
  SRGBColorSpace,
  type BufferGeometry,
  type Texture,
} from "three";

import { ZONE_COLORS, zoneGrid, type Zone } from "@/lib/safeReturn";
import { useMapStore } from "@/lib/store";
import type { SafeReturnResponse } from "@/lib/types";

const ZONES: Zone[] = [0, 1, 2, 3];

/**
 * Safe-return map zones as an RGBA texture, with the same colors as the legend.
 * The API sends the north row first and the texture starts at the bottom (south): rows are flipped.
 */
export function zoneTexture(res: SafeReturnResponse): DataTexture {
  const zones = zoneGrid(res);
  const [h, w] = res.shape;
  const palette = ZONES.map((z) => {
    const hex = parseInt(ZONE_COLORS[z].slice(1), 16);
    return [(hex >> 16) & 255, (hex >> 8) & 255, hex & 255];
  });
  const data = new Uint8Array(w * h * 4);
  for (let r = 0; r < h; r++) {
    const src = r * w;
    const dst = (h - 1 - r) * w;
    for (let c = 0; c < w; c++) {
      const [red, green, blue] = palette[zones[src + c]];
      const i = (dst + c) * 4;
      data[i] = red;
      data[i + 1] = green;
      data[i + 2] = blue;
      data[i + 3] = 255;
    }
  }
  const texture = new DataTexture(data, w, h, RGBAFormat);
  texture.colorSpace = SRGBColorSpace;
  // Zones, not a gradient: up close each cell keeps its color.
  texture.magFilter = NearestFilter;
  texture.minFilter = LinearFilter;
  texture.generateMipmaps = false;
  texture.needsUpdate = true;
  return texture;
}

export interface Displacement {
  displacementMap: Texture;
  displacementScale: number;
}

/**
 * Safe-return map painted over the relief, above the layers. Without heightmap.bin, the veil
 * uses the same displacementMap as the ground (Lambert, because Basic does not support it).
 */
export function SafeReturnVeil({
  geometry,
  order,
  opacity,
  displacement,
}: {
  geometry: BufferGeometry;
  order: number;
  opacity: number;
  displacement?: Displacement;
}) {
  const res = useMapStore((s) => (s.showSafeReturn ? s.safeReturn : null));
  const texture = useMemo(() => (res ? zoneTexture(res) : null), [res]);
  useEffect(() => () => texture?.dispose(), [texture]);
  if (!texture) return null;

  const common = {
    map: texture,
    transparent: true,
    opacity,
    depthWrite: false,
    polygonOffset: true,
    polygonOffsetFactor: -order,
  };
  return (
    <mesh geometry={geometry} renderOrder={order}>
      {displacement ? <meshLambertMaterial {...common} {...displacement} /> : <meshBasicMaterial {...common} />}
    </mesh>
  );
}
