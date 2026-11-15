"use client";

import { useFrame } from "@react-three/fiber";
import { useLayoutEffect, useMemo, useRef } from "react";
import { Vector3 } from "three";

import { regionFrame } from "@/lib/geo";
import { dataName, useLang } from "@/lib/i18n";
import { useMapStore } from "@/lib/store";

import { heightAt, useRegionExtras, useRegionHeights } from "./regionAssets";

/**
 * Nombres anclados al terreno. Van en HTML fuera del <Canvas> (el <Html> de drei falla con
 * React 19): LabelAnchors proyecta cada punto a la pantalla cuando se dibuja un cuadro y avisa a
 * LabelOverlay, que mueve las etiquetas con esas posiciones sin pasar por React. Si la cámara no
 * se mueve no se dibujan cuadros, y las etiquetas tampoco hacen trabajo.
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

// Posiciones en pantalla: las escribe LabelAnchors y las lee LabelOverlay en el mismo cuadro.
const screen: ScreenPoint[] = [];
// LabelOverlay se suscribe aquí para acomodar las etiquetas después de cada proyección.
const listeners = new Set<() => void>();

const LIFT = 0.25; // la etiqueta flota sobre el punto, unida por una línea

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

/** Dentro del Canvas: marca cada punto y calcula dónde cae en la pantalla. */
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

/** Fuera del Canvas: las etiquetas en HTML, movidas cada vez que se dibuja un cuadro. */
export function LabelOverlay({ labels }: { labels: PlacedLabel[] }) {
  const refs = useRef<(HTMLDivElement | null)[]>([]);

  useLayoutEffect(() => {
    // El tamaño de cada etiqueta se mide una vez por juego de nombres (cambia con el idioma), no en
    // cada cuadro: leer offsetWidth después de mover elementos obliga al navegador a recalcular.
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
        // Si choca con una etiqueta ya puesta, sube por encima de ella.
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
    // Si la fuente termina de cargar después, los anchos cambian: se miden de nuevo.
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
