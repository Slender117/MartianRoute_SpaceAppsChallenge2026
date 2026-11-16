"use client";

import { Line } from "@react-three/drei";
import { useMemo } from "react";

import { regionFrame } from "@/lib/geo";
import { useMapStore } from "@/lib/store";

import { heightAt, useRegionExtras, useRegionHeights } from "./regionAssets";

const LIFT = 0.015; // just above the ground, so the line does not sink between cells

/**
 * The rover's real traverse, laid on the terrain, to compare with the proposed routes.
 * Its height comes from the same heightmap as the mesh; if the region has none, from the third
 * GeoJSON coordinate, and if that is missing too, it is drawn at maximum height as a "shadow" in the air.
 */
export function TraverseOverlay({ exaggeration }: { exaggeration: number }) {
  const manifest = useMapStore((s) => s.manifest)!;
  const traverse = useMapStore((s) => s.traverse);
  const show = useMapStore((s) => s.showTraverse);
  const extras = useRegionExtras(manifest.id);
  const heights = useRegionHeights(manifest, extras);
  const frame = useMemo(() => regionFrame(manifest, exaggeration), [manifest, exaggeration]);

  const points = useMemo(() => {
    if (!traverse) return [];
    const zMax = manifest.elevation_range[1];
    return traverse.geometry.coordinates.map((c) => {
      const [lon, lat, z] = c as number[];
      const elev = heights ? heightAt(heights, manifest, lat, lon) : (z ?? zMax);
      return frame.toScene(lat, lon, elev, LIFT);
    });
  }, [traverse, heights, manifest, frame]);

  if (!show || points.length < 2) return null;
  return <Line points={points} color="#ffffff" lineWidth={2} transparent opacity={0.9} />;
}
