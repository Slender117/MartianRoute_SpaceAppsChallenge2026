"use client";

import { OrbitControls } from "@react-three/drei";
import { useFrame, useThree } from "@react-three/fiber";
import { useEffect, useMemo } from "react";
import { Vector3 } from "three";

import { bboxCenter, latLonToSphere, TERRAIN_SIZE } from "@/lib/geo";
import { useMapStore } from "@/lib/store";

const GLOBE_POSE = new Vector3(0, 0, 3.2);
const REGION_POSE = new Vector3(0, TERRAIN_SIZE * 0.6, TERRAIN_SIZE * 0.9);

/**
 * Transición continua globo → región: la cámara se acerca al sitio y, al llegar,
 * se cambia el globo por el terreno detallado.
 * TODO(3D): reemplazar el lerp por la secuencia de Theatre.js (lib/theatre.ts) para la demo.
 */
export function CameraRig() {
  const camera = useThree((s) => s.camera);
  const controls = useThree((s) => s.controls) as unknown as { target: Vector3; update: () => void } | null;
  const view = useMapStore((s) => s.view);
  const regions = useMapStore((s) => s.regions);
  const regionId = useMapStore((s) => s.regionId);
  const manifest = useMapStore((s) => s.manifest);
  const arriveAtRegion = useMapStore((s) => s.arriveAtRegion);

  const zoomTarget = useMemo(() => {
    const r = regions.find((x) => x.id === regionId);
    return r ? latLonToSphere(bboxCenter(r.bbox), 1.15) : null;
  }, [regions, regionId]);

  useEffect(() => {
    if (view === "region") camera.position.copy(REGION_POSE);
    if (view === "globe") camera.position.copy(GLOBE_POSE);
    camera.lookAt(0, 0, 0);
    // OrbitControls guarda su propia distancia: hay que sincronizarlo con la nueva pose.
    controls?.target.set(0, 0, 0);
    controls?.update();
  }, [view, camera, controls]);

  useFrame((_, dt) => {
    if (view !== "zooming" || !zoomTarget) return;
    camera.position.lerp(zoomTarget, 1 - Math.exp(-dt * 2.5));
    camera.lookAt(0, 0, 0);
    if (manifest && camera.position.distanceTo(zoomTarget) < 0.02) arriveAtRegion();
  });

  return (
    <OrbitControls
      makeDefault
      enabled={view !== "zooming"}
      enablePan={view === "region"}
      minDistance={view === "globe" ? 1.3 : 1}
      maxDistance={view === "globe" ? 8 : TERRAIN_SIZE * 2.5}
      maxPolarAngle={view === "region" ? Math.PI / 2.1 : Math.PI}
    />
  );
}
