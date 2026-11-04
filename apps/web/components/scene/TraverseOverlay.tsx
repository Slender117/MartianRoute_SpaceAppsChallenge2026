"use client";

import { Line } from "@react-three/drei";
import { useMemo } from "react";

import { regionFrame } from "@/lib/geo";
import { useMapStore } from "@/lib/store";

/**
 * Recorrido real del rover para validar las rutas propuestas.
 * El GeoJSON no trae elevación: se dibuja a la altura máxima de la región, como una "sombra" en el aire.
 * TODO(3D): muestrear el heightmap para pegarlo al terreno.
 */
export function TraverseOverlay({ exaggeration }: { exaggeration: number }) {
  const manifest = useMapStore((s) => s.manifest)!;
  const traverse = useMapStore((s) => s.traverse);
  const show = useMapStore((s) => s.showTraverse);
  const frame = useMemo(() => regionFrame(manifest, exaggeration), [manifest, exaggeration]);

  if (!show || !traverse) return null;

  const zMax = manifest.elevation_range[1];
  const points = traverse.geometry.coordinates.map(([lon, lat]) => frame.toScene(lat, lon, zMax, 0.1));

  return <Line points={points} color="#ffffff" lineWidth={2} dashed dashSize={0.15} gapSize={0.1} />;
}
