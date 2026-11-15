import { create } from "zustand";

/** Ajustes de la escena. En desarrollo se cambian en vivo con Leva (DebugControls). */
export const SCENE_DEFAULTS = {
  sunIntensity: 2.2,
  exaggeration: 2,
  layerOpacity: 0.75,
  bloom: 0.6,
};

export type SceneSettings = typeof SCENE_DEFAULTS;

export const useSceneSettings = create<SceneSettings>(() => SCENE_DEFAULTS);
