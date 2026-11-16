"use client";

import { useProgress } from "@react-three/drei";

import { dataName, useLang, useT } from "@/lib/i18n";
import { useMapStore } from "@/lib/store";

/**
 * Loading notice over the scene: large while the region or its relief arrives, and a small
 * label while the orthophoto or a layer downloads (the terrain can already be used).
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
