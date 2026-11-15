"use client";

import { OrbitControls } from "@react-three/drei";
import { useFrame, useThree } from "@react-three/fiber";
import { useEffect, useMemo } from "react";
import { Vector3 } from "three";

import { bboxCenter, latLonToSphere, TERRAIN_SIZE } from "@/lib/geo";
import { useMapStore } from "@/lib/store";

const GLOBE_POSE = new Vector3(0, 0, 3.2);
const ORIGIN = new Vector3(0, 0, 0);
const REGION_POSE = new Vector3(0, TERRAIN_SIZE * 0.6, TERRAIN_SIZE * 0.9);
// Pantalla vertical de celular: más alta y más lejos, mirando un poco al sur del centro.
const PORTRAIT_POSE = new Vector3(0, TERRAIN_SIZE * 1.3, TERRAIN_SIZE * 1.2);
const PORTRAIT_TARGET = new Vector3(0, 0, TERRAIN_SIZE * 0.25);

/**
 * Pose al llegar a la región según la proporción de la pantalla. En vertical el campo de visión
 * horizontal es angosto: la cámara sube y se aleja para que el terreno quepa a lo ancho, y apunta
 * al sur del centro para que el sitio quede arriba de la hoja de paneles.
 */
function regionPose(aspect: number) {
  const t = Math.min(Math.max((1 - aspect) / 0.55, 0), 1); // 0 = cuadrada o ancha, 1 = celular vertical
  return {
    position: REGION_POSE.clone().lerp(PORTRAIT_POSE, t),
    target: ORIGIN.clone().lerp(PORTRAIT_TARGET, t),
  };
}

/**
 * Transición continua globo → región: la cámara se acerca al sitio y, al llegar,
 * se cambia el globo por el terreno detallado.
 * TODO(3D): reemplazar el lerp por la secuencia de Theatre.js (lib/theatre.ts) para la demo.
 */
export function CameraRig() {
  const camera = useThree((s) => s.camera);
  const get = useThree((s) => s.get);
  const invalidate = useThree((s) => s.invalidate);
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
    // La proporción se lee solo al cambiar de vista: al girar el celular no se mueve la cámara
    // que el usuario ya acomodó.
    const { width, height } = get().size;
    const pose = view === "region" ? regionPose(width / Math.max(height, 1)) : { position: GLOBE_POSE, target: ORIGIN };
    if (view !== "zooming") {
      camera.position.copy(pose.position);
      camera.lookAt(pose.target);
    } else {
      camera.lookAt(ORIGIN);
    }
    // OrbitControls guarda su propia distancia: hay que sincronizarlo con la nueva pose.
    controls?.target.copy(view === "zooming" ? ORIGIN : pose.target);
    controls?.update();
    // En la región la escena se dibuja a pedido: la nueva pose necesita su cuadro.
    invalidate();
  }, [view, camera, controls, invalidate, get]);

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
