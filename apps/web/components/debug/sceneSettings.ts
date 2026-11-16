import { create } from "zustand";

/** Scene settings. In development they change live with Leva (DebugControls). */
export const SCENE_DEFAULTS = {
  sunIntensity: 2.2,
  exaggeration: 2,
  layerOpacity: 0.75,
  bloom: 0.6,
};

export type SceneSettings = typeof SCENE_DEFAULTS;

export const useSceneSettings = create<SceneSettings>(() => SCENE_DEFAULTS);
