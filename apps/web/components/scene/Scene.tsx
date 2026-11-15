"use client";

import { Stars } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Bloom, EffectComposer, Vignette } from "@react-three/postprocessing";
import dynamic from "next/dynamic";

import { useSceneSettings } from "@/components/debug/sceneSettings";
import { useMapStore } from "@/lib/store";

import { CameraRig } from "./CameraRig";
import { Globe } from "./Globe";
import { RegionTerrain } from "./RegionTerrain";
import { RoutePath } from "./RoutePath";
import { LabelAnchors, LabelOverlay, usePlacedLabels } from "./SceneLabels";
import { TraverseOverlay } from "./TraverseOverlay";

// Panel de ajustes (Leva) solo en desarrollo: en producción la condición es constante y el
// paquete ni siquiera entra en la descarga.
const DebugControls =
  process.env.NODE_ENV === "production"
    ? null
    : dynamic(() => import("@/components/debug/DebugControls"), { ssr: false });

/** Una sola escena para todo el recorrido: el zoom es una transición de cámara. */
export default function Scene() {
  const view = useMapStore((s) => s.view);
  const { sunIntensity, exaggeration, layerOpacity, bloom } = useSceneSettings();
  const labels = usePlacedLabels(exaggeration);
  const showLabels = view === "region" && labels.length > 0;

  return (
    <>
      {DebugControls && <DebugControls />}
      <Canvas
        camera={{ position: [0, 0, 3.2], fov: 45, near: 0.01, far: 200 }}
        dpr={[1, 2]}
        // En la región nada se mueve solo: se dibuja un cuadro solo cuando algo cambia (cámara,
        // capas, rutas). El globo gira y el zoom es una animación, así que ahí se dibuja siempre.
        frameloop={view === "region" ? "demand" : "always"}
      >
        <color attach="background" args={["#0b0605"]} />
        <ambientLight intensity={0.25} />
        {/* Luz de cielo: rellena las laderas en sombra sin aplanar el relieve. */}
        <hemisphereLight args={["#f6d8c4", "#2a1510", 0.35]} />
        <directionalLight position={[5, 6, 3]} intensity={sunIntensity} />
        <Stars radius={80} depth={40} count={3000} factor={3} fade />

        {view !== "region" && <Globe />}
        {view === "region" && (
          <>
            <RegionTerrain exaggeration={exaggeration} layerOpacity={layerOpacity} />
            <RoutePath exaggeration={exaggeration} />
            <TraverseOverlay exaggeration={exaggeration} />
            {showLabels && <LabelAnchors labels={labels} />}
          </>
        )}

        <CameraRig />
        <EffectComposer>
          <Bloom intensity={bloom} luminanceThreshold={0.8} mipmapBlur />
          <Vignette darkness={0.6} />
        </EffectComposer>
      </Canvas>
      {showLabels && <LabelOverlay labels={labels} />}
    </>
  );
}
