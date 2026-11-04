"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";

import { LayerPanel } from "@/components/ui/LayerPanel";
import { NavPanel } from "@/components/ui/NavPanel";
import { RoutePanel } from "@/components/ui/RoutePanel";
import { SitePanel } from "@/components/ui/SitePanel";
import { useMapStore } from "@/lib/store";

// three.js necesita el navegador: la escena no se renderiza en el servidor.
const Scene = dynamic(() => import("@/components/scene/Scene"), { ssr: false });

export default function Home() {
  const loadRegions = useMapStore((s) => s.loadRegions);
  const openRegion = useMapStore((s) => s.openRegion);
  const view = useMapStore((s) => s.view);

  // Arranca en la vista de ruta de la primera región; con ?globe arranca en el globo.
  useEffect(() => {
    loadRegions().then(() => {
      const first = useMapStore.getState().regions[0];
      if (first && !new URLSearchParams(window.location.search).has("globe")) openRegion(first.id);
    });
  }, [loadRegions, openRegion]);

  return (
    <main>
      <Scene />
      {view === "globe" && <SitePanel />}
      {view === "region" && (
        <>
          <LayerPanel />
          <RoutePanel />
          <NavPanel />
        </>
      )}
    </main>
  );
}
