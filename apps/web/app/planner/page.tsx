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

// three.js needs the browser: the scene is not rendered on the server.
const Scene = dynamic(() => import("@/components/scene/Scene"), { ssr: false });

// On narrow screens the panels do not fit in the corners: they go in a bottom sheet with tabs.
const NARROW = "(max-width: 720px)";

export default function Planner() {
  const loadRegions = useMapStore((s) => s.loadRegions);
  const openRegion = useMapStore((s) => s.openRegion);
  const view = useMapStore((s) => s.view);
  const regionId = useMapStore((s) => s.regionId);
  const narrow = useMediaQuery(NARROW);

  // It starts in the route view of the first region; with ?globe it starts on the globe.
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
        {/* While a region is opening, picking another one is not offered. */}
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
