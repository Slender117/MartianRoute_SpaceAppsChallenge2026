"use client";

import { useProgress } from "@react-three/drei";

import { dataName, useLang, useT } from "@/lib/i18n";
import { useMapStore } from "@/lib/store";

/**
 * Aviso de carga sobre la escena: grande mientras llega la región o su relieve, y una etiqueta
 * pequeña mientras se descargan la ortofoto o una capa (el terreno ya se puede usar).
 */
export function SceneLoader() {
  const view = useMapStore((s) => s.view);
  const regionId = useMapStore((s) => s.regionId);
  const manifest = useMapStore((s) => s.manifest);
  const terrainReady = useMapStore((s) => s.terrainReady);
  const { active, progress } = useProgress();
  const lang = useLang((s) => s.lang);
  const t = useT();

  const opening = view === "globe" && regionId !== null;
  if (opening || (view === "region" && !terrainReady)) {
    return (
      <div className="scene-loader" role="status">
        <span className="spinner" aria-hidden />
        {manifest && !opening ? t.loadingTerrain(dataName(manifest.name, lang)) : t.loadingRegion}
      </div>
    );
  }
  if (view === "region" && active) {
    return (
      <div className="scene-chip" role="status">
        {t.loadingImages(Math.round(progress))}
      </div>
    );
  }
  return null;
}
