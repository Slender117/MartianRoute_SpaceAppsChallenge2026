import { Vector3 } from "three";

import type { LatLon, RegionManifest } from "./types";

export const MARS_RADIUS_M = 3_389_500;
const METERS_PER_DEGREE = (Math.PI * MARS_RADIUS_M) / 180;

/** Point on the globe of radius `r` (east positive, north = +Y). */
export function latLonToSphere({ lat, lon }: LatLon, r = 1): Vector3 {
  const phi = (lat * Math.PI) / 180;
  const theta = (lon * Math.PI) / 180;
  return new Vector3(r * Math.cos(phi) * Math.cos(theta), r * Math.sin(phi), -r * Math.cos(phi) * Math.sin(theta));
}

export function bboxCenter(bbox: [number, number, number, number]): LatLon {
  const [lonMin, latMin, lonMax, latMax] = bbox;
  return { lat: (latMin + latMax) / 2, lon: (lonMin + lonMax) / 2 };
}

/** Size of a region's terrain in scene units (X axis). */
export const TERRAIN_SIZE = 10;

/**
 * Conversion between lat/lon/elevation and a region's scene coordinates.
 * The terrain is a TERRAIN_SIZE × TERRAIN_SIZE plane centered on the origin, north toward −Z.
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
