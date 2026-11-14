"use client";

import { useEffect, useState } from "react";

import { assetUrl } from "@/lib/api";
import type { RegionManifest } from "@/lib/types";

/**
 * Datos de la vista 3D que el pipeline escribe en manifest.json y la API todavía no sirve
 * (propuesta de contrato en docs/arquitectura.md). Mientras Miguel no los agregue al esquema,
 * se leen del manifest.json publicado junto a los archivos de la región.
 */
export interface LegendItem {
  code: number;
  name: string;
  color: string;
  risk: number;
  share: number;
}

export interface SceneLabel {
  name: string;
  lat: number;
  lon: number;
  elev?: number;
  source?: string;
  kind?: "traverse"; // inicio o final de un recorrido: solo con el recorrido visible
}

export interface RegionExtras {
  assets?: {
    heightmap?: { path: string; dtype: "float32"; byte_order: "little"; shape: [number, number] };
    ortho?: { path: string; size: [number, number]; provenance: string; source: string };
  };
  legends?: Record<string, LegendItem[]>;
  labels?: SceneLabel[];
  cell_size_m?: [number, number];
}

const extrasCache = new Map<string, Promise<RegionExtras>>();
const heightsCache = new Map<string, Promise<Float32Array>>();

/** Una sola descarga por región, compartida entre la escena y los paneles. */
export function loadRegionExtras(regionId: string): Promise<RegionExtras> {
  let promise = extrasCache.get(regionId);
  if (!promise) {
    promise = fetch(assetUrl(regionId, "manifest.json"))
      .then((r) => (r.ok ? (r.json() as Promise<RegionExtras>) : {}))
      .catch(() => ({}));
    extrasCache.set(regionId, promise);
  }
  return promise;
}

/** Alturas en metros del heightmap Float32 little-endian, fila 0 al norte. */
export function loadHeights(regionId: string, path: string, shape: [number, number]): Promise<Float32Array> {
  const key = `${regionId}/${path}`;
  let promise = heightsCache.get(key);
  if (!promise) {
    promise = fetch(assetUrl(regionId, path))
      .then((r) => {
        if (!r.ok) throw new Error(`No se pudo leer ${path}: HTTP ${r.status}`);
        return r.arrayBuffer();
      })
      .then((buffer) => {
        const n = shape[0] * shape[1];
        if (buffer.byteLength !== n * 4) {
          throw new Error(`${path} mide ${buffer.byteLength} bytes; se esperaban ${n * 4}`);
        }
        // DataView fija el orden de bytes del archivo, sin depender del de la máquina.
        const view = new DataView(buffer);
        const heights = new Float32Array(n);
        for (let i = 0; i < n; i++) heights[i] = view.getFloat32(i * 4, true);
        return heights;
      });
    promise.catch(() => heightsCache.delete(key));
    heightsCache.set(key, promise);
  }
  return promise;
}

export function useRegionExtras(regionId: string | undefined): RegionExtras | null {
  const [state, setState] = useState<{ id: string; extras: RegionExtras } | null>(null);
  useEffect(() => {
    if (!regionId) return;
    let alive = true;
    loadRegionExtras(regionId).then((extras) => {
      if (alive) setState({ id: regionId, extras });
    });
    return () => {
      alive = false;
    };
  }, [regionId]);
  return state && state.id === regionId ? state.extras : null;
}

/** Alturas de la región, o null mientras cargan o si la región no tiene heightmap.bin. */
export function useRegionHeights(
  manifest: RegionManifest | null,
  extras: RegionExtras | null,
): Float32Array | null {
  const path = extras?.assets?.heightmap?.path;
  const id = manifest?.id;
  const [h, w] = manifest?.shape ?? [0, 0];
  const key = id && path ? `${id}/${path}/${h}x${w}` : null;
  const [state, setState] = useState<{ key: string; heights: Float32Array } | null>(null);
  useEffect(() => {
    if (!key || !id || !path) return;
    let alive = true;
    loadHeights(id, path, [h, w])
      .then((heights) => {
        if (alive) setState({ key, heights });
      })
      .catch((e: Error) => console.error(e.message));
    return () => {
      alive = false;
    };
  }, [key, id, path, h, w]);
  return state && state.key === key ? state.heights : null;
}

/** Altura bilineal en (lat, lon), con la misma convención de grilla que la API. */
export function heightAt(heights: Float32Array, manifest: RegionManifest, lat: number, lon: number): number {
  const [h, w] = manifest.shape;
  const [lonMin, latMin, lonMax, latMax] = manifest.bbox;
  const r = Math.min(Math.max(((latMax - lat) / (latMax - latMin)) * (h - 1), 0), h - 1);
  const c = Math.min(Math.max(((lon - lonMin) / (lonMax - lonMin)) * (w - 1), 0), w - 1);
  const r0 = Math.min(Math.floor(r), h - 2);
  const c0 = Math.min(Math.floor(c), w - 2);
  const fr = r - r0;
  const fc = c - c0;
  const at = (row: number, col: number) => heights[row * w + col];
  const top = at(r0, c0) * (1 - fc) + at(r0, c0 + 1) * fc;
  const bottom = at(r0 + 1, c0) * (1 - fc) + at(r0 + 1, c0 + 1) * fc;
  return top * (1 - fr) + bottom * fr;
}
