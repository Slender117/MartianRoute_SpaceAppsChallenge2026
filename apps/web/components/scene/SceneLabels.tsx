"use client";

import { useFrame } from "@react-three/fiber";
import { useLayoutEffect, useMemo, useRef } from "react";
import { Vector3 } from "three";

import { regionFrame } from "@/lib/geo";
import { dataName, useLang } from "@/lib/i18n";
import { useMapStore } from "@/lib/store";

import { heightAt, useRegionExtras, useRegionHeights } from "./regionAssets";

/**
 * Names anchored to the terrain. They are HTML outside the <Canvas> (drei's <Html> fails with
 * React 19): LabelAnchors projects each point to the screen when a frame is drawn and notifies
 * LabelOverlay, which moves the labels to those positions without going through React. If the camera
 * does not move no frames are drawn, and the labels do no work either.
 */
export interface PlacedLabel {
  name: string;
  position: Vector3;
}

interface ScreenPoint {
  x: number;
  y: number;
  visible: boolean;
}

// Screen positions: LabelAnchors writes them and LabelOverlay reads them in the same frame.
const screen: ScreenPoint[] = [];
// LabelOverlay subscribes here to place the labels after each projection.
const listeners = new Set<() => void>();

const LIFT = 0.25; // the label floats above the point, joined by a line

export function usePlacedLabels(exaggeration: number): PlacedLabel[] {
  const manifest = useMapStore((s) => s.manifest);
  const showTraverse = useMapStore((s) => s.showTraverse);
  const extras = useRegionExtras(manifest?.id);
  const heights = useRegionHeights(manifest, extras);
  const lang = useLang((s) => s.lang);
  return useMemo(() => {
    if (!manifest || !extras?.labels) return [];
    const frame = regionFrame(manifest, exaggeration);
    return extras.labels
      .filter((l) => l.kind !== "traverse" || showTraverse)
      .map((l) => {
        const elev = heights ? heightAt(heights, manifest, l.lat, l.lon) : (l.elev ?? manifest.elevation_range[0]);
        return { name: dataName(l.name, lang), position: frame.toScene(l.lat, l.lon, elev) };
      });
  }, [manifest, extras, heights, exaggeration, showTraverse, lang]);
}

/** Inside the Canvas: marks each point and computes where it falls on the screen. */
export function LabelAnchors({ labels }: { labels: PlacedLabel[] }) {
  const v = useMemo(() => new Vector3(), []);
  useFrame(({ camera, size }) => {
    screen.length = labels.length;
    labels.forEach((l, i) => {
      v.copy(l.position).setY(l.position.y + LIFT).project(camera);
      screen[i] = {
        x: ((v.x + 1) / 2) * size.width,
        y: ((1 - v.y) / 2) * size.height,
        visible: v.z < 1 && Math.abs(v.x) < 1.05 && Math.abs(v.y) < 1.05,
      };
    });
    for (const notify of listeners) notify();
  });

  return (
    <group>
      {labels.map((l) => (
        <group key={l.name} position={l.position}>
          <mesh>
            <sphereGeometry args={[0.035, 12, 12]} />
            <meshBasicMaterial color="#ffffff" toneMapped={false} />
          </mesh>
          <mesh position={[0, LIFT / 2, 0]}>
            <cylinderGeometry args={[0.004, 0.004, LIFT, 6]} />
            <meshBasicMaterial color="#ffffff" transparent opacity={0.7} toneMapped={false} />
          </mesh>
        </group>
      ))}
    </group>
  );
}

/** Outside the Canvas: the HTML labels, moved every time a frame is drawn. */
export function LabelOverlay({ labels }: { labels: PlacedLabel[] }) {
  const refs = useRef<(HTMLDivElement | null)[]>([]);

  useLayoutEffect(() => {
    // Each label's size is measured once per set of names (it changes with the language), not on
    // every frame: reading offsetWidth after moving elements forces the browser to recompute.
    let sizes = refs.current.map((el) => ({ w: el?.offsetWidth ?? 0, h: el?.offsetHeight ?? 0 }));

    const place = () => {
      const placed: { x0: number; y0: number; x1: number; y1: number }[] = [];
      refs.current.forEach((el, i) => {
        if (!el) return;
        const p = screen[i];
        if (!p || !p.visible) {
          el.style.opacity = "0";
          return;
        }
        const { w, h } = sizes[i];
        // If it overlaps a label already placed, it goes up above it.
        const x0 = p.x - w / 2;
        let y0 = p.y - h;
        for (let hit = true; hit; ) {
          hit = false;
          for (const r of placed) {
            if (x0 < r.x1 && x0 + w > r.x0 && y0 < r.y1 && y0 + h > r.y0) {
              y0 = r.y0 - h - 2;
              hit = true;
            }
          }
        }
        placed.push({ x0, y0, x1: x0 + w, y1: y0 + h });
        el.style.opacity = "1";
        el.style.transform = `translate(${x0}px, ${y0}px)`;
      });
    };

    place();
    listeners.add(place);
    // If the font finishes loading later, the widths change: they are measured again.
    let alive = true;
    void document.fonts?.ready.then(() => {
      if (!alive) return;
      sizes = refs.current.map((el) => ({ w: el?.offsetWidth ?? 0, h: el?.offsetHeight ?? 0 }));
      place();
    });
    return () => {
      alive = false;
      listeners.delete(place);
    };
  }, [labels]);

  return (
    <div className="scene-labels" aria-hidden>
      {labels.map((l, i) => (
        <div
          key={l.name}
          className="scene-label"
          ref={(el) => {
            refs.current[i] = el;
          }}
        >
          {l.name}
        </div>
      ))}
    </div>
  );
}
