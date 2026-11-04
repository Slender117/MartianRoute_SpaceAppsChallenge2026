"use client";

import { useControls } from "leva";

/** Ajustes en vivo de la escena (Leva). El panel se oculta en producción. */
export function useDebugControls() {
  return useControls("Escena", {
    sunIntensity: { value: 2.2, min: 0, max: 6, step: 0.1, label: "Sol" },
    exaggeration: { value: 2, min: 1, max: 6, step: 0.5, label: "Exageración vertical" },
    bloom: { value: 0.6, min: 0, max: 2, step: 0.05, label: "Bloom" },
  });
}
