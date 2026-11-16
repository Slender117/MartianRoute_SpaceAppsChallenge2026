"use client";

import { useState } from "react";

import { AssumptionsPanel } from "@/components/ui/AssumptionsPanel";
import { LayerPanel } from "@/components/ui/LayerPanel";
import { NavPanel } from "@/components/ui/NavPanel";
import { RoutePanel } from "@/components/ui/RoutePanel";
import { useT } from "@/lib/i18n";

type Tab = "route" | "layers" | "info";
const TABS: Tab[] = ["route", "layers", "info"];

/**
 * Panels on phones: a bottom sheet with tabs (Route, Layers, Assumptions) that can be hidden
 * to see the whole terrain. On wide screens the same panels go in the corners.
 */
export function MobileSheet() {
  const [tab, setTab] = useState<Tab>("route");
  const [open, setOpen] = useState(true);
  const t = useT();

  return (
    <section className="sheet" aria-label={t.panelsLabel}>
      <div className="sheet-bar">
        <div role="tablist" className="sheet-tabs">
          {TABS.map((id) => (
            <button
              key={id}
              role="tab"
              id={`sheet-tab-${id}`}
              aria-selected={tab === id}
              aria-controls="sheet-body"
              className={tab === id ? undefined : "ghost"}
              onClick={() => {
                setTab(id);
                setOpen(true);
              }}
            >
              {t.tabs[id]}
            </button>
          ))}
        </div>
        <button
          className="ghost sheet-toggle"
          aria-expanded={open}
          aria-controls="sheet-body"
          title={open ? t.sheetCollapse : t.sheetExpand}
          aria-label={open ? t.sheetCollapse : t.sheetExpand}
          onClick={() => setOpen(!open)}
        >
          <span aria-hidden>{open ? "▾" : "▴"}</span>
        </button>
      </div>
      {open && (
        <div id="sheet-body" role="tabpanel" aria-labelledby={`sheet-tab-${tab}`} className="sheet-body">
          {tab === "route" && (
            <>
              <RoutePanel />
              <NavPanel />
            </>
          )}
          {tab === "layers" && <LayerPanel />}
          {tab === "info" && <AssumptionsPanel defaultOpen />}
        </div>
      )}
    </section>
  );
}
