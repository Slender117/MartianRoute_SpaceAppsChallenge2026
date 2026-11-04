import { Vector3 } from "three";

import type { LatLon, RegionManifest } from "./types";

export const MARS_RADIUS_M = 3_389_500;
const METERS_PER_DEGREE = (Math.PI * MARS_RADIUS_M) / 180;

/** Punto sobre el globo de radio `r` (este positivo, norte = +Y). */
export function latLonToSphere({ lat, lon }: LatLon, r = 1): Vector3 {
  const phi = (lat * Math.PI) / 180;
  const theta = (lon * Math.PI) / 180;
  return new Vector3(r * Math.cos(phi) * Math.cos(theta), r * Math.sin(phi), -r * Math.cos(phi) * Math.sin(theta));
}

export function bboxCenter(bbox: [number, number, number, number]): LatLon {
  const [lonMin, latMin, lonMax, latMax] = bbox;
  return { lat: (latMin + latMax) / 2, lon: (lonMin + lonMax) / 2 };
}

/** Tamaño del terreno de una región en unidades de escena (eje X). */
export const TERRAIN_SIZE = 10;

/**
 * Conversión entre lat/lon/elevación y coordenadas de la escena de una región.
 * El terreno es un plano TERRAIN_SIZE × TERRAIN_SIZE centrado en el origen, norte hacia −Z.
 */
export function regionFrame(m: RegionManifest, exaggeration = 2) {
  const [lonMin, latMin, lonMax, latMax] = m.bbox;
  const [zMin, zMax] = m.elevation_range;
  const widthM = (latMax - latMin) * METERS_PER_DEGREE;
  const heightScale = ((zMax - zMin) / widthM) * TERRAIN_SIZE * exaggeration;
  const half = TERRAIN_SIZE / 2;

  return {
    heightScale,
    toScene(lat: number, lon: number, elev = zMin, lift = 0): Vector3 {
      const x = ((lon - lonMin) / (lonMax - lonMin)) * TERRAIN_SIZE - half;
      const z = ((latMax - lat) / (latMax - latMin)) * TERRAIN_SIZE - half;
      const y = ((elev - zMin) / Math.max(zMax - zMin, 1e-6)) * heightScale + lift;
      return new Vector3(x, y, z);
    },
    fromScene(p: Vector3): LatLon {
      return {
        lat: latMax - ((p.z + half) / TERRAIN_SIZE) * (latMax - latMin),
        lon: lonMin + ((p.x + half) / TERRAIN_SIZE) * (lonMax - lonMin),
      };
    },
  };
}
