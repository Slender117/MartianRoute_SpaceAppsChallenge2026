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
  baseline: "#9aa0a6", // gray: a reference, not a mode
};

const LIFT = 0.04; // lifts the line off the terrain so it does not flicker
const START_COLOR = "#ffffff";
const END_COLOR = "#ff7a45";

/**
 * Route of the active mode (highlighted), the others faded, start and destination markers, and stops.
 * Each stop's detail is in NavPanel. The scene points are computed once per set of
 * routes: changing the mode only changes thickness and opacity.
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

  // Each stop, at the height of the nearest route point.
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

  // The endpoints rest on the terrain; without heightmap.bin, at the base height.
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
