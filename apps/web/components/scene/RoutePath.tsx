"use client";

import { Line } from "@react-three/drei";
import { useMemo } from "react";

import { regionFrame } from "@/lib/geo";
import { useMapStore } from "@/lib/store";
import type { LatLon, WalkMode } from "@/lib/types";

import { heightAt, useRegionExtras, useRegionHeights } from "./regionAssets";

export const MODE_COLORS: Record<WalkMode, string> = {
  safe: "#4fd1a5",
  fast: "#ffc94d",
  science: "#6aa8ff",
  baseline: "#9aa0a6", // gris: referencia, no un modo
};

const LIFT = 0.04; // separa la línea del terreno para que no parpadee
const START_COLOR = "#ffffff";
const END_COLOR = "#ff7a45";

/**
 * Ruta del modo activo (resaltada), las otras en tenue, marcadores de inicio y destino, y paradas.
 * El detalle de cada parada se lee en NavPanel. Los puntos en la escena se calculan una vez por
 * juego de rutas: cambiar de modo solo cambia el grosor y la opacidad.
 */
export function RoutePath({ exaggeration }: { exaggeration: number }) {
  const manifest = useMapStore((s) => s.manifest)!;
  const routes = useMapStore((s) => s.routes);
  const mode = useMapStore((s) => s.mode);
  const start = useMapStore((s) => s.start);
  const end = useMapStore((s) => s.end);
  const frame = useMemo(() => regionFrame(manifest, exaggeration), [manifest, exaggeration]);
  const heights = useRegionHeights(manifest, useRegionExtras(manifest.id));

  const lines = useMemo(
    () =>
      Object.values(routes).map((r) => ({
        mode: r.mode,
        points: r.path.map((p) => frame.toScene(p.lat, p.lon, p.elev, LIFT)),
      })),
    [routes, frame],
  );

  // Cada parada, a la altura del punto de la ruta más cercano.
  const active = routes[mode];
  const stops = useMemo(
    () =>
      active?.stops.map((s) => {
        let best = active.path[0];
        let bestD = Infinity;
        for (const q of active.path) {
          const d = (q.lat - s.lat) ** 2 + (q.lon - s.lon) ** 2;
          if (d < bestD) [best, bestD] = [q, d];
        }
        return { position: frame.toScene(s.lat, s.lon, best.elev, LIFT * 3), ice: s.type === "ice" };
      }) ?? [],
    [active, frame],
  );

  // Los extremos se apoyan en el terreno; sin heightmap.bin, a la altura base.
  const markerAt = (p: LatLon) =>
    frame.toScene(
      p.lat,
      p.lon,
      heights ? heightAt(heights, manifest, p.lat, p.lon) : manifest.elevation_range[0],
      LIFT,
    );

  return (
    <group>
      {lines.map(({ mode: m, points }) => (
        <Line
          key={m}
          points={points}
          color={MODE_COLORS[m]}
          lineWidth={m === mode ? 4 : 1.5}
          transparent
          opacity={m === mode ? 1 : 0.35}
        />
      ))}

      {start && (
        <mesh position={markerAt(start)}>
          <sphereGeometry args={[0.06, 16, 16]} />
          <meshBasicMaterial color={START_COLOR} toneMapped={false} />
        </mesh>
      )}
      {end && (
        <mesh position={markerAt(end)}>
          <sphereGeometry args={[0.06, 16, 16]} />
          <meshBasicMaterial color={END_COLOR} toneMapped={false} />
        </mesh>
      )}

      {stops.map((s, i) => (
        <mesh key={i} position={s.position}>
          <octahedronGeometry args={[0.08]} />
          <meshBasicMaterial color={s.ice ? "#b4f0ff" : "#3ddc84"} toneMapped={false} />
        </mesh>
      ))}
    </group>
  );
}
