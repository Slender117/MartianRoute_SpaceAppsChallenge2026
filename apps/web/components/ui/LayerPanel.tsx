"use client";

import { useRegionExtras } from "@/components/scene/regionAssets";
import { SafeReturnToggle } from "@/components/ui/SafeReturnLegend";
import { dataName, useLang, useT } from "@/lib/i18n";
import { useMapStore } from "@/lib/store";

export function LayerPanel() {
  const manifest = useMapStore((s) => s.manifest);
  const activeLayers = useMapStore((s) => s.activeLayers);
  const toggleLayer = useMapStore((s) => s.toggleLayer);
  const showTraverse = useMapStore((s) => s.showTraverse);
  const toggleTraverse = useMapStore((s) => s.toggleTraverse);
  const backToGlobe = useMapStore((s) => s.backToGlobe);
  const legends = useRegionExtras(manifest?.id)?.legends;
  const t = useT();
  const lang = useLang((s) => s.lang);

  if (!manifest) return null;

  return (
    <section className="panel" style={{ top: 16, left: 16 }}>
      <h2>{dataName(manifest.name, lang)}</h2>
      {["slope", ...manifest.layers].map((layer) => (
        <div key={layer}>
          <label style={{ display: "block", margin: "4px 0" }}>
            <input type="checkbox" checked={activeLayers.includes(layer)} onChange={() => toggleLayer(layer)} />{" "}
            {t.layers[layer] ?? layer}
          </label>
          {activeLayers.includes(layer) && legends?.[layer] && (
            <ul className="class-legend">
              {legends[layer].map((item) => (
                <li key={item.code}>
                  <span className="class-swatch" style={{ background: item.color }} />
                  {dataName(item.name, lang)}
                  <span className="muted"> · {Math.round(item.share * 100)} %</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
      {manifest.traverses.length > 0 && (
        <label style={{ display: "block", margin: "8px 0 4px" }}>
          <input type="checkbox" checked={showTraverse} onChange={toggleTraverse} />{" "}
          {t.realTraverse(manifest.traverses[0])}
        </label>
      )}
      <SafeReturnToggle />
      <button className="ghost" onClick={backToGlobe} style={{ marginTop: 8 }}>
        {t.backToGlobe}
      </button>
    </section>
  );
}
