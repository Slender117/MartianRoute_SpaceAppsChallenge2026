"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";

import { AssumptionsPanel } from "@/components/ui/AssumptionsPanel";
import { LayerPanel } from "@/components/ui/LayerPanel";
import { MobileSheet } from "@/components/ui/MobileSheet";
import { NavPanel } from "@/components/ui/NavPanel";
import { PlannerBar } from "@/components/ui/PlannerBar";
import { RoutePanel } from "@/components/ui/RoutePanel";
import { SceneLoader } from "@/components/ui/SceneLoader";
import { SitePanel } from "@/components/ui/SitePanel";
import { useMapStore } from "@/lib/store";
import { useMediaQuery } from "@/lib/useMediaQuery";

// three.js necesita el navegador: la escena no se renderiza en el servidor.
const Scene = dynamic(() => import("@/components/scene/Scene"), { ssr: false });

// En pantallas angostas los paneles no caben en las esquinas: van en una hoja inferior con pestañas.
const NARROW = "(max-width: 720px)";

export default function Planner() {
  const loadRegions = useMapStore((s) => s.loadRegions);
  const openRegion = useMapStore((s) => s.openRegion);
  const view = useMapStore((s) => s.view);
  const regionId = useMapStore((s) => s.regionId);
  const narrow = useMediaQuery(NARROW);

  // Arranca en la vista de ruta de la primera región; con ?globe arranca en el globo.
  useEffect(() => {
    loadRegions().then(() => {
      const first = useMapStore.getState().regions[0];
      if (first && !new URLSearchParams(window.location.search).has("globe")) openRegion(first.id);
    });
  }, [loadRegions, openRegion]);

  return (
    <main className="planner">
      <Scene />
      <SceneLoader />
      <div className={narrow ? "hud hud-narrow" : "hud"}>
        <PlannerBar />
        {/* Mientras se abre una región no se ofrece elegir otra. */}
        {view === "globe" && !regionId && (
          <div className="hud-col hud-left">
            <SitePanel />
          </div>
        )}
        {view === "region" &&
          (narrow ? (
            <MobileSheet />
          ) : (
            <>
              <div className="hud-col hud-left">
                <LayerPanel />
                <NavPanel />
              </div>
              <div className="hud-col hud-right">
                <RoutePanel />
                <AssumptionsPanel />
              </div>
            </>
          ))}
      </div>
    </main>
  );
}
