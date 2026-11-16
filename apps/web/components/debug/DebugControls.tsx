"use client";

import { Leva, useControls } from "leva";
import { useEffect } from "react";

import { SCENE_DEFAULTS, useSceneSettings } from "./sceneSettings";

/**
 * Live scene settings (Leva). Only loaded in development (see Scene.tsx): in production
 * Leva is not even downloaded and the scene uses SCENE_DEFAULTS.
 */
export default function DebugControls() {
  const { sunIntensity, exaggeration, layerOpacity, bloom } = useControls("Escena", {
    sunIntensity: { value: SCENE_DEFAULTS.sunIntensity, min: 0, max: 6, step: 0.1, label: "Sol" },
    exaggeration: { value: SCENE_DEFAULTS.exaggeration, min: 1, max: 6, step: 0.5, label: "Vertical exaggeration" },
    layerOpacity: { value: SCENE_DEFAULTS.layerOpacity, min: 0.2, max: 1, step: 0.05, label: "Opacidad de capas" },
    bloom: { value: SCENE_DEFAULTS.bloom, min: 0, max: 2, step: 0.05, label: "Bloom" },
  });

  useEffect(() => {
    useSceneSettings.setState({ sunIntensity, exaggeration, layerOpacity, bloom });
  }, [sunIntensity, exaggeration, layerOpacity, bloom]);

  return <Leva collapsed />;
}
