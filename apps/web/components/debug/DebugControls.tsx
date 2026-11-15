"use client";

import { Leva, useControls } from "leva";
import { useEffect } from "react";

import { SCENE_DEFAULTS, useSceneSettings } from "./sceneSettings";

/**
 * Ajustes en vivo de la escena (Leva). Solo se carga en desarrollo (ver Scene.tsx): en producción
 * Leva ni se descarga y la escena usa SCENE_DEFAULTS.
 */
export default function DebugControls() {
  const { sunIntensity, exaggeration, layerOpacity, bloom } = useControls("Escena", {
    sunIntensity: { value: SCENE_DEFAULTS.sunIntensity, min: 0, max: 6, step: 0.1, label: "Sol" },
    exaggeration: { value: SCENE_DEFAULTS.exaggeration, min: 1, max: 6, step: 0.5, label: "Exageración vertical" },
    layerOpacity: { value: SCENE_DEFAULTS.layerOpacity, min: 0.2, max: 1, step: 0.05, label: "Opacidad de capas" },
    bloom: { value: SCENE_DEFAULTS.bloom, min: 0, max: 2, step: 0.05, label: "Bloom" },
  });

  useEffect(() => {
    useSceneSettings.setState({ sunIntensity, exaggeration, layerOpacity, bloom });
  }, [sunIntensity, exaggeration, layerOpacity, bloom]);

  return <Leva collapsed />;
}
