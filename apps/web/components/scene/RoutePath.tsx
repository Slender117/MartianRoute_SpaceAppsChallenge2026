"use client";

import { Line } from "@react-three/drei";
import { useMemo } from "react";

import { regionFrame } from "@/lib/geo";
import { useMapStore } from "@/lib/store";
import type { WalkMode } from "@/lib/types";

export const MODE_COLORS: Record<WalkMode, string> = {
  safe: "#4fd1a5",
  fast: "#ffc94d",
  science: "#6aa8ff",
  baseline: "#9aa0a6", // gris: referencia, no un modo
};

const LIFT = 0.04; // separa la línea del terreno para que no parpadee

/**
 * Ruta del modo activo (resaltada), las otras en tenue, y marcadores de inicio/destino/paradas.
 * El detalle de cada parada se lee en NavPanel.
 */
export function RoutePath({ exaggeration }: { exaggeration: number }) {
  const manifest = useMapStore((s) => s.manifest)!;
  const { routes, mode, start, end } = useMapStore();
  const frame = useMemo(() => regionFrame(manifest, exaggeration), [manifest, exaggeration]);
  const [zMin] = manifest.elevation_range;

  // Los extremos se dibujan a la altura base hasta que la API devuelve elevaciones.
  const marker = (p: { lat: number; lon: number }, color: string, key: string) => (
    <mesh key={key} position={frame.toScene(p.lat, p.lon, zMin, LIFT)}>
      <sphereGeometry args={[0.06, 16, 16]} />
      <meshBasicMaterial color={color} toneMapped={false} />
    </mesh>
  );

  const active = routes[mode];

  return (
    <group>
      {Object.values(routes).map((r) => (
        <Line
          key={r.mode}
          points={r.path.map((p) => frame.toScene(p.lat, p.lon, p.elev, LIFT))}
          color={MODE_COLORS[r.mode]}
          lineWidth={r.mode === mode ? 4 : 1.5}
          transparent
          opacity={r.mode === mode ? 1 : 0.35}
        />
      ))}

      {!active && start && marker(start, "#ffffff", "start")}
      {!active && end && marker(end, "#ff7a45", "end")}

      {active?.stops.map((s, i) => {
        const p = active.path.reduce((best, q) =>
          Math.hypot(q.lat - s.lat, q.lon - s.lon) < Math.hypot(best.lat - s.lat, best.lon - s.lon) ? q : best,
        );
        return (
          <mesh key={i} position={frame.toScene(s.lat, s.lon, p.elev, LIFT * 3)}>
            <octahedronGeometry args={[0.08]} />
            <meshBasicMaterial color={s.type === "ice" ? "#b4f0ff" : "#3ddc84"} toneMapped={false} />
          </mesh>
        );
      })}
    </group>
  );
}
