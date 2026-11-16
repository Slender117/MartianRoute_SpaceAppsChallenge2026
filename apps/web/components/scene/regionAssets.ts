"use client";

import { useEffect, useState } from "react";

import { assetUrl } from "@/lib/api";
import type { RegionManifest } from "@/lib/types";

/**
 * 3D view data that the pipeline writes into manifest.json and the API does not serve yet
 * (contract proposal in docs/arquitectura.md). Until Miguel adds them to the schema,
 * they are read from the manifest.json published next to the region files.
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
  kind?: "traverse"; // start or end of a traverse: only with the traverse visible
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

/** A single download per region, shared by the scene and the panels. */
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

/** Heights in meters from the little-endian Float32 heightmap, row 0 to the north. */
export function loadHeights(regionId: string, path: string, shape: [number, number]): Promise<Float32Array> {
  const key = `${regionId}/${path}`;
  let promise = heightsCache.get(key);
  if (!promise) {
    promise = fetch(assetUrl(regionId, path))
      .then((r) => {
        if (!r.ok) throw new Error(`Could not read ${path}: HTTP ${r.status}`);
        return r.arrayBuffer();
      })
      .then((buffer) => {
        const n = shape[0] * shape[1];
        if (buffer.byteLength !== n * 4) {
          throw new Error(`${path} is ${buffer.byteLength} bytes; ${n * 4} were expected`);
        }
        // DataView fixes the file's byte order, without depending on the machine's.
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

/** Region heights, or null while they load or if the region has no heightmap.bin. */
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

/** Bilinear height at (lat, lon), with the same grid convention as the API. */
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
