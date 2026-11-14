"use client";

import { Line } from "@react-three/drei";
import { useMemo } from "react";

import { regionFrame } from "@/lib/geo";
import { useMapStore } from "@/lib/store";

import { heightAt, useRegionExtras, useRegionHeights } from "./regionAssets";

const LIFT = 0.015; // apenas sobre el suelo, para que la línea no se hunda entre celdas

/**
 * Recorrido real del rover, pegado al terreno, para comparar con las rutas propuestas.
 * La altura sale del mismo heightmap que la malla; si la región no lo tiene, de la tercera
 * coordenada del GeoJSON, y si tampoco, se dibuja a la altura máxima como una "sombra" en el aire.
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
